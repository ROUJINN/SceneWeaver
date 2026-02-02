import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.config import LLMSettings, config
from app.logger import logger  # Assuming a logger is set up in your app


def log_llm_io(
    save_dir: str,
    messages: List[dict],
    response: str,
    system_msgs: Optional[List[dict]] = None,
    tool_calls: Optional[List] = None,
    method_name: str = "ask",
):
    """
    Log LLM input and output to a file.

    Args:
        save_dir: Directory to save the log file
        messages: Input messages sent to LLM
        response: Response from LLM
        system_msgs: Optional system messages
        tool_calls: Optional tool calls in response
        method_name: Name of the method used (ask, ask_tool, ask_with_images)
    """
    try:
        log_dir = os.path.join(save_dir, "llm_io_logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = os.path.join(log_dir, f"llm_{timestamp}.json")

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "method": method_name,
            "input": {
                "messages": messages,
                "system_messages": system_msgs if system_msgs else [],
            },
            "output": {
                "content": response,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (tool_calls or [])
                ],
            },
        }

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"LLM I/O logged to: {log_file}")
    except Exception as e:
        logger.warning(f"Failed to log LLM I/O: {e}")


from app.schema import (
    ROLE_VALUES,
    TOOL_CHOICE_TYPE,
    TOOL_CHOICE_VALUES,
    Function,
    Message,
    ToolCall,
    ToolChoice,
)

MULTIMODAL_MODELS = ["gemini-3-flash-preview", "gemini-3-flash-exp", "gemini-2.5-pro"]


class GeminiResponse:
    """
    Wrapper class to provide OpenAI-like response interface for Gemini REST API responses.

    This class is used to maintain compatibility with existing code that expects
    responses to have .content and .tool_calls attributes.
    """

    def __init__(self, text: str = "", tool_calls: Optional[List[ToolCall]] = None):
        self.content = text or ""
        self.tool_calls = tool_calls
        self._usage = MagicMock()

    @property
    def usage(self):
        """Mock usage object for backward compatibility"""
        return self._usage


class MagicMock:
    """Simple mock class for backward compatibility"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def convert_openai_tools_to_rest(openai_tools: List[dict]) -> List[dict]:
    """
    Convert OpenAI tool definitions to Gemini REST API format.

    Args:
        openai_tools: List of OpenAI-style tool definitions

    Returns:
        List of tool declarations in Gemini REST API format
    """
    function_declarations = []
    for tool in openai_tools:
        if tool.get("type") == "function":
            func = tool["function"]
            declaration = {
                "name": func["name"],
                "description": func["description"],
                "parameters": func.get("parameters", {"type": "object"}),
            }
            function_declarations.append(declaration)
    return [{"functionDeclarations": function_declarations}]


def parse_gemini_response(
    response_json: dict, content_text: str = ""
) -> GeminiResponse:
    """
    Parse Gemini REST API response to OpenAI-like format.

    Args:
        response_json: Raw JSON response from Gemini REST API
        content_text: Text content from response (if already extracted)

    Returns:
        GeminiResponse object with content and tool_calls
    """
    tool_calls = None

    # Extract candidates
    candidates = response_json.get("candidates", [])
    if candidates:
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        calls = []
        for part in parts:
            # Check for function call (camelCase in REST API)
            if "functionCall" in part:
                fc = part["functionCall"]
                args_dict = fc.get("args", {})

                function = Function(
                    name=fc.get("name", ""),
                    arguments=json.dumps(args_dict) if args_dict else "{}",
                )
                tool_call = ToolCall(
                    id=f"call_{len(calls)}", type="function", function=function
                )
                calls.append(tool_call)
            # Check for text content
            elif "text" in part:
                content_text += part["text"]

        if calls:
            tool_calls = calls

    return GeminiResponse(text=content_text, tool_calls=tool_calls)


def convert_messages_to_rest(
    messages: List[dict], supports_images: bool = False
) -> tuple:
    """
    Convert internal messages to Gemini REST API format.

    Args:
        messages: List of message dictionaries
        supports_images: Whether the model supports images

    Returns:
        Tuple of (contents, system_text) where contents is formatted for REST API
    """
    contents = []
    system_text = None

    for msg in messages:
        role = msg.get("role", "")

        # Handle system messages - extract separately
        if role == "system":
            system_text = msg.get("content", "")
            continue

        # Gemini REST API uses "user" and "model" roles
        content = {"role": "user", "parts": []}

        # Handle user messages with images
        if role == "user":
            # Handle base64 images (inline data format for REST API)
            if supports_images and msg.get("base64_image"):
                content["parts"].append(
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": msg["base64_image"],
                        }
                    }
                )

            # Handle text content
            if msg.get("content"):
                if isinstance(msg["content"], list):
                    for item in msg["content"]:
                        if isinstance(item, str):
                            content["parts"].append({"text": item})
                        elif isinstance(item, dict) and item.get("type") == "text":
                            content["parts"].append({"text": item.get("text", "")})
                else:
                    content["parts"].append({"text": msg["content"]})

        # Handle assistant messages
        elif role == "assistant":
            content["role"] = "model"

            if msg.get("content"):
                content["parts"].append({"text": msg["content"]})

            # Handle tool calls
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    if isinstance(func, dict):
                        func_name = func.get("name", "")
                        func_args = func.get("arguments", "{}")
                        try:
                            args_dict = json.loads(func_args)
                        except json.JSONDecodeError:
                            args_dict = {}
                    elif isinstance(func, Function):
                        func_name = func.name
                        try:
                            args_dict = json.loads(func.arguments)
                        except json.JSONDecodeError:
                            args_dict = {}
                    else:
                        continue

                    content["parts"].append(
                        {"functionCall": {"name": func_name, "args": args_dict}}
                    )

        # Handle tool response messages
        elif role == "tool":
            if msg.get("content"):
                # Tool response goes as user message with functionResponse
                content["parts"].append(
                    {
                        "functionResponse": {
                            "name": msg.get("name", "function"),
                            "response": {"result": msg["content"]},
                        }
                    }
                )

        # Only add content if it has parts
        if content["parts"]:
            contents.append(content)

    return contents, system_text


class LLM:
    _instances: Dict[str, "LLM"] = {}

    def __new__(
        cls, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name, llm_config)
            cls._instances[config_name] = instance
        return cls._instances[config_name]

    def __init__(
        self, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if not hasattr(
            self, "client_initialized"
        ):  # Only initialize if not already initialized
            llm_config = llm_config or config.llm
            llm_config = llm_config.get(config_name, llm_config["default"])
            self.model = llm_config.model
            self.max_tokens = llm_config.max_tokens
            self.temperature = llm_config.temperature
            self.api_key = llm_config.api_key
            self.base_url = llm_config.base_url.rstrip("/")

            self.client_initialized = True

            logger.info(
                f"Initialized LLM with model: {self.model}, base_url: {self.base_url}"
            )

    @staticmethod
    def format_messages(
        messages: List[Union[dict, Message]], supports_images: bool = False
    ) -> List[dict]:
        """
        Format messages for LLM by converting them to dictionary format.

        Args:
            messages: List of messages that can be either dict or Message objects
            supports_images: Flag indicating if the target model supports image inputs

        Returns:
            List[dict]: List of formatted message dictionaries

        Raises:
            ValueError: If messages are invalid or missing required fields
            TypeError: If unsupported message types are provided
        """
        formatted_messages = []

        for message in messages:
            # Convert Message objects to dictionaries
            if isinstance(message, Message):
                message = message.to_dict()

            if isinstance(message, dict):
                # If message is a dict, ensure it has required fields
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")

                # For Gemini REST API, we keep base64_image as-is for conversion
                if "content" in message or "tool_calls" in message:
                    formatted_messages.append(message)
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # Validate all messages have required fields
        for msg in formatted_messages:
            if msg["role"] not in ROLE_VALUES:
                raise ValueError(f"Invalid role: {msg['role']}")

        return formatted_messages

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
    )
    def ask(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to the LLM and get the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response (not implemented for REST API yet)
            temperature (float): Sampling temperature for the response

        Returns:
            str: The generated response

        Raises:
            ValueError: If messages are invalid or response is empty
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            supports_images = self.model in MULTIMODAL_MODELS

            # Format messages
            if system_msgs:
                system_msgs = self.format_messages(system_msgs, supports_images)
                messages = system_msgs + self.format_messages(messages, supports_images)
            else:
                messages = self.format_messages(messages, supports_images)

            # Convert to REST API format
            contents, system_text = convert_messages_to_rest(messages, supports_images)

            # Build request body
            body = {"contents": contents}

            # Add system instruction if provided
            if system_text:
                body["systemInstruction"] = {"parts": [{"text": system_text}]}

            # Add generation config
            body["generationConfig"] = {
                "maxOutputTokens": self.max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.temperature,
            }

            # Make POST request to REST API
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            # Use extended timeout (600s) for LLM calls to avoid timeout issues
            response = requests.post(url, headers=headers, json=body, timeout=600)

            # Check for errors
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                error_msg = (
                    f"REST API error: {e.response.status_code} - {e.response.text}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e

            response_json = response.json()

            # Parse response
            result = parse_gemini_response(response_json)

            if not result.content:
                raise ValueError("Empty response from LLM")

            # Log LLM I/O
            save_dir = os.getenv("save_dir", ".")
            log_llm_io(save_dir, messages, result.content, system_msgs, None, "ask")

            # Print streaming-like output for compatibility
            if stream:
                print(result.content, end="", flush=True)
                print()

            return result.content

        except Exception:
            logger.exception("Unexpected error in ask")
            raise

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
    )
    def ask_tool(
        self,
        messages: List[Union[dict, Message]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        timeout: int = 300,
        tools: Optional[List[dict]] = None,
        tool_choice: TOOL_CHOICE_TYPE = ToolChoice.AUTO,  # type: ignore
        temperature: Optional[float] = None,
        **kwargs,
    ):
        """
        Ask LLM using functions/tools and return the response.

        Args:
            messages: List of conversation messages
            system_msgs: Optional system messages to prepend
            timeout: Request timeout in seconds
            tools: List of tools to use
            tool_choice: Tool choice strategy (not fully supported in REST API)
            temperature: Sampling temperature for the response
            **kwargs: Additional completion arguments

        Returns:
            GeminiResponse: The model's response with .content and .tool_calls attributes

        Raises:
            ValueError: If tools, tool_choice, or messages are invalid
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            supports_images = self.model in MULTIMODAL_MODELS

            # Format messages
            if system_msgs:
                system_msgs = self.format_messages(system_msgs, supports_images)
                messages = system_msgs + self.format_messages(messages, supports_images)
            else:
                messages = self.format_messages(messages, supports_images)

            # Convert to REST API format
            contents, system_text = convert_messages_to_rest(messages, supports_images)

            # Build request body
            body = {"contents": contents}

            # Add system instruction if provided
            if system_text:
                body["systemInstruction"] = {"parts": [{"text": system_text}]}

            # Add tools if provided (function calling)
            if tools:
                body["tools"] = convert_openai_tools_to_rest(tools)

            body["generationConfig"] = {
                "maxOutputTokens": self.max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.temperature,
            }

            # Make POST request to REST API
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=body, timeout=timeout)

            # Check for errors
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                error_msg = (
                    f"REST API error: {e.response.status_code} - {e.response.text}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e

            response_json = response.json()

            # Parse response
            result = parse_gemini_response(response_json)

            if not result.content and not result.tool_calls:
                raise ValueError("Empty response from LLM")

            # Log LLM I/O
            save_dir = os.getenv("save_dir", ".")
            log_llm_io(
                save_dir,
                messages,
                result.content or "",
                system_msgs,
                result.tool_calls,
                "ask_tool",
            )

            return result

        except Exception:
            logger.exception("Unexpected error in ask_tool")
            raise

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
    )
    def ask_with_images(
        self,
        messages: List[Union[dict, Message]],
        images: List[Union[str, dict]],
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt with images to the LLM and get the response.

        Args:
            messages: List of conversation messages
            images: List of image URLs or image data dictionaries
            system_msgs: Optional system messages to prepend
            stream (bool): Whether to stream the response
            temperature (float): Sampling temperature for the response

        Returns:
            str: The generated response

        Raises:
            ValueError: If messages are invalid or response is empty
            Exception: For unexpected errors
        """
        try:
            # Check if the model supports images
            if self.model not in MULTIMODAL_MODELS:
                raise ValueError(
                    f"Model {self.model} does not support images. Use a model from {MULTIMODAL_MODELS}"
                )

            # Format messages
            formatted_messages = self.format_messages(messages, supports_images=True)

            # Ensure the last message is from the user to attach images
            if not formatted_messages or formatted_messages[-1]["role"] != "user":
                raise ValueError(
                    "The last message must be from the user to attach images"
                )

            # Add images to the last user message
            for image in images:
                if isinstance(image, str):
                    # Assume image path - read and encode as base64
                    import base64

                    with open(image, "rb") as f:
                        formatted_messages[-1]["base64_image"] = base64.b64encode(
                            f.read()
                        ).decode("utf-8")
                elif isinstance(image, dict):
                    if "url" in image:
                        # Handle image URL (download and encode)
                        # For simplicity, we'll skip this for now
                        pass
                    elif "base64" in image:
                        formatted_messages[-1]["base64_image"] = image["base64"]

            # Combine with system messages
            if system_msgs:
                all_messages = (
                    self.format_messages(system_msgs, supports_images=True)
                    + formatted_messages
                )
            else:
                all_messages = formatted_messages

            # Convert to REST API format
            contents, system_text = convert_messages_to_rest(
                all_messages, supports_images=True
            )

            # Build request body
            body = {"contents": contents}
            if system_text:
                body["systemInstruction"] = {"parts": [{"text": system_text}]}

            body["generationConfig"] = {
                "maxOutputTokens": self.max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.temperature,
            }

            # Make POST request
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            # Use extended timeout (600s) for LLM calls to avoid timeout issues
            response = requests.post(url, headers=headers, json=body, timeout=600)

            # Check for errors
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                error_msg = (
                    f"REST API error: {e.response.status_code} - {e.response.text}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e

            response_json = response.json()

            # Parse response
            result = parse_gemini_response(response_json)

            if not result.content:
                raise ValueError("Empty response from LLM")

            # Log LLM I/O
            save_dir = os.getenv("save_dir", ".")
            log_llm_io(
                save_dir,
                all_messages,
                result.content,
                system_msgs,
                None,
                "ask_with_images",
            )

            if stream:
                print(result.content, end="", flush=True)
                print()

            return result.content

        except ValueError as ve:
            logger.exception(f"Validation error in ask_with_images: {ve}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in ask_with_images: {e}")
            raise

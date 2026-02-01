#!/usr/bin/env python3
"""
Test script to verify Gemini REST API implementation.
"""
import os
import sys

# Add the Pipeline directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Pipeline'))

from app.llm import LLM, parse_gemini_response, convert_openai_tools_to_rest, convert_messages_to_rest


def test_basic_message_conversion():
    """Test converting messages to REST API format."""
    print("Testing message conversion...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ]
    contents, system_text = convert_messages_to_rest(messages, supports_images=False)
    assert system_text == "You are a helpful assistant."
    assert len(contents) == 1
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "Hello, how are you?"
    print("  Message conversion: PASSED")


def test_tool_conversion():
    """Test converting tools to REST API format."""
    print("Testing tool conversion...")
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": "test_function",
                "description": "A test function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "string"}
                    }
                }
            }
        }
    ]
    rest_tools = convert_openai_tools_to_rest(openai_tools)
    assert len(rest_tools) == 1
    assert "functionDeclarations" in rest_tools[0]
    assert rest_tools[0]["functionDeclarations"][0]["name"] == "test_function"
    print("  Tool conversion: PASSED")


def test_response_parsing():
    """Test parsing REST API response."""
    print("Testing response parsing...")
    response_json = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Hello! How can I help you today?"}
                    ]
                }
            }
        ]
    }
    response = parse_gemini_response(response_json)
    assert response.content == "Hello! How can I help you today?"
    assert response.tool_calls is None
    print("  Response parsing: PASSED")


def test_function_call_parsing():
    """Test parsing function call response."""
    print("Testing function call parsing...")
    response_json = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "test_function",
                                "args": {"arg1": "value1"}
                            }
                        }
                    ]
                }
            }
        ]
    }
    response = parse_gemini_response(response_json)
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].function.name == "test_function"
    print("  Function call parsing: PASSED")


def test_llm_initialization():
    """Test LLM class initialization."""
    print("Testing LLM initialization...")
    # Check if GOOGLE_API_KEY is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  WARNING: GOOGLE_API_KEY not set, skipping API call test")
        print("  To test API calls, set: export GOOGLE_API_KEY=your_key")
        print("  LLM initialization: SKIPPED (no API key)")
        return

    try:
        llm = LLM()
        assert llm.model == "gemini-3-flash-preview"
        assert "zhizengzeng.com" in llm.base_url
        print(f"  LLM initialized with model: {llm.model}")
        print("  LLM initialization: PASSED")
    except Exception as e:
        print(f"  LLM initialization: FAILED - {e}")
        raise


def main():
    """Run all tests."""
    print("=" * 60)
    print("Gemini REST API Implementation Tests")
    print("=" * 60)
    print()

    try:
        test_basic_message_conversion()
        test_tool_conversion()
        test_response_parsing()
        test_function_call_parsing()
        test_llm_initialization()

        print()
        print("=" * 60)
        print("All tests PASSED!")
        print("=" * 60)
        return 0
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Test FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

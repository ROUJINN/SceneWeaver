from TongGPT import GPT4V, GPT4o, TongGPT


class GPT4(GPT4o):
    """
    Simple interface for interacting with GPT-4O model
    """

    VERSIONS = {
        "4v": "gpt-4-vision-preview",
        "4o": "gpt-4o",
        "4o-mini": "gpt-4o-mini",
        "gpt-4-turbo-2024-04-09": "gpt-4-turbo-2024-04-09",
    }

    def __init__(
        self,
        api_key=None,
        version="4o",
    ):
        # def __init__(self, '
        MODEL = "gpt-4-turbo-2024-04-09"
        REGION = "eastus2"
        super().__init__(MODEL, REGION)
        self.version = MODEL

    def __call__(self, payload, verbose=False):
        """
        Queries GPT using the desired @prompt

        Args:
            payload (dict): Prompt payload to pass to GPT. This should be formatted properly, see
                https://platform.openai.com/docs/overview for details
            verbose (bool): Whether to be verbose as GPT is being queried

        Returns:
            None or str: Raw outputted GPT response if valid, else None
        """
        if verbose:
            print(f"Querying GPT-{self.version} API...")
        # import pdb
        # pdb.set_trace()
        response = self.send_request(payload)
        try:
            content = response.choices[0].message.content
        except:
            print(
                f"Got error while querying GPT-{self.version} API! Response:\n\n{response}"
            )
            return None

        if verbose:
            print(f"Finished querying GPT-{self.version}.")

        return content

    def get_payload(self, prompting_text_system, prompting_text_user):
        text_dict_system = {"type": "text", "text": prompting_text_system}
        content_system = [text_dict_system]

        content_user = [{"type": "text", "text": prompting_text_user}]

        object_caption_payload = {
            "model": "gpt-4-turbo-2024-04-09",
            "messages": [
                {"role": "system", "content": content_system},
                {"role": "user", "content": content_user},
            ],
            "temperature": 0,
            "max_tokens": 500,
        }
        return object_caption_payload

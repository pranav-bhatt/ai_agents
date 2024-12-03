import os


class LLMConfig:
    """constructing the llm configuration for running multi-agent system"""

    def __init__(self, config_dict: dict) -> None:
        self.config_dict = config_dict
        self.context_len = None
        self.llm_name = "llama3-70b-8192"
        self.temperature = 0.3
        self.stop = ["\n"]
        self.max_tokens = 4096
        self.end_of_prompt = ""
        self.api_key: str = ""
        self.base_url = "https://api.groq.com/openai/v1"
        self.__dict__.update(config_dict)

from openai import AzureOpenAI
from dotenv import load_dotenv
import os

class OpenAIClient:
    _client = None

    @classmethod
    def initialize(cls):
        """Initialize the OpenAI client."""
        load_dotenv(override=True)
        cls._client = AzureOpenAI(
            api_version=os.getenv("GPT_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("ENDPOINT"),
        )

    @classmethod
    def get_client(cls):
        """Get the initialized OpenAI client."""
        if cls._client is None:
            cls.initialize()
        return cls._client
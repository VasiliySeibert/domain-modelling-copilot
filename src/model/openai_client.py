from openai import OpenAI
from dotenv import load_dotenv
import os

class OpenAIClient:
    _client = None

    @classmethod
    def initialize(cls):
        """Initialize the OpenAI client."""
        load_dotenv(override=True)
        cls._client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    @classmethod
    def get_client(cls):
        """Get the initialized OpenAI client."""
        if cls._client is None:
            cls.initialize()
        return cls._client
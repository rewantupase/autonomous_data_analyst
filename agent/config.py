import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./db/sample.db")
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", 10))
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"
    CHARTS_DIR: str = os.getenv("CHARTS_DIR", "./output/charts")

    @classmethod
    def get_llm(cls, streaming: bool = False):
        """Return a LangChain chat model based on LLM_PROVIDER."""
        if cls.LLM_PROVIDER == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=cls.ANTHROPIC_MODEL,
                anthropic_api_key=cls.ANTHROPIC_API_KEY,
                streaming=streaming,
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=cls.OPENAI_MODEL,
                openai_api_key=cls.OPENAI_API_KEY,
                streaming=streaming,
            )

    @classmethod
    def validate(cls):
        """Raise if required keys are missing."""
        if cls.LLM_PROVIDER == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
        else:
            if not cls.OPENAI_API_KEY:
                raise EnvironmentError("OPENAI_API_KEY is not set.")

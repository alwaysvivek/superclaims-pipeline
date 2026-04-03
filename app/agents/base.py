from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logger import setup_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = setup_logger(__name__)

class BaseAgent:
    def __init__(self, api_key: str, model_name: str = settings.MODEL_NAME, temperature: float = 0.0):
        self.llm = ChatGroq(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def invoke_with_retry(self, message):
        logger.info(f"Invoking LLM for model: {self.llm.model_name}")
        return self.llm.invoke([message])

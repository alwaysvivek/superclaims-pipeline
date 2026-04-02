import logging
from typing import Type
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from groq import AuthenticationError

from graph.state import PipelineState
from graph.utils.pdf_utils import extract_specific_pages
from graph.utils.logger import get_json_logger

logger = logging.getLogger(__name__)

class BaseExtractionAgent:
    """Base OOP class for extraction agents to enforce DRY."""
    
    def __init__(
        self, 
        agent_name: str, 
        result_key: str, 
        prompt: str, 
        schema: Type[BaseModel], 
        relevant_types: list[str], 
        max_tokens: int = 1000
    ):
        self.agent_name = agent_name
        self.result_key = result_key
        self.prompt = prompt
        self.schema = schema
        self.relevant_types = relevant_types
        self.max_tokens = max_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_not_exception_type(AuthenticationError),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry {retry_state.attempt_number} for extraction..."
        ),
    )
    async def _extract_info(self, llm_structured: any, images: list[str]) -> BaseModel:
        content = [{"type": "text", "text": self.prompt}]
        for img_b64 in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            })
        message = HumanMessage(content=content)
        return await llm_structured.ainvoke([message])

    async def _post_process(self, extracted: BaseModel) -> dict:
        """Hook for subclasses to override and manipulate data before returning."""
        return extracted.dict()

    async def __call__(self, state: PipelineState) -> dict:
        """Callable so this class can act natively as a LangGraph Node."""
        request_id = state["request_id"]
        api_key = state["api_key"]
        pdf_filepath = state["pdf_filepath"]
        classifications = state["page_classifications"]["mapping"]
        node_logger = get_json_logger(self.agent_name, request_id)

        # 1. Fetch relevant indices
        page_indices = []
        for doc_type in self.relevant_types:
            page_indices.extend(classifications.get(doc_type, []))

        if not page_indices:
            node_logger.info(f"{self.agent_name}: No relevant pages found")
            return {self.result_key: {"status": "no_pages_found", "data": {}}}

        # 2. Extract images
        unique_indices = sorted(set(page_indices))[:5]  # Groq limit
        relevant_images = extract_specific_pages(pdf_filepath, unique_indices)
        
        if not relevant_images:
            node_logger.info(f"{self.agent_name}: No valid images extracted from disk")
            return {self.result_key: {"status": "no_pages_found", "data": {}}}

        # 3. Initialize LLM
        llm = ChatGroq(
            model="llama-3.2-11b-vision-preview",
            api_key=api_key,
            temperature=0.1,
            max_tokens=self.max_tokens,
        )
        llm_structured = llm.with_structured_output(self.schema)

        # 4. Process and Handle Erors
        try:
            extracted = await self._extract_info(llm_structured, relevant_images)
            data = await self._post_process(extracted)
            
            node_logger.info(f"{self.agent_name}: Successfully extracted info")
            return {
                self.result_key: {
                    "status": "success",
                    "pages_processed": unique_indices,
                    "data": data,
                }
            }
        except AuthenticationError:
            raise
        except Exception as e:
            node_logger.error(f"{self.agent_name}: Extraction failed — {e}")
            return {
                self.result_key: {
                    "status": "error",
                    "error": str(e),
                    "pages_processed": unique_indices,
                    "data": {},
                }
            }

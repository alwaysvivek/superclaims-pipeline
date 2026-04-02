"""Segregator Agent — classifies each PDF page into document types using Groq vision."""

import asyncio
import json
import logging

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from groq import AuthenticationError

from graph.state import PipelineState
from graph.schemas import PageClassification
from prompts.segregator import SEGREGATOR_PROMPT
from graph.utils.logger import get_json_logger
from graph.utils.pdf_utils import extract_specific_pages

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other",
]


class SegregatorAgent:
    """Classifies each PDF page into one of 9 document types using vision LLM."""

    def __init__(self, model: str = "llama-3.2-11b-vision-preview", max_tokens: int = 300):
        self.model = model
        self.max_tokens = max_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_not_exception_type(AuthenticationError),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry {retry_state.attempt_number} for page classification..."
        ),
    )
    async def _classify_page(self, llm_structured, image_b64: str) -> PageClassification:
        """Classify a single page using the vision model and Pydantic schema."""
        message = HumanMessage(
            content=[
                {"type": "text", "text": SEGREGATOR_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            ]
        )
        result = await llm_structured.ainvoke([message])

        # Simple normalization
        if result.classification.lower().strip() not in DOCUMENT_TYPES:
            result.classification = "other"

        return result

    async def _process_page(self, llm_structured, pdf_filepath: str, idx: int):
        """Extract and classify a single page."""
        try:
            images = extract_specific_pages(pdf_filepath, [idx])
            if not images:
                raise ValueError("No image extracted")

            result = await self._classify_page(llm_structured, images[0])
            return idx, result, None
        except AuthenticationError:
            raise
        except Exception as e:
            return idx, None, str(e)

    async def __call__(self, state: PipelineState) -> dict:
        """Callable so this class can act natively as a LangGraph Node."""
        request_id = state["request_id"]
        api_key = state["api_key"]
        pdf_filepath = state["pdf_filepath"]
        total_pages = state["total_pages"]
        node_logger = get_json_logger(__name__, request_id)

        llm = ChatGroq(
            model=self.model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=self.max_tokens,
        )
        llm_structured = llm.with_structured_output(PageClassification)

        # Classify each page concurrently with a semaphore to prevent API rate limit / 400 errors
        classifications: dict[str, list[int]] = {doc_type: [] for doc_type in DOCUMENT_TYPES}
        page_details = []
        semaphore = asyncio.Semaphore(3)

        async def throttled_process(idx):
            async with semaphore:
                return await self._process_page(llm_structured, pdf_filepath, idx)

        tasks = [throttled_process(i) for i in range(total_pages)]
        results = await asyncio.gather(*tasks)

        for idx, result, error in results:
            if error:
                node_logger.error(f"Page {idx}: classification failed after retries — {error}")
                classifications["other"].append(idx)
                page_details.append(
                    {
                        "page": idx,
                        "classification": "other",
                        "confidence": 0.0,
                        "reasoning": f"Classification failed: {error}",
                    }
                )
            else:
                classifications[result.classification].append(idx)
                page_details.append(result.dict())
                node_logger.info(f"Page {idx}: classified as '{result.classification}' (confidence: {result.confidence})")

        # Remove empty categories
        mapping = {k: v for k, v in classifications.items() if v}
        summary = {k: len(v) for k, v in mapping.items()}

        node_logger.info(f"Segregation complete: {json.dumps(summary)}")

        return {
            "page_classifications": {
                "summary": summary,
                "details": page_details,
                "mapping": mapping,
            }
        }


# Instantiate as a callable node for LangGraph
segregator_node = SegregatorAgent()


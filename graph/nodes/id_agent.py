"""ID Agent — extracts identity information from classified pages."""

from graph.schemas import IdentityExtraction
from prompts.id_extraction import ID_EXTRACTION_PROMPT
from graph.nodes.base_agent import BaseExtractionAgent

id_agent_node = BaseExtractionAgent(
    agent_name="ID Agent",
    result_key="id_result",
    prompt=ID_EXTRACTION_PROMPT,
    schema=IdentityExtraction,
    relevant_types=["identity_document", "claim_forms"],
    max_tokens=1000,
)

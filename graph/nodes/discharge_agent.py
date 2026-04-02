"""Discharge Summary Agent — extracts discharge details from classified pages."""

from graph.schemas import DischargeExtraction
from prompts.discharge_extraction import DISCHARGE_EXTRACTION_PROMPT
from graph.nodes.base_agent import BaseExtractionAgent

discharge_agent_node = BaseExtractionAgent(
    agent_name="Discharge Agent",
    result_key="discharge_result",
    prompt=DISCHARGE_EXTRACTION_PROMPT,
    schema=DischargeExtraction,
    relevant_types=["discharge_summary"],
    max_tokens=1500,
)

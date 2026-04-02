"""LangGraph workflow definition — the claim processing pipeline."""

import logging

from langgraph.graph import StateGraph, START, END

from graph.state import PipelineState
from graph.nodes.segregator import segregator_node
from graph.nodes.id_agent import id_agent_node
from graph.nodes.discharge_agent import discharge_agent_node
from graph.nodes.bill_agent import bill_agent_node
from graph.nodes.aggregator import aggregator_node

logger = logging.getLogger(__name__)


def build_pipeline() -> StateGraph:
    """Build and compile the claim processing LangGraph pipeline.

    Flow:
        START → Segregator → (fan-out) ID Agent, Discharge Agent, Bill Agent
                           → (fan-in)  Aggregator → END
    """
    builder = StateGraph(PipelineState)

    # Add nodes
    builder.add_node("segregator", segregator_node)
    builder.add_node("id_agent", id_agent_node)
    builder.add_node("discharge_agent", discharge_agent_node)
    builder.add_node("bill_agent", bill_agent_node)
    builder.add_node("aggregator", aggregator_node)

    # Entry: START → Segregator
    builder.add_edge(START, "segregator")

    # Fan-out: Segregator → all 3 extraction agents (run in parallel)
    builder.add_edge("segregator", "id_agent")
    builder.add_edge("segregator", "discharge_agent")
    builder.add_edge("segregator", "bill_agent")

    # Fan-in: All 3 agents → Aggregator
    builder.add_edge("id_agent", "aggregator")
    builder.add_edge("discharge_agent", "aggregator")
    builder.add_edge("bill_agent", "aggregator")

    # Exit: Aggregator → END
    builder.add_edge("aggregator", END)

    graph = builder.compile()
    logger.info("Pipeline graph compiled successfully")
    return graph


# Pre-compiled graph instance
pipeline = build_pipeline()


async def run_pipeline(
    claim_id: str,
    request_id: str,
    api_key: str,
    pdf_filepath: str,
    total_pages: int,
    page_thumbnails: list[str],
) -> dict:
    """Execute the claim processing pipeline.

    Args:
        claim_id: Unique claim identifier.
        request_id: Unique correlation ID for logging.
        api_key: Groq API key for LLM calls.
        pdf_filepath: Local temporary file path to the PDF.
        total_pages: Number of pages in the PDF.
        page_thumbnails: List of base64 low-res thumbnails.

    Returns:
        Final aggregated result dict.
    """
    initial_state: PipelineState = {
        "claim_id": claim_id,
        "request_id": request_id,
        "api_key": api_key,
        "pdf_filepath": pdf_filepath,
        "total_pages": total_pages,
        "page_thumbnails": page_thumbnails,
        "page_classifications": {},
        "id_result": {},
        "discharge_result": {},
        "bill_result": {},
        "final_result": {},
    }

    logger.info(f"Starting pipeline for claim {claim_id} ({total_pages} pages)")
    result = await pipeline.ainvoke(initial_state)
    logger.info(f"Pipeline complete for claim {claim_id}")
    return result["final_result"]

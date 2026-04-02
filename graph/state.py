"""Pipeline state definition for LangGraph workflow."""

from typing import TypedDict


class PipelineState(TypedDict):
    """Shared state across all nodes in the claim processing pipeline."""

    # Input
    claim_id: str
    request_id: str
    api_key: str
    pdf_filepath: str  # Local path to temporary PDF file
    total_pages: int  # Total number of pages in the PDF
    page_thumbnails: list[str]  # base64-encoded low-res PNG images for UI

    # Segregator output
    page_classifications: dict  # {summary, details, mapping}

    # Extraction agent outputs
    id_result: dict
    discharge_result: dict
    bill_result: dict

    # Final aggregated result
    final_result: dict

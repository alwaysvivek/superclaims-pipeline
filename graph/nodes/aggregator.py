from datetime import datetime, timezone
from graph.utils.logger import get_json_logger
from graph.state import PipelineState

def aggregator_node(state: PipelineState) -> dict:
    """Combine all extraction results into a final structured response."""
    request_id = state["request_id"]
    claim_id = state["claim_id"]
    node_logger = get_json_logger(__name__, request_id)
    
    page_classifications = state["page_classifications"]
    id_result = state.get("id_result", {})
    discharge_result = state.get("discharge_result", {})
    bill_result = state.get("bill_result", {})

    # Math Hallucination Check
    bill_data = bill_result.get("data", {})
    line_items = bill_data.get("line_items", [])
    extracted_total = bill_data.get("grand_total")
    
    math_validation = {"math_match": True, "discrepancy": 0.0}
    if line_items and extracted_total is not None:
        calc_total = sum(item.get("total", 0.0) for item in line_items)
        discrepancy = abs(calc_total - extracted_total)
        
        if discrepancy > 0.01:
            node_logger.warning(f"Math mismatch: Calculated {calc_total}, Extracted {extracted_total}")
            math_validation = {
                "math_match": False,
                "discrepancy": round(discrepancy, 2),
                "calculated_total": round(calc_total, 2),
                "extracted_total": round(extracted_total, 2)
            }

    final = {
        "claim_id": claim_id,
        "request_id": request_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "total_pages": state["total_pages"],
        "page_thumbnails": state.get("page_thumbnails", []),
        "document_classification": {
            "summary": page_classifications.get("summary", {}),
            "page_details": page_classifications.get("details", []),
        },
        "extracted_data": {
            "identity": id_result,
            "discharge_summary": discharge_result,
            "billing": bill_result,
        },
        "validation": {
            "billing": math_validation
        }
    }

    node_logger.info(f"Aggregator: Final result assembled for claim {claim_id}")
    return {"final_result": final}

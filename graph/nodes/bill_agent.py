"""Itemized Bill Agent — extracts billing details from classified pages."""

from graph.schemas import BillingExtraction
from prompts.bill_extraction import BILL_EXTRACTION_PROMPT
from graph.nodes.base_agent import BaseExtractionAgent

class BillAgent(BaseExtractionAgent):
    async def _post_process(self, extracted: BillingExtraction) -> dict:
        """Override to add calculated_total before returning."""
        data = extracted.dict()
        if extracted.line_items:
            calculated_total = sum(item.total for item in extracted.line_items)
            if calculated_total > 0:
                data["calculated_total"] = calculated_total
        return data

bill_agent_node = BillAgent(
    agent_name="Bill Agent",
    result_key="bill_result",
    prompt=BILL_EXTRACTION_PROMPT,
    schema=BillingExtraction,
    relevant_types=["itemized_bill", "cash_receipt"],
    max_tokens=2000,
)

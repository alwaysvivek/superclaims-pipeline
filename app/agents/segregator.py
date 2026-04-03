import json
from app.agents.base import BaseAgent
from app.models.state import GraphState
from langchain_core.messages import HumanMessage
import concurrent.futures
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class SegregatorAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    def _classify_page(self, page: dict) -> dict:
        prompt = f"""
        Classify the following document page text into exactly one of the following categories:
        claim_forms, cheque_or_bank_details, identity_document, itemized_bill, discharge_summary, prescription, investigation_report, cash_receipt, other.
        Return ONLY a JSON object with a single key 'page_type' and the categorized value. Example: {{"page_type": "identity_document"}}
        
        Document Text:
        {page['extracted_text']}
        """
        message = HumanMessage(content=prompt)
        try:
            logger.info(f"Segregator processing page {page['page_number']}")
            response = self.invoke_with_retry(message)
            content = response.content.replace("```json", "").replace("```", "").strip()
            # Find JSON segment
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                result = json.loads(content[start:end])
                page["page_type"] = result.get("page_type", "other")
            else:
                page["page_type"] = "other"
            return page, None
        except Exception as e:
            page["page_type"] = "other"
            return page, f"Segregation error on page {page['page_number']}: {str(e)}"

    def process(self, state: GraphState) -> dict:
        pages = state["pages"]
        updated_pages = []
        new_errors = []
        
        # Parallel processing for speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._classify_page, page.copy()) for page in pages]
            for future in concurrent.futures.as_completed(futures):
                page_res, error = future.result()
                updated_pages.append(page_res)
                if error:
                    new_errors.append(error)
        
        # Sort back by page number
        updated_pages.sort(key=lambda x: x["page_number"])
        return {"pages": updated_pages, "errors": new_errors}

def segregator_node(state: GraphState):
    agent = SegregatorAgent(api_key=state["api_key"])
    return agent.process(state)

import json
from app.agents.base import BaseAgent
from app.models.state import GraphState
from langchain_core.messages import HumanMessage
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class BaseExtractor(BaseAgent):
    def extract(self, pages: list, prompt: str, key_name: str) -> dict:
        if not pages:
            return {key_name: None, "errors": []}
            
        content_text = prompt + "\n\nAvailable Document Pages:\n"
        for page in pages:
            content_text += f"\n--- Page {page['page_number']} ---\n{page['extracted_text']}\n"
            
        message = HumanMessage(content=content_text)
        try:
            logger.info(f"Extractor invoked for {key_name} on {len(pages)} pages")
            response = self.invoke_with_retry(message)
            res_content = response.content.replace("```json", "").replace("```", "").strip()
            start = res_content.find("{")
            end = res_content.rfind("}") + 1
            if start != -1 and end != 0:
                result = json.loads(res_content[start:end])
                return {key_name: result, "errors": []}
            else:
                return {key_name: None, "errors": [f"Failed to parse JSON for {key_name}"]}
        except Exception as e:
            return {key_name: None, "errors": [f"Extraction error for {key_name}: {str(e)}"]}

def id_agent_node(state: GraphState):
    agent = BaseExtractor(api_key=state["api_key"])
    pages = [p for p in state.get("pages", []) if p.get("page_type") == "identity_document"]
    prompt = "Extract identity information: patient_name, dob, id_number. Return ONLY a JSON object."
    result = agent.extract(pages, prompt, "identity")
    return {"extracted_data": {"identity": result.get("identity")}, "errors": result.get("errors", [])}

def discharge_summary_node(state: GraphState):
    agent = BaseExtractor(api_key=state["api_key"])
    pages = [p for p in state.get("pages", []) if p.get("page_type") == "discharge_summary"]
    prompt = "Extract discharge summary facts: diagnosis, admit_date, discharge_date, physician. Return ONLY a JSON object."
    result = agent.extract(pages, prompt, "discharge_summary")
    return {"extracted_data": {"discharge_summary": result.get("discharge_summary")}, "errors": result.get("errors", [])}

def itemized_bill_node(state: GraphState):
    agent = BaseExtractor(api_key=state["api_key"])
    pages = [p for p in state.get("pages", []) if p.get("page_type") == "itemized_bill"]
    prompt = "Extract itemized bill details: list of items with costs, and total_amount. Return ONLY a JSON object."
    result = agent.extract(pages, prompt, "itemized_bill")
    return {"extracted_data": {"itemized_bill": result.get("itemized_bill")}, "errors": result.get("errors", [])}

from langgraph.graph import StateGraph, END
from app.models.state import GraphState
from app.agents.segregator import segregator_node
from app.agents.extractors import id_agent_node, discharge_summary_node, itemized_bill_node
from app.agents.aggregator import aggregator_node

def route_after_segregator(state: GraphState):
    destinations = []
    types = {p["page_type"] for p in state["pages"]}
    if "identity_document" in types:
        destinations.append("id_agent")
    if "discharge_summary" in types:
        destinations.append("discharge_summary_agent")
    if "itemized_bill" in types:
        destinations.append("itemized_bill_agent")
    
    if not destinations:
        return ["aggregator"]
    return destinations

def create_workflow():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("segregator", segregator_node)
    workflow.add_node("id_agent", id_agent_node)
    workflow.add_node("discharge_summary_agent", discharge_summary_node)
    workflow.add_node("itemized_bill_agent", itemized_bill_node)
    workflow.add_node("aggregator", aggregator_node)
    
    workflow.set_entry_point("segregator")
    
    workflow.add_conditional_edges(
        "segregator",
        route_after_segregator,
        {
            "id_agent": "id_agent",
            "discharge_summary_agent": "discharge_summary_agent",
            "itemized_bill_agent": "itemized_bill_agent",
            "aggregator": "aggregator"
        }
    )
    
    workflow.add_edge("id_agent", "aggregator")
    workflow.add_edge("discharge_summary_agent", "aggregator")
    workflow.add_edge("itemized_bill_agent", "aggregator")
    workflow.add_edge("aggregator", END)
    
    return workflow.compile()

claim_workflow = create_workflow()

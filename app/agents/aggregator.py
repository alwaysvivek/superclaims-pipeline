from app.models.state import GraphState

def aggregator_node(state: GraphState):
    # Empty node, because extracted_data is populated directly via LangGraph state annotations (operator.ior)
    return {}

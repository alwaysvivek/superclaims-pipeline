import operator
from typing import TypedDict, List, Optional, Annotated

class PageModel(TypedDict):
    page_number: int
    extracted_text: str
    page_type: Optional[str]

class GraphState(TypedDict):
    claim_id: str
    api_key: str
    pages: List[PageModel]
    # We use Annotated with operator.ior to handle dictionary updates in parallel
    extracted_data: Annotated[dict, operator.ior]
    errors: Annotated[list[str], operator.add]

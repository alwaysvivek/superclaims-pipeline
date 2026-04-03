from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ProcessClaimRequest(BaseModel):
    claim_id: str = Field(..., description="Unique claim identifier")

class ProcessClaimResponse(BaseModel):
    claim_id: str
    status: str
    extracted_data: Dict[str, Any]
    errors: List[str] = []

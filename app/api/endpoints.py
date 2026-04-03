from fastapi import APIRouter, Request, Response, status, File, UploadFile, Form, HTTPException
from typing import Optional
from app.models.schemas import ProcessClaimResponse
from app.services.pdf_service import PDFProcessor
from app.services.workflow import claim_workflow
from app.models.state import GraphState
from app.core.logger import setup_logger
from app.core.limiter import limiter

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/process", response_model=ProcessClaimResponse)
@limiter.limit("5/minute")
async def process_claim(
    request: Request,
    response: Response,
    claim_id: str = Form(...),
    groq_api_key: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid file upload intent: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        logger.info(f"Starting pipeline execution for claim_id: {claim_id}")
        content = await file.read()
        pages = PDFProcessor.process_pdf(content)
        
        initial_state: GraphState = {
            "claim_id": claim_id,
            "api_key": groq_api_key,
            "pages": pages,
            "extracted_data": {},
            "errors": []
        }
        
        # Invoke workflow
        logger.info(f"Triggering LangGraph workflow for claim_id: {claim_id}")
        final_state = claim_workflow.invoke(initial_state)
        logger.info(f"Completed LangGraph workflow for claim_id: {claim_id}")
        
        errors = final_state.get("errors", [])
        if errors:
            logger.warning(f"Partial errors logged processing claim_id: {claim_id}")
            response.status_code = status.HTTP_207_MULTI_STATUS
        
        return ProcessClaimResponse(
            claim_id=final_state.get("claim_id", claim_id),
            status="partial_success" if errors else "completed",
            extracted_data=final_state.get("extracted_data", {}),
            errors=errors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

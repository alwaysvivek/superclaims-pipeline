import logging
import uuid
import os
import tempfile
import aiofiles
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.background import BackgroundTasks
from groq import AuthenticationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from graph.utils.pdf_utils import extract_thumbnails, get_total_pages
from graph.utils.logger import setup_json_logging, get_json_logger
from graph.workflow import run_pipeline

# Configure structured JSON logging
setup_json_logging(logging.INFO)


class ClaimProcessingApp:
    """Encapsulates the FastAPI application, middleware, and route registration."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.limiter = Limiter(key_func=get_remote_address)
        self.app = FastAPI(
            title="Claim Processing Pipeline",
            description="AI-powered document segregation and extraction for insurance claims",
            version="1.0.0",
            lifespan=self._lifespan,
        )
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        self._register_routes()

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        self.logger.info("🚀 Claim Processing Pipeline API starting up")
        yield
        self.logger.info("👋 Shutting down")

    # ── PDF helpers ──────────────────────────────────────────────

    async def _stream_to_disk(self, file: UploadFile, dest: str) -> None:
        """Stream an UploadFile to disk in 1 MB chunks (zero RAM spike)."""
        async with aiofiles.open(dest, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)

        if os.path.getsize(dest) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

    @staticmethod
    def _cleanup(path: str, directory: str):
        """Remove temporary PDF and its parent directory."""
        try:
            os.remove(path)
            os.rmdir(directory)
        except Exception:
            pass

    # ── Route registration ───────────────────────────────────────

    def _register_routes(self):
        """Register all API endpoints on the FastAPI instance."""

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "ok", "service": "claim-processing-pipeline"}

        @self.app.post("/api/process")
        @self.limiter.limit("5/minute")
        async def process_claim(
            request: Request,
            background_tasks: BackgroundTasks,
            claim_id: str = Form(..., description="Unique claim identifier"),
            api_key: str = Form(..., description="Groq API key"),
            file: UploadFile = File(..., description="PDF file to process"),
        ):
            """Process a PDF claim document through the AI pipeline.

            1. Generates a unique request_id for the pipeline run
            2. Streams PDF to a temporary file on disk
            3. Segregator classifies each page
            4. Extraction agents process their assigned pages in parallel
            5. Aggregator combines all results
            """
            request_id = str(uuid.uuid4())
            req_logger = get_json_logger(__name__, request_id)
            req_logger.info(f"Received process request for claim {claim_id}")

            # ── Validate inputs ──────────────────────────────────
            if not claim_id.strip():
                raise HTTPException(status_code=400, detail="claim_id is required")
            if not api_key.strip():
                raise HTTPException(status_code=400, detail="api_key is required")
            if not file.filename or not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="File must be a PDF")

            # ── Stream PDF to temp disk ──────────────────────────
            temp_dir = tempfile.mkdtemp()
            temp_pdf_path = os.path.join(temp_dir, f"{request_id}.pdf")
            background_tasks.add_task(self._cleanup, temp_pdf_path, temp_dir)

            try:
                await self._stream_to_disk(file, temp_pdf_path)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

            # ── Extract metadata & thumbnails ────────────────────
            try:
                req_logger.info("Extracting PDF metadata and thumbnails...")
                total_pages = get_total_pages(temp_pdf_path)
                thumbnails = extract_thumbnails(temp_pdf_path)
                req_logger.info(f"Extracted {total_pages} pages metadata")
            except Exception as e:
                req_logger.error(f"PDF extraction failed: {e}")
                raise HTTPException(status_code=422, detail=f"Failed to process PDF: {str(e)}")

            # ── Run LangGraph pipeline ───────────────────────────
            try:
                result = await run_pipeline(
                    claim_id=claim_id.strip(),
                    request_id=request_id,
                    api_key=api_key.strip(),
                    pdf_filepath=temp_pdf_path,
                    total_pages=total_pages,
                    page_thumbnails=thumbnails,
                )
                return result
            except AuthenticationError:
                req_logger.error("Authentication failed")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Groq API Key. Please verify your key and try again.",
                )
            except Exception as e:
                self.logger.error(f"Pipeline error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


# ── Application entry point ──────────────────────────────────────
claim_app = ClaimProcessingApp()
app = claim_app.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


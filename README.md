# SuperClaims Pipeline

AI-powered claims processing pipeline using FastAPI and LangGraph with agent-based document classification and extraction.

## Architecture

```
START → [Segregator Agent] → [ID Agent]               → [Aggregator] → END
                            → [Discharge Summary Agent] ↗
                            → [Itemized Bill Agent]     ↗
```

### How It Works

1. **Document Ingestion** — Claim PDF is uploaded via the API endpoint
2. **Disk Streaming** — PDF is streamed to a temporary file in chunks (zero RAM spike, OOM-safe)
3. **Segregation** — AI classifies each page concurrently (`asyncio.gather`) into one of 9 document types using Groq's vision model
4. **Parallel Extraction** — Three specialized agents extract only their assigned pages directly from the disk file:
   - **ID Agent** — Extracts patient name, DOB, policy number, ID details
   - **Discharge Agent** — Extracts diagnosis, admission/discharge dates, physician info
   - **Bill Agent** — Extracts itemized charges with line items and calculates totals (includes math hallucination guard)
5. **Aggregation** — All results are combined into a single structured JSON response with validation checks

### Document Types (Segregator)

| Type | Description |
|------|-------------|
| `claim_forms` | Insurance claim application forms |
| `cheque_or_bank_details` | Cheques, bank account details |
| `identity_document` | Aadhaar, PAN, passport, etc. |
| `itemized_bill` | Hospital bills with cost breakdowns |
| `discharge_summary` | Hospital discharge summaries |
| `prescription` | Doctor prescriptions |
| `investigation_report` | Lab/diagnostic reports |
| `cash_receipt` | Payment receipts |
| `other` | Unclassified documents |

## Quick Start

### 1. Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com/) — **Required.** This service uses a Bring Your Own Key (BYOK) model. You must provide your personal Groq API key with every request (see [API Reference](#api-reference) below).

### 2. Setup & Run

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Test It

```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=CLM-001" \
  -F "api_key=gsk_YOUR_GROQ_API_KEY_HERE" \
  -F "file=@path/to/claim.pdf"
```

> **Note:** The `api_key` field is required. Get a free key at [console.groq.com](https://console.groq.com/).

## Tech Stack

- **Framework:** FastAPI
- **Orchestration:** LangGraph
- **LLM Provider:** Groq (Llama 3.2 Vision)
- **PDF Processing:** PyMuPDF
- **Retry Logic:** Tenacity (exponential backoff)
- **Async I/O:** aiofiles (chunked disk streaming)

## API Reference

### `POST /api/process`

Process a PDF claim document.

**Request** (multipart/form-data):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | string | ✅ | Unique claim identifier |
| `api_key` | string | ✅ | Your Groq API key ([get one here](https://console.groq.com/)) |
| `file` | file | ✅ | PDF document to process |

**Response** (JSON):
```json
{
  "claim_id": "CLM-001",
  "request_id": "a1b2c3d4-...",
  "processed_at": "2026-04-01T00:00:00+00:00",
  "total_pages": 10,
  "document_classification": {
    "summary": { "identity_document": 2, "discharge_summary": 3, "itemized_bill": 2 },
    "page_details": [...]
  },
  "extracted_data": {
    "identity": { "status": "success", "data": { "patient_name": "...", ... } },
    "discharge_summary": { "status": "success", "data": { "diagnosis": "...", ... } },
    "billing": { "status": "success", "data": { "line_items": [...], "grand_total": 0.0 } }
  },
  "validation": {
    "billing": {
      "math_match": true,
      "discrepancy": 0.0
    }
  }
}
```

### `GET /health`

Health check endpoint. Returns `{"status": "ok"}`.

## Project Structure

```
├── main.py                      # FastAPI application (ClaimProcessingApp class)
├── requirements.txt             # Python dependencies
├── graph/
│   ├── state.py                 # LangGraph state definition
│   ├── schemas.py               # Pydantic extraction schemas
│   ├── workflow.py              # StateGraph orchestration
│   ├── nodes/
│   │   ├── base_agent.py        # BaseExtractionAgent (OOP base class)
│   │   ├── segregator.py        # SegregatorAgent — AI page classifier
│   │   ├── id_agent.py          # Identity extraction (inherits BaseExtractionAgent)
│   │   ├── discharge_agent.py   # Discharge summary extraction (inherits BaseExtractionAgent)
│   │   ├── bill_agent.py        # BillAgent — billing extraction with math verification
│   │   └── aggregator.py        # Result combiner + hallucination check
│   └── utils/
│       ├── pdf_utils.py         # PDF → image utilities (disk-based extraction)
│       └── logger.py            # Structured JSON logging with request correlation
├── prompts/                     # LLM prompt templates
└── README.md
```

## License

MIT


# SuperClaims AI Pipeline

A production-grade FastAPI service that processes multi-page PDF medical claims using LangGraph. The workflow orchestrates intelligent document segregation and parallel multi-agent extraction using Groq's high-performance Large Language Models and Tesseract OCR.

## 🚀 Architecture
This pipeline embraces Object-Oriented Programming (OOP) and a directed acyclic graph (DAG) routing architecture. 

**Workflow Route:**
```text
START 
  ↓
[Segregator Agent] (Categorizes each page into 9 distinct medical classes via OCR + LLM)
  ↓
  ├──→ [ID Agent] (Extracts Patient Info & Policies)
  ├──→ [Discharge Summary Agent] (Extracts Admission Dates, Physician, Diagnosis)
  └──→ [Itemized Bill Agent] (Extracts Line Items & Total Cost)
  ↓
[Aggregator Node] (Safely merges parallel data states)
  ↓
 END
```

**Key Features:**
- **Zero-Waste Processing:** The Segregator isolates pages by document type. Extraction agents only read the exact pages associated with their domain, massively reducing token burn.
- **OCR-First Processing:** Native PyMuPDF + Tesseract integration smoothly handles purely scanned, non-text PDFs (like protected image scans) and feeds ultra-fast text prompts to Groq.
- **BYOK (Bring Your Own Key):** Securely pass your API key per request in the endpoint form data without relying on insecure environment variable hardcoding.

## 🛠️ Tech Stack
- **FastAPI**: Endpoint serving and async handling.
- **LangGraph**: Stateful, parallel multi-agent orchestration.
- **Langchain-Groq**: Deep integration with `llama-3.3-70b-versatile` for blazing-fast inference.
- **PyMuPDF & PyTesseract**: Rapid local slicing of PDFs into images and localized text extraction.

## 📦 Installation & Setup

1. **Clone the repo and create a virtual environment**
```bash
git clone https://github.com/your-username/superclaims-pipeline.git
cd superclaims-pipeline
python -m venv venv
source venv/bin/activate
```

2. **Install System Dependencies (For OCR)**
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

3. **Install Python Requirements**
```bash
pip install -r requirements.txt
```

## 🎯 Usage

1. **Start the FastAPI Server**
```bash
python -m app.main
```
Server runs locally at `http://0.0.0.0:8000`.

2. **Test the Endpoint**
Using cURL or Postman, hit the `/api/process` endpoint.

```bash
curl -X POST "http://127.0.0.1:8000/api/process" \
     -F "claim_id=CLM-1002" \
     -F "groq_api_key=gsk_YOUR_API_KEY_HERE" \
     -F "file=@final_image_protected.pdf"
```

## Deployment

Deployment was attempted but not completed due to errors encountered during setup. 

Given the assignment timeline, priority was given to completing and stabilizing the core document processing pipeline.

The system runs fully in a local environment.

## 📂 Project Structure
```text
.
├── app/
│   ├── agents/
│   │   ├── base.py              # Parent constructor initializing ChatGroq
│   │   ├── segregator.py        # Classifies pages via ThreadPool concurrency mapping
│   │   ├── extractors.py        # ID, Discharge, and Bill dedicated agents
│   │   └── aggregator.py        # Unifies and syncs parallel states
│   ├── api/
│   │   └── endpoints.py         # FastAPI POST route
│   ├── core/
│   │   └── config.py            # Pydantic BaseSettings
│   ├── models/
│   │   ├── schemas.py           # Endpoint Pydantic validation
│   │   └── state.py             # LangGraph TypedDict definitions
│   ├── services/
│   │   ├── pdf_service.py       # Tesseract + PyMuPDF pipeline
│   │   └── workflow.py          # StateGraph edge connections
│   └── main.py                  # API Factory
├── requirements.txt
└── README.md
```

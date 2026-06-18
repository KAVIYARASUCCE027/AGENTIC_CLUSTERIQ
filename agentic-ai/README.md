# K8S Agentic AI Service

An **Agentic AI platform** for Kubernetes monitoring and analysis. Built with **FastAPI**, **LangGraph**, **LangChain**, and **Google Gemini**, this service provides intelligent CPU analysis and actionable recommendations for Kubernetes pods.

## Architecture

```
START → Collect Metrics → Analyze with Gemini → Generate Recommendations → END
```

The service uses a **LangGraph StateGraph** pipeline with three sequential nodes:

| Node        | Responsibility                                      |
|-------------|-----------------------------------------------------|
| **Collect** | Fetches CPU metrics from Prometheus (mock data)     |
| **Analyze** | Sends metrics to Gemini for expert analysis         |
| **Recommend** | Generates actionable K8s remediation guidance     |

## Project Structure

```
agentic-ai/
├── agents/          # High-level agent orchestrators
├── nodes/           # LangGraph processing nodes
├── services/        # LLM and Prometheus integrations
├── schemas/         # Pydantic request/response models
├── prompts/         # Reusable prompt templates
├── memory/          # Conversation history management
├── graph/           # LangGraph workflow definitions
├── config/          # Application settings
├── main.py          # FastAPI application entry point
├── requirements.txt # Python dependencies
├── .env             # Environment variables (not committed)
└── .gitignore
```

## Tech Stack

- **Python 3.12+**
- **FastAPI** — Web framework
- **LangGraph** — Agent workflow orchestration
- **LangChain** — LLM integration framework
- **Google Gemini** (`gemini-2.5-flash`) — Large Language Model
- **Pydantic** — Data validation and settings management
- **Uvicorn** — ASGI server

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agentic-ai
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Edit the `.env` file and set your Google API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-2.5-flash
HOST=0.0.0.0
PORT=8000
```

## Running the Service

```bash
uvicorn main:app --reload
```

Or run directly:

```bash
python main.py
```

The service will start at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint        | Description                              |
|--------|-----------------|------------------------------------------|
| GET    | `/`             | Service status check                     |
| GET    | `/health`       | Health check                             |
| GET    | `/test-gemini`  | Test Gemini LLM connectivity             |
| POST   | `/cpu`          | Run CPU analysis agent for a K8s pod     |

### Swagger Documentation

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

### Example: CPU Analysis

**Request:**

```bash
curl -X POST http://localhost:8000/cpu \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default", "pod_name": "nginx"}'
```

**Response:**

```json
{
  "status": "success",
  "message": "## CPU Analysis\n\n...\n\n---\n\n## Recommendations\n\n..."
}
```

## Phase 1 — Completed Features

- [x] FastAPI application with health checks
- [x] Google Gemini LLM integration (singleton)
- [x] Pydantic settings with `.env` loading
- [x] CPU analysis LangGraph pipeline (collect → analyze → recommend)
- [x] Structured prompt templates
- [x] In-memory conversation history
- [x] Mock Prometheus metrics service
- [x] Comprehensive logging
- [x] Error handling across all layers
- [x] OpenAPI documentation

## License

MIT

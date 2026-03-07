# Action Item Extractor

A FastAPI-based web application that extracts action items from meeting notes using either heuristic-based extraction or LLM-powered extraction (via Ollama).

## Overview

This project provides:
- A REST API for extracting action items from text
- Two extraction methods: heuristic-based and LLM-powered (using Ollama)
- A simple HTML frontend for interacting with the API
- SQLite database for storing notes and action items

## Project Structure

```
week2/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── db.py                 # Database layer (SQLite)
│   ├── schemas.py            # Pydantic models for request/response
│   ├── routers/
│   │   ├── notes.py          # Notes API endpoints
│   │   └── action_items.py   # Action items API endpoints
│   └── services/
│       └── extract.py        # Extraction logic (heuristic + LLM)
├── frontend/
│   └── index.html            # Simple HTML frontend
├── tests/
│   └── test_extract.py       # Unit tests for extraction
└── data/                     # SQLite database storage
```

## Setup

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- Ollama (for LLM-powered extraction)

### Installation

1. Install dependencies using Poetry:

```bash
poetry install
```

2. Activate the virtual environment:

```bash
poetry shell
```

3. Ensure Ollama is running locally with the `llama3.1:8b` model:

```bash
ollama serve
ollama pull llama3.1:8b
```

## Running the Application

Start the FastAPI server:

```bash
poetry run uvicorn week2.app.main:app --reload
```

The application will be available at:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs

## API Endpoints

### Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notes` | Create a new note |
| GET | `/notes/list` | List all notes |
| GET | `/notes/{note_id}` | Get a specific note |
| DELETE | `/notes/{note_id}` | Delete a note |

### Action Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/action-items/extract` | Extract action items (heuristic) |
| POST | `/action-items/extract-llm` | Extract action items (LLM-powered) |
| GET | `/action-items` | List all action items |
| GET | `/action-items/{action_item_id}` | Get a specific action item |
| POST | `/action-items/{action_item_id}/done` | Mark action item as done |

### Request/Response Examples

#### Extract Action Items (POST /action-items/extract)

**Request:**
```json
{
  "text": "Meeting notes:\n- [ ] Set up database\n- Implement API endpoint",
  "save_note": true
}
```

**Response:**
```json
{
  "note_id": 1,
  "items": [
    {"id": 1, "note_id": 1, "text": "Set up database", "done": false, "created_at": "..."},
    {"id": 2, "note_id": 1, "text": "Implement API endpoint", "done": false, "created_at": "..."}
  ]
}
```

#### List Notes (GET /notes/list)

**Response:**
```json
[
  {"id": 1, "content": "Meeting notes...", "created_at": "2024-01-01 12:00:00"}
]
```

## Extraction Methods

### Heuristic-based Extraction (`extract_action_items`)

Uses pattern matching to identify action items based on:
- Bullet points (`-`, `*`, numbered lists)
- Keywords (`TODO:`, `ACTION:`, `NEXT:`)
- Checkboxes (`[ ]`, `[todo]`)

### LLM-powered Extraction (`extract_action_items_llm`)

Uses Ollama with the `llama3.1:8b` model to intelligently extract action items from natural language text.

## Running Tests

Run the test suite using pytest:

```bash
poetry run pytest week2/tests/test_extract.py -v
```

Expected output:
```
============================= test session starts ==============================
week2/tests/test_extract.py::test_extract_bullets_and_checkboxes PASSED
week2/tests/test_extract.py::test_llm_extract_bullet_list PASSED
week2/tests/test_extract.py::test_llm_extract_keyword_prefixed PASSED
week2/tests/test_llm_extract_empty_input PASSED
week2/tests/test_llm_extract_checkboxes PASSED

============================== 5 passed in X.XXs ===============================
```

## Technology Stack

- **Framework**: FastAPI
- **Database**: SQLite (via sqlite3)
- **Validation**: Pydantic
- **LLM**: Ollama (llama3.1:8b)
- **Testing**: pytest
- **Package Management**: Poetry

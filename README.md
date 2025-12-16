# Audit Assistant (Agentic AI)

Local setup for the Audit Assistant (API + Ollama) using Docker Compose.

## Prerequisites
- Git
- Docker Desktop

## Project layout
```text
audit-assistant/
├── docker-compose.yml
├── .env.example
├── .env               # local only (do not commit)
├── data/              # place PDFs/CSVs here (mounted into the container)
└── README.md

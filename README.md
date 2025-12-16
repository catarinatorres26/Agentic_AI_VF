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

## Run locally

```bash
git clone https://github.com/catarinatorres26/Agentic_AI_VF.git
cd Agentic_AI_VF/audit-assistant
cp .env.example .env

docker compose up -d ollama
docker exec -it ollama ollama pull qwen2.5:7b
docker compose up --build

## Ask the agent

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'


### Analisar CSV
```markdown
## Analyze a CSV

```bash
curl -X POST http://localhost:8000/analyze_csv \
  -F "file=@data/sample.csv"


### Preferências / memória
```markdown
## Preferences

```bash
curl http://localhost:8000/preferences


# src/server/app.py

import time

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import ollama

from src.rag.rag_engine import AuditRAG
from src.memory.memory_store import MemoryStore
from src.tools.csv_analyzer import analyze_csv_bytes

from src.observability.logger import get_logger
from src.observability.middleware import RequestLoggingMiddleware

# -------------------------------------------------
# App & Observability
# -------------------------------------------------

app = FastAPI(
    title="Audit Assistant - API (Qwen2.5 7B + RAG + Memory + Tools + Observability)"
)

log = get_logger()
app.add_middleware(RequestLoggingMiddleware)

# Core components
rag = AuditRAG()
memory = MemoryStore()

# -------------------------------------------------
# Models
# -------------------------------------------------

class AskRequest(BaseModel):
    question: str


class PreferencesUpdateRequest(BaseModel):
    answer_style: str | None = None
    language: str | None = None
    require_sources: bool | None = None


# -------------------------------------------------
# Health
# -------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "audit-assistant",
        "model": "qwen2.5:7b",
        "features": ["rag", "sources", "memory", "csv_tool", "observability"],
        "phase": 10,
    }


# -------------------------------------------------
# Memory
# -------------------------------------------------

@app.get("/preferences")
async def get_preferences():
    return memory.get_preferences()


@app.post("/preferences")
async def update_preferences(body: PreferencesUpdateRequest):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma preferência para atualizar.",
        )
    updated = memory.set_preferences(updates)
    return {"status": "ok", "preferences": updated}


# -------------------------------------------------
# Main agent endpoint
# -------------------------------------------------

@app.post("/ask")
async def ask_agent(body: AskRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="A pergunta ('question') não pode estar vazia.",
        )

    # -----------------------------
    # Preferences
    # -----------------------------
    prefs = memory.get_preferences()
    answer_style = prefs.get("answer_style", "bullets")
    language = prefs.get("language", "pt")
    require_sources = prefs.get("require_sources", True)

    style_instruction = (
        "Responde em pontos (bullets) e com headings curtos."
        if answer_style == "bullets"
        else "Responde em texto corrido, claro e conciso."
    )

    sources_instruction = (
        "No final, inclui uma secção 'Fontes' e refere os PDFs/páginas relevantes."
        if require_sources
        else "Não é necessário incluir secção de fontes."
    )

    system_prompt = (
        "És um assistente especializado em auditoria. "
        "Responde apenas com base no contexto fornecido. "
        "Se a resposta não estiver claramente suportada pelo contexto, "
        "indica explicitamente que não existe evidência suficiente. "
        f"Idioma: {language}. "
        f"{style_instruction} "
        f"{sources_instruction}"
    )

    # -----------------------------
    # RAG (COM MEDIÇÃO DE TEMPO)
    # -----------------------------
    try:
        t0 = time.perf_counter()
        context = rag.search_context(question, k=3)
        sources = rag.build_sources(question, k=3)
        rag_ms = (time.perf_counter() - t0) * 1000.0
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar documentos de auditoria (RAG): {e}",
        )

    # -----------------------------
    # LLM (COM MEDIÇÃO DE TEMPO)
    # -----------------------------
    try:
        t1 = time.perf_counter()
        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Contexto de auditoria:\n{context}"},
                {"role": "user", "content": question},
            ],
        )
        llm_ms = (time.perf_counter() - t1) * 1000.0
        answer = response["message"]["content"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Falha ao chamar o modelo via Ollama. "
                "Verifica se o Ollama está ativo e se o modelo qwen2.5:7b existe. "
                f"Erro: {e}"
            ),
        )

    # -----------------------------
    # Observability log
    # -----------------------------
    log.info(
        "ask_processed",
        extra={
            "question_len": len(question),
            "rag_ms": round(rag_ms, 2),
            "llm_ms": round(llm_ms, 2),
            "sources_count": len(sources),
            "preferences_used": prefs,
        },
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "preferences_used": prefs,
        "metrics": {
            "rag_ms": round(rag_ms, 2),
            "llm_ms": round(llm_ms, 2),
        },
    }


# -------------------------------------------------
# CSV analysis tool
# -------------------------------------------------

@app.post("/analyze_csv")
async def analyze_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Por favor envia um ficheiro .csv",
        )

    try:
        content = await file.read()
        result = analyze_csv_bytes(content)
        return {
            "filename": file.filename,
            "summary": result.summary,
            "preview_rows": result.preview_rows,
            "column_stats": result.column_stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao analisar CSV: {e}",
        )

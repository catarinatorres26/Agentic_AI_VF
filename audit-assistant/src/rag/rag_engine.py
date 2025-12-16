# src/rag/rag_engine.py

import os
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class AuditRAG:
    def __init__(self, docs_path: str = "data/docs") -> None:
        self.docs_path = docs_path
        self.vectorstore: FAISS | None = None

    def _load_pdfs(self):
        if not os.path.isdir(self.docs_path):
            raise ValueError(
                f"Pasta não encontrada: {self.docs_path}. Cria-a com: mkdir -p {self.docs_path}"
            )

        pdf_files = [f for f in os.listdir(self.docs_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            raise ValueError(f"Não encontrei PDFs em {self.docs_path}. Coloca pelo menos 1 PDF lá dentro.")

        documents = []
        for file in pdf_files:
            file_path = os.path.join(self.docs_path, file)
            loader = PyPDFLoader(file_path)
            docs = loader.load()

            # Garantir metadata útil (file + page)
            for d in docs:
                d.metadata["source"] = file  # nome do PDF
                # PyPDFLoader normalmente já mete page, mas garantimos fallback
                if "page" not in d.metadata:
                    d.metadata["page"] = None

            documents.extend(docs)

        return documents

    def load_and_index(self) -> None:
        documents = self._load_pdfs()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        )
        chunks = splitter.split_documents(documents)

        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vectorstore = FAISS.from_documents(chunks, embeddings)

    def search_docs(self, query: str, k: int = 3):
        if self.vectorstore is None:
            self.load_and_index()
        return self.vectorstore.similarity_search(query, k=k)

    def search_context(self, query: str, k: int = 3) -> str:
        docs = self.search_docs(query, k=k)
        return "\n\n".join(d.page_content for d in docs)

    def build_sources(self, query: str, k: int = 3, snippet_chars: int = 240) -> List[Dict[str, Any]]:
        docs = self.search_docs(query, k=k)
        sources = []
        for d in docs:
            file = d.metadata.get("source", "unknown")
            page = d.metadata.get("page", None)
            text = (d.page_content or "").strip().replace("\n", " ")
            snippet = text[:snippet_chars] + ("..." if len(text) > snippet_chars else "")
            sources.append({"file": file, "page": page, "snippet": snippet})
        return sources

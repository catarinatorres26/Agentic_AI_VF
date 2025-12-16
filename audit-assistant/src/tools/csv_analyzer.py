# src/tools/csv_analyzer.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class CSVAnalysisResult:
    summary: Dict[str, Any]
    preview_rows: List[Dict[str, Any]]
    column_stats: Dict[str, Any]


def analyze_csv_bytes(
    csv_bytes: bytes,
    max_preview_rows: int = 10,
) -> CSVAnalysisResult:
    """
    Analisa um CSV (bytes) com pandas e devolve um resumo útil para auditoria.
    Não executa código arbitrário; faz apenas estatísticas básicas.
    """
    # Tentativas comuns de encoding
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = csv_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Não consegui decodificar o CSV (tenta UTF-8).")

    # Lê CSV
    from io import StringIO
    df = pd.read_csv(StringIO(text))

    # Resumo
    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_values_total": int(df.isna().sum().sum()),
    }

    # Preview (amostra)
    preview = df.head(max_preview_rows).to_dict(orient="records")

    # Estatísticas simples por coluna
    column_stats: Dict[str, Any] = {}
    for col in df.columns:
        s = df[col]
        stats: Dict[str, Any] = {"dtype": str(s.dtype), "missing": int(s.isna().sum())}

        # Numéricas
        if pd.api.types.is_numeric_dtype(s):
            stats.update(
                {
                    "min": None if s.dropna().empty else float(s.min()),
                    "max": None if s.dropna().empty else float(s.max()),
                    "mean": None if s.dropna().empty else float(s.mean()),
                }
            )
        # Texto/categorias
        else:
            top = s.dropna().astype(str).value_counts().head(5)
            stats["top_values"] = [{"value": k, "count": int(v)} for k, v in top.items()]

        column_stats[col] = stats

    return CSVAnalysisResult(summary=summary, preview_rows=preview, column_stats=column_stats)

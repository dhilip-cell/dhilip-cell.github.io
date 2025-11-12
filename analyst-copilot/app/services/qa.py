from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class QAResult:
    answer: str
    topic: Optional[str] = None
    confidence: float = 0.0


class KnowledgeBaseQA:
    """TF-IDF powered retrieval over a curated analytics knowledge base."""

    def __init__(
        self, knowledge_base_path: Optional[Path] = None, min_confidence: float = 0.22
    ) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        default_path = base_dir / "data" / "knowledge_base.json"
        self.knowledge_base_path = knowledge_base_path or default_path
        self.min_confidence = min_confidence

        self.entries = self._load_entries()
        self.documents = self._build_documents(self.entries)

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self.document_vectors = (
            self.vectorizer.fit_transform(self.documents)
            if self.documents
            else None
        )

        self.rule_map = self._build_rule_map()

    def _load_entries(self) -> list[dict]:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base file not found: {self.knowledge_base_path}"
            )
        with self.knowledge_base_path.open(encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _build_documents(entries: Sequence[dict]) -> list[str]:
        docs: list[str] = []
        for entry in entries:
            joined_questions = " ".join(entry.get("questions", []))
            text = f"{entry.get('topic', '')}. {joined_questions}. {entry.get('answer', '')}"
            docs.append(text)
        return docs

    @staticmethod
    def _build_rule_map() -> dict[str, str]:
        return {
            r"\bgoogle\s?sheets?\b": (
                "In Google Sheets you can speed up analytics by using FILTER, QUERY, "
                "and Pivot tables. Combine named ranges with the Explore feature for "
                "automatic visual insights."
            ),
            r"\bexcel\b": (
                "Excel analysts rely on dynamic arrays, XLOOKUP, Power Query, and "
                "Power Pivot for modeling larger datasets. Consider using Alt + Shift "
                "+ = for quick auto-sum blocks."
            ),
            r"\bpower\s?bi\b": (
                "Power BI best practice: split your model into Star Schema tables, "
                "enable incremental refresh for large fact tables, and validate DAX "
                "with Performance Analyzer."
            ),
            r"\btableau\b": (
                "In Tableau, prefer extracts for faster dashboards, use Level of Detail "
                "expressions for cohort logic, and document data sources with Data Catalog."
            ),
            r"\bsql\b": (
                "SQL tip: profile the table with COUNT(*), MIN/MAX timestamps, and use "
                "WINDOW functions (ROW_NUMBER, LAG, LEAD) for advanced analytics."
            ),
            r"\bspss\b": (
                "SPSS workflows often start with Analyze → Descriptive Statistics. For "
                "predictive modeling, check out Analyze → Regression → Linear or "
                "Logistic, and export syntax for reproducibility."
            ),
        }

    def _apply_rules(self, question: str) -> Optional[QAResult]:
        for pattern, response in self.rule_map.items():
            if re.search(pattern, question, flags=re.IGNORECASE):
                return QAResult(answer=response, confidence=0.65)
        return None

    def answer(self, question: str) -> QAResult:
        question = question.strip()
        if not question:
            return QAResult(answer="Please provide a question to analyze.")

        rule_hit = self._apply_rules(question)
        if rule_hit:
            return rule_hit

        if self.document_vectors is None:
            return QAResult(
                answer=(
                    "The knowledge base is not ready yet. Please upload data or ask again later."
                )
            )

        query_vector = self.vectorizer.transform([question])
        similarities = cosine_similarity(query_vector, self.document_vectors)
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[0, best_idx])

        if best_score < self.min_confidence:
            return QAResult(
                answer=(
                    "I do not have a confident answer yet. Try rephrasing or provide more detail."
                ),
                confidence=best_score,
            )

        match = self.entries[best_idx]
        return QAResult(
            answer=match.get("answer", "No answer available."),
            topic=match.get("topic"),
            confidence=best_score,
        )


aq_engine: Optional[KnowledgeBaseQA] = None


def get_qa_engine() -> KnowledgeBaseQA:
    global qa_engine
    if qa_engine is None:
        qa_engine = KnowledgeBaseQA()
    return qa_engine

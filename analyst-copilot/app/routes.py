from __future__ import annotations

import secrets
from pathlib import Path
from typing import Optional

from flask import Blueprint, current_app, jsonify, render_template, request, session
from werkzeug.utils import secure_filename

from .services.analyzer import (
    DatasetStore,
    answer_dataset_question,
    load_dataframe,
    profile_dataframe,
    summary_to_text,
)
from .services.qa import get_qa_engine


main_bp = Blueprint("main", __name__)


@main_bp.before_app_request
def ensure_session_id() -> None:
    """Ensure every visitor has a session identifier for caching uploads."""
    if "session_id" not in session:
        session["session_id"] = secrets.token_hex(16)


@main_bp.get("/")
def index():
    """Render the main chat interface."""
    return render_template("index.html")


@main_bp.post("/chat")
def chat():
    """Placeholder chat endpoint to be implemented with QA pipeline."""
    message = request.json.get("message", "").strip() if request.is_json else ""
    if not message:
        return jsonify({"reply": "Please enter a question to analyze."}), 400

    session_id: Optional[str] = session.get("session_id")
    dataset_context = DatasetStore.get(session_id)
    if dataset_context:
        dataset_reply = answer_dataset_question(message, dataset_context)
        if dataset_reply:
            return jsonify({"reply": dataset_reply, "source": "dataset"})

    qa_engine = get_qa_engine()
    result = qa_engine.answer(message)
    reply = result.answer

    if result.topic:
        reply = f"[{result.topic.replace('_', ' ').title()}]\n{reply}"

    return jsonify({"reply": reply, "confidence": result.confidence})


@main_bp.post("/upload")
def upload():
    """Placeholder upload endpoint for dataset ingestion."""
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "Select a CSV or Excel file to upload."}), 400

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid file name."}), 400

    filepath = upload_dir / filename
    file.save(filepath)

    try:
        dataframe = load_dataframe(filepath)
    except ValueError as exc:
        filepath.unlink(missing_ok=True)
        return jsonify({"error": str(exc)}), 400
    except Exception:
        filepath.unlink(missing_ok=True)
        return jsonify({"error": "Unable to read the uploaded file."}), 400

    profile = profile_dataframe(dataframe)
    DatasetStore.set(session.get("session_id"), dataframe, profile)
    summary_text = summary_to_text(profile)

    return jsonify(
        {
            "message": "File uploaded successfully.",
            "filename": filename,
            "summary": summary_text,
        }
    )

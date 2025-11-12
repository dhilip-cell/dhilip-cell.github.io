import os
from pathlib import Path

from flask import Flask


def create_app() -> Flask:
    """Application factory for the analyst chatbot."""
    app = Flask(__name__, static_folder="static", template_folder="templates")

    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        UPLOAD_FOLDER=str(uploads_dir),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB upload limit
        SESSION_TYPE="filesystem",
    )

    from .routes import main_bp

    app.register_blueprint(main_bp)

    return app

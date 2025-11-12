# Analyst Copilot (Offline)

A lightweight analytics assistant that runs entirely locally. It combines a curated knowledge base with classic machine learning (TF-IDF + cosine similarity) and can analyze user-supplied CSV or Excel files.

## Features

- Web chat interface powered by Flask; no external APIs.
- Built-in knowledge base for Google Sheets, Excel, Power BI, Tableau, SQL, SPSS, and core analytics concepts.
- Upload CSV/Excel files for quick profiling (column types, descriptive stats, aggregations).
- TF-IDF similarity search to surface relevant knowledge base entries.
- Modular Python services for expanding rules or analytics logic.

## Requirements

- Python 3.10+
- Recommended: virtual environment (python -m venv .venv)

## Setup

`ash
# from project root
python -m venv .venv
.venv\Scripts\activate  # PowerShell
pip install -r requirements.txt
`

## Run

`ash
flask --app app.py run
`

Open http://127.0.0.1:5000 in your browser.

## Project Structure

- pp/
  - __init__.py – Flask app factory
  - outes.py – endpoints for chat and dataset uploads
  - services/ – NLP & analysis utilities (qa.py, nalyzer.py)
  - 	emplates/index.html – chat UI
  - static/css/styles.css – page styles
  - static/js/chat.js – front-end chat logic
- data/knowledge_base.json – curated knowledge entries
- uploads/ – runtime upload directory (ignored in VCS)
- equirements.txt – Python dependencies
- pp.py – entry point for running the app

## Create ZIP Package

`powershell
Compress-Archive -Path * -DestinationPath analyst-copilot.zip
`

Upload the generated ZIP to GitHub or share directly.

## Next Steps

- Implement TF-IDF retrieval and rule-engine in pp/services/qa.py.
- Build dataset analyzer utilities in pp/services/analyzer.py.
- Expand UI with conversation history persistence.

"""Веб-интерфейс агента: python -m web.app  →  http://localhost:5000"""
import sys
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from docagent.agent import make_agent  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "workspace"
INPUT, OUTPUT = ROOT / "input", ROOT / "output"
INPUT.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
_agent = None


def agent() -> DocAgent:
    global _agent
    if _agent is None:
        _agent = make_agent(str(ROOT), verbose=False)
    return _agent


def listing(d: Path):
    return sorted(f.name for f in d.iterdir() if f.is_file() and not f.name.startswith("."))


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/files")
def files():
    return jsonify(input=listing(INPUT), output=listing(OUTPUT))


@app.post("/api/upload")
def upload():
    for f in request.files.getlist("files"):
        name = Path(f.filename or "").name.strip()
        if name and not name.startswith("."):
            f.save(INPUT / name)
    return files()


@app.post("/api/chat")
def chat():
    text = (request.json or {}).get("message", "").strip()
    if not text:
        return jsonify(error="Пустое сообщение"), 400
    try:
        reply = agent().ask(text)
    except Exception as e:
        msg = str(e)
        if "api_key" in msg.lower() or "authentication" in msg.lower() or "api key" in msg.lower():
            msg = "Не задан или неверен ключ API. См. раздел «Модели и ключи» в README."
        return jsonify(error=msg), 500
    return jsonify(reply=reply, **files().json)


@app.post("/api/reset")
def reset():
    global _agent
    _agent = None
    return jsonify(ok=True)


@app.get("/download/<path:name>")
def download(name):
    return send_from_directory(OUTPUT, name, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

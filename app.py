#!/usr/bin/env python3
"""
Flask web app that hosts Tucker (local-only, no API keys).
Run: python app.py
Open: http://127.0.0.1:5000 in your browser (Chrome recommended)
"""
from flask import Flask, render_template, request, jsonify, make_response
import uuid
from pathlib import Path
from tucker_core import process_input, log_turn
import json

app = Flask(__name__, static_folder="static", template_folder="templates")

LOG_FILE = Path("tucker_conversation.jsonl")

def get_session_id():
    sid = request.cookies.get("tucker_sid")
    if not sid:
        sid = str(uuid.uuid4())
    return sid

@app.route("/")
def index():
    sid = get_session_id()
    resp = make_response(render_template("index.html"))
    resp.set_cookie("tucker_sid", sid)
    return resp

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = get_session_id()
    reply = process_input(message, session_id=session_id)
    # Log the turn with session id
    log_turn(message, reply, session_id=session_id, log_file=LOG_FILE)
    return jsonify({"reply": reply})

@app.route("/api/history", methods=["GET"])
def api_history():
    # Return last 200 lines for the current session (best-effort)
    session_id = get_session_id()
    res = []
    try:
        if LOG_FILE.exists():
            with LOG_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("session_id") == session_id:
                            res.append(entry)
                    except Exception:
                        continue
    except Exception:
        pass
    return jsonify({"history": res})

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)

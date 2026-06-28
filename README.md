Tucker Web — local chatbot with a Chrome-ready UI
===============================================

What this is
- A tiny local web app that runs Tucker (rule-based chatbot) and serves a simple single-page UI you can open in Chrome. No API keys or external services.

Files
- app.py — Flask server that serves the UI and chat API.
- tucker_core.py — Tucker's logic with persistent memory and logging.
- templates/index.html — the web UI.
- static/style.css, static/app.js — UI styling and JS.
- requirements.txt — dependency list.
- tucker_conversation.jsonl — created when you chat (server-side log).
- tucker_memory.db — SQLite database created automatically for persistent memory.

Run locally (development)
1. Save the files above in a folder (example: tucker-web) preserving the paths (templates/ and static/).
2. Create and activate a Python virtualenv (optional but recommended):
   - python -m venv venv
   - source venv/bin/activate    (Linux/macOS) or venv\\Scripts\\activate (Windows)
3. Install:
   - pip install -r requirements.txt
4. Run for local development:
   - HOST=127.0.0.1 PORT=5000 python app.py
5. Open Chrome to: http://127.0.0.1:5000

Run in production (example)
- Start with gunicorn:
  - gunicorn app:app --bind 0.0.0.0:8000
- Or use the provided Procfile with a platform that supports it (Heroku-style):
  - web: gunicorn app:app --bind 0.0.0.0:$PORT

Notes & next steps
- Memory is persistent: facts you store with "remember X is Y" are saved in tucker_memory.db and survive restarts.
- Conversation is appended to tucker_conversation.jsonl for later reference.
- If you want:
  - Create a pull request and merge the tucker-web branch into main (I can do that for you).
  - Add user authentication or rooms.
  - Improve the assistant answers further with a local LLM (no external API keys required) — I can guide you.

Enjoy — open Chrome and have a chat with Tucker!

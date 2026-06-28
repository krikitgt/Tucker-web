Tucker Web — local chatbot with a Chrome-ready UI
===============================================

What this is
- A tiny local web app that runs Tucker (rule-based chatbot) and serves a simple single-page UI you can open in Chrome. No API keys or external services.

Files
- app.py — Flask server that serves the UI and chat API.
- tucker_core.py — Tucker's logic and memory/log helpers.
- templates/index.html — the web UI.
- static/style.css, static/app.js — UI styling and JS.
- requirements.txt — dependency list.
- tucker_conversation.jsonl — created when you chat (server-side log).

Run locally
1. Save the files above in a folder (example: tucker-web) preserving the paths (templates/ and static/).
2. Create and activate a Python virtualenv (optional but recommended):
   - python -m venv venv
   - source venv/bin/activate    (Linux/macOS) or venv\\Scripts\\activate (Windows)
3. Install:
   - pip install -r requirements.txt
4. Run:
   - python app.py
5. Open Chrome to: http://127.0.0.1:5000

Notes & next steps
- Memory is ephemeral for each browser session and stored on the server process while it runs.
- Conversation is appended to tucker_conversation.jsonl for later reference.
- If you want:
  - I can push this into an existing GitHub repo — give me the owner/repo.
  - Add persistent storage for memory (SQLite or JSON file).
  - Add a better UI, avatars, or themes.
  - Add authentication or multiple rooms.

Enjoy — open Chrome and have a chat with Tucker!

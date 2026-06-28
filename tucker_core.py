#!/usr/bin/env python3
"""
Tucker core logic with persistent memory (SQLite) and improved response handling.
This file replaces the previous in-memory-only memory with a simple SQLite-backed store
and includes a small FAQ and improved question handling for better responses.
"""
import re
import ast
import operator
import random
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("tucker_memory.db")

# Initialize DB
def _init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY(session_id, key)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

_init_db()

# ---- Jokes ----
JOKES = [
    "Why did the programmer quit his job? Because he didn't get arrays.",
    "I would tell you a UDP joke, but you might not get it.",
    "Why do Java programmers have to wear glasses? Because they don't C#.",
    "I told my computer I needed a break, and it said 'No problem — I'll go to sleep.'"
]

# ---- Simple FAQ / knowledge base ----
FAQ = {
    "what is your name": "I'm Tucker, a small local chatbot running on this server.",
    "who made you": "You did — or at least you created the project where I run.",
    "what can you do": "I can do basic math, tell jokes, remember short facts for you, and have small conversations.",
    "how do i run this": "Run `python app.py` and open the web UI in your browser at http://127.0.0.1:5000.",
}

# ---- Safe arithmetic evaluation using AST ----
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval(expr: str):
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise ValueError("Syntax error in expression.")
    return _eval_node(node.body)


def _eval_node(node):
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError("Operator not allowed.")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return ALLOWED_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError("Unary operator not allowed.")
        operand = _eval_node(node.operand)
        return ALLOWED_OPERATORS[op_type](operand)
    elif isinstance(node, ast.Num):  # py <3.8
        return node.n
    elif isinstance(node, ast.Constant):  # py 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed.")
    else:
        raise ValueError("Unsupported expression element.")

# ---- Memory helpers (SQLite-backed) ----

def store_memory(session_id, key, value):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "REPLACE INTO memories(session_id, key, value) VALUES (?, ?, ?)",
            (session_id, key.lower(), value),
        )
        conn.commit()
    finally:
        conn.close()


def recall_memory(session_id, key):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT value FROM memories WHERE session_id = ? AND key = ?",
            (session_id, key.lower()),
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

# ---- Logging ----
LOG_FILE = Path("tucker_conversation.jsonl")

def log_turn(user_text, bot_text, session_id=None, log_file: Path = LOG_FILE):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "user": user_text,
        "tucker": bot_text,
    }
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ---- Better response processing ----

def _clean_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s\?]", " ", text.lower()).strip()


def _match_faq(text: str):
    t = _clean_text(text)
    for q, a in FAQ.items():
        if q in t:
            return a
    return None


def _is_math_expression(text: str) -> bool:
    return bool(re.fullmatch(r"[\d\s\.\+\-\*\/\%\^\(\)]+", text.strip()))


def _try_answer_question(text: str, session_id: str):
    # 1) FAQ
    faq = _match_faq(text)
    if faq:
        return faq

    # 2) Memory recall: "what is my X" patterns
    m = re.match(r"what(?:'s| is)? my (?P<k>[\w\s]+)\??$", text.strip(), re.I)
    if m:
        val = recall_memory(session_id, m.group("k").strip())
        if val:
            return f"Your {m.group('k').strip()} is '{val}'."
        else:
            return f"I don't have anything stored for '{m.group('k').strip()}'. You can say 'remember {m.group('k').strip()} is ...'."

    # 3) Simple heuristics for 'how to' or 'how do i'
    if re.search(r"\bhow (do i|to)\b", text.lower()):
        return (
            "If you tell me the exact task, I can give step-by-step advice. For many tasks, a good approach is:\n"
            "1) define the goal, 2) break it into small steps, 3) try one step and observe results, 4) iterate."
        )

    # 4) Fallback polite answer
    return None


def process_input(text: str, session_id: str = "default"):
    text_clean = (text or "").strip()
    if not text_clean:
        return "You said nothing — try typing something."

    low = text_clean.lower()

    # Simple commands
    if low in ("quit", "exit", "bye", "goodbye", "q"):
        return "Goodbye — Tucker signing off."

    if low in ("help", "commands", "h"):
        return (
            "I am Tucker. Try:\n"
            "- say 'hello' or 'hi'\n"
            "- ask 'what time is it' or 'date'\n"
            "- 'calculate 2+2' or just give a math expression\n"
            "- 'remember X is Y' to store a fact for this session\n"
            "- 'what is my X' to recall a fact\n"
            "- 'joke' for a joke\n"
            "- 'save' to save conversation to file (server-side)"
        )

    # Greeting
    if re.search(r"\b(hello|hi|hey|greetings|yo)\b", low):
        return random.choice(["Hi, I'm Tucker. How can I help?", "Hello — Tucker here! What's up?", "Hey! What would you like to do today?"])

    if re.search(r"\b(how are you|how's it going|how do you do)\b", low):
        return random.choice(["I'm a program, so I'm always okay. How are you?", "Doing fine! Ready to chat."])

    if "joke" in low:
        return random.choice(JOKES)

    if "time" in low:
        return "Current time (local): " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "date" in low:
        return "Today's date: " + datetime.now().strftime("%Y-%m-%d")

    if low == "save":
        return "Conversation is logged to the server file."

    # Remember patterns
    m = re.match(r"remember(?: that)? (?P<k>[\w\s]+?) (?:is|=|:)\s*(?P<v>.+)$", text_clean, re.I)
    if m:
        key = m.group("k").strip()
        val = m.group("v").strip()
        store_memory(session_id, key, val)
        return f"I'll remember that your {key} is '{val}'."

    # Calculation commands
    m = re.match(r"^(?:calculate|calc)\s+(?P<expr>.+)$", text_clean, re.I)
    if m:
        expr = m.group("expr").replace("^", "**")
        try:
            result = safe_eval(expr)
            return f"{expr} = {result}"
        except Exception as e:
            return f"Couldn't calculate that: {e}"

    # Bare math expression
    if _is_math_expression(text_clean):
        expr = text_clean.replace("^", "**")
        try:
            result = safe_eval(expr)
            return f"{expr} = {result}"
        except Exception as e:
            return f"Couldn't evaluate expression: {e}"

    # If it's a question, try to answer more intelligently
    if "?" in text_clean or text_clean.endswith("how") or text_clean.lower().startswith("how"):
        ans = _try_answer_question(text_clean, session_id)
        if ans:
            return ans
        else:
            # Try a more helpful fallback
            return (
                "That's an interesting question. I might not know everything, but I can try to help. "
                "Try asking in a bit more detail or tell me the context, and I'll provide step-by-step guidance."
            )

    # Generic small-talk improvements
    replies = [
        "Tell me more — the more details, the better I can help.",
        "I see. What specifically would you like me to do with that information?",
        "Okay — I can remember that if you say 'remember ... is ...', or I can help with calculations and simple instructions.",
    ]
    return random.choice(replies)

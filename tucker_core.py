#!/usr/bin/env python3
"""
Tucker core logic refactored for use by the Flask app.
Provides:
- process_input(message, session_id=...) -> reply
- safe math evaluation
- per-session ephemeral memory
- logging helper log_turn(...)
"""
import re
import ast
import operator
import random
import json
from datetime import datetime
from pathlib import Path

# In-memory per-session memory: { session_id: { key: value } }
_session_memory = {}

# ---- Jokes ----
JOKES = [
    "Why did the programmer quit his job? Because he didn't get arrays.",
    "I would tell you a UDP joke, but you might not get it.",
    "Why do Java programmers have to wear glasses? Because they don't C#.",
    "I told my computer I needed a break, and it said 'No problem — I'll go to sleep.'"
]

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

# ---- Memory helpers ----
def _get_store(session_id):
    if session_id not in _session_memory:
        _session_memory[session_id] = {}
    return _session_memory[session_id]

def store_memory(session_id, key, value):
    store = _get_store(session_id)
    store[key.lower()] = value

def recall_memory(session_id, key):
    store = _get_store(session_id)
    return store.get(key.lower())

# ---- Logging ----
def log_turn(user_text, bot_text, session_id=None, log_file: Path = Path("tucker_conversation.jsonl")):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "user": user_text,
        "tucker": bot_text
    }
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ---- Main processing ----
def process_input(text: str, session_id: str = "default"):
    text_clean = (text or "").strip()
    if not text_clean:
        return "You said nothing — try typing something."

    low = text_clean.lower()

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

    if re.search(r"\b(hello|hi|hey|greetings|yo)\b", low):
        return random.choice(["Hi, I'm Tucker. How can I help?", "Hello — Tucker here! What's up?"])

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

    # Recall
    m = re.match(r"what(?:'s| is)? my (?P<k>[\w\s]+)\??$", text_clean, re.I)
    if m:
        key = m.group("k").strip()
        val = recall_memory(session_id, key)
        if val:
            return f"Your {key} is '{val}'."
        else:
            return f"I don't have anything stored for '{key}'. You can say 'remember {key} is ...'."

    # Calculate
    m = re.match(r"^(?:calculate|calc)\s+(?P<expr>.+)$", text_clean, re.I)
    if m:
        expr = m.group("expr").replace("^", "**")
        try:
            result = safe_eval(expr)
            return f"{expr} = {result}"
        except Exception as e:
            return f"Couldn't calculate that: {e}"

    # Bare expression detection
    if re.fullmatch(r"[\d\s\.\+\-\*\/\%\^\(\)]+", text_clean):
        expr = text_clean.replace("^", "**")
        try:
            result = safe_eval(expr)
            return f"{expr} = {result}"
        except Exception as e:
            return f"Couldn't evaluate expression: {e}"

    if "?" in text_clean:
        return "That's an interesting question. I don't know everything, but I can help with basic math, remembering facts, and small talk."

    replies = [
        "Tell me more.",
        "I see. What else?",
        "Okay — and what would you like me to do with that?",
        "Thanks for telling me. I can remember short facts if you say 'remember ... is ...'."
    ]
    return random.choice(replies)

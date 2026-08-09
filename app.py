from datetime import datetime, timezone
import re
import sqlite3
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB = "mental_health.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mood TEXT NOT NULL,
        note TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def chatbot(message):
    text = re.sub(r"\s+", " ", message.lower()).strip()

    if not text:
        return "Tell me a little about how you're feeling."

    if any(k in text for k in ["suicide", "kill myself", "end my life", "self harm", "hurt myself"]):
        return (
            "I'm really sorry you're dealing with something this heavy. "
            "I can't provide emergency or clinical support. Please contact local emergency "
            "services or a trusted person who can stay with you, and seek professional help now."
        )

    intents = {
        "greeting": (["hello", "hi", "hey"], "Hi. I'm here to listen. How are you feeling today?"),
        "sad": (["sad", "down", "unhappy", "lonely", "cry"], "That sounds difficult. If you can, try putting the feeling into words and consider talking to someone you trust."),
        "stress": (["stress", "stressed", "pressure", "overwhelmed"], "When things feel overwhelming, try breaking the next task into one small step and taking a short pause."),
        "anxiety": (["anxious", "anxiety", "worried", "panic", "nervous"], "Try a slow breathing exercise and focus on one thing you can control right now."),
        "happy": (["happy", "good", "great", "excited"], "I'm glad to hear that. What has been going well?"),
        "sleep": (["sleep", "insomnia", "tired"], "A consistent sleep routine and reducing screen time before bed can be useful. If sleep problems persist, consider speaking with a professional."),
    }

    for _, (keywords, response) in intents.items():
        if any(k in text for k in keywords):
            return response

    return (
        "Thanks for sharing that. I can help you reflect on what you're feeling, "
        "but I'm not a substitute for a mental-health professional."
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/moods")
def moods():
    conn = get_db()
    rows = conn.execute("SELECT * FROM moods ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/moods")
def add_mood():
    data = request.get_json(silent=True) or {}
    mood = str(data.get("mood", "")).strip()
    note = str(data.get("note", "")).strip()[:500]

    if mood not in {"Happy", "Okay", "Sad", "Anxious", "Stressed", "Angry"}:
        return jsonify({"error": "Invalid mood"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO moods (mood, note, created_at) VALUES (?, ?, ?)",
        (mood, note, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Mood saved"}), 201

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", ""))[:1000]
    return jsonify({"reply": chatbot(message)})

@app.get("/api/posts")
def posts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/posts")
def add_post():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()[:500]
    if len(text) < 3:
        return jsonify({"error": "Post is too short"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO posts (text, created_at) VALUES (?, ?)",
        (text, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Post created"}), 201

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

import os, sqlite3, secrets, string
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, session, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "CHANGE_THIS_LONG_RANDOM_SECRET")
DB_PATH = os.environ.get("DB_PATH", "vip_bot.db")
ADMIN_PASSWORD = os.environ.get("WEB_ADMIN_PASSWORD", "")
CHANNEL = os.environ.get("CHANNEL_USERNAME", "@Dark_Alamin_Vai")

def now():
    return datetime.now(timezone.utc)

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS keys (
          code TEXT PRIMARY KEY, days INTEGER NOT NULL, created_by INTEGER NOT NULL,
          created_at TEXT NOT NULL, used_by INTEGER, used_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
          user_id INTEGER PRIMARY KEY, username TEXT, expires_at TEXT NOT NULL,
          activated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS web_users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, session_token TEXT UNIQUE,
          expires_at TEXT NOT NULL, created_at TEXT NOT NULL)""")

def make_key():
    alphabet = string.ascii_uppercase + string.digits
    raw = ''.join(secrets.choice(alphabet) for _ in range(12))
    return "DARK-" + "-".join(raw[i:i+4] for i in range(0, 12, 4))

def web_admin(f):
    @wraps(f)
    def inner(*a, **kw):
        if not session.get("is_admin"):
            return jsonify({"ok": False, "error": "Admin login required"}), 401
        return f(*a, **kw)
    return inner

@app.get("/")
def home():
    return render_template("index.html", channel=CHANNEL)

@app.post("/api/login")
def login():
    code = (request.json or {}).get("key", "").strip().upper()
    if not code:
        return jsonify(ok=False, error="VIP Key লিখুন"), 400
    with db() as c:
        row = c.execute("SELECT * FROM keys WHERE code=?", (code,)).fetchone()
        if not row:
            return jsonify(ok=False, error="Key সঠিক নয়"), 401
        if row["used_by"] is not None:
            return jsonify(ok=False, error="এই Key আগে ব্যবহার হয়েছে"), 409
        expiry = now() + timedelta(days=int(row["days"]))
        token = secrets.token_urlsafe(32)
        c.execute("UPDATE keys SET used_by=?, used_at=? WHERE code=? AND used_by IS NULL",
                  (-1, now().isoformat(), code))
        c.execute("INSERT INTO web_users(session_token,expires_at,created_at) VALUES(?,?,?)",
                  (token, expiry.isoformat(), now().isoformat()))
    session["vip_token"] = token
    return jsonify(ok=True, expires=expiry.strftime("%Y-%m-%d %H:%M UTC"))

@app.get("/api/me")
def me():
    token = session.get("vip_token")
    if not token:
        return jsonify(ok=False), 401
    with db() as c:
        row = c.execute("SELECT expires_at FROM web_users WHERE session_token=?", (token,)).fetchone()
    if not row or datetime.fromisoformat(row["expires_at"]) <= now():
        session.pop("vip_token", None)
        return jsonify(ok=False), 401
    return jsonify(ok=True, expires=datetime.fromisoformat(row["expires_at"]).strftime("%Y-%m-%d %H:%M UTC"))

@app.post("/api/logout")
def logout():
    session.pop("vip_token", None)
    return jsonify(ok=True)

@app.post("/api/admin/login")
def admin_login():
    if not ADMIN_PASSWORD:
        return jsonify(ok=False, error="Server admin password is not configured"), 503
    password = (request.json or {}).get("password", "")
    if secrets.compare_digest(password, ADMIN_PASSWORD):
        session["is_admin"] = True
        return jsonify(ok=True)
    return jsonify(ok=False, error="পাসওয়ার্ড সঠিক নয়"), 401

@app.post("/api/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return jsonify(ok=True)

@app.get("/api/admin/stats")
@web_admin
def admin_stats():
    with db() as c:
        total_keys = c.execute("SELECT COUNT(*) n FROM keys").fetchone()["n"]
        unused = c.execute("SELECT COUNT(*) n FROM keys WHERE used_by IS NULL").fetchone()["n"]
        bot_users = c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        web_users = c.execute("SELECT COUNT(*) n FROM web_users WHERE expires_at > ?", (now().isoformat(),)).fetchone()["n"]
        recent = c.execute("SELECT code,days,used_by,created_at FROM keys ORDER BY created_at DESC LIMIT 25").fetchall()
    return jsonify(ok=True, total_keys=total_keys, unused=unused, bot_users=bot_users,
                   web_vips=web_users, keys=[dict(r) for r in recent])

@app.post("/api/admin/generate")
@web_admin
def generate():
    data = request.json or {}
    try: days = int(data.get("days", 30))
    except (TypeError, ValueError): days = 0
    if not 1 <= days <= 3650:
        return jsonify(ok=False, error="দিন ১ থেকে ৩৬৫০-এর মধ্যে দিন"), 400
    code = make_key()
    with db() as c:
        c.execute("INSERT INTO keys(code,days,created_by,created_at) VALUES(?,?,?,?)",
                  (code, days, 0, now().isoformat()))
    return jsonify(ok=True, key=code, days=days)

@app.post("/api/admin/revoke")
@web_admin
def revoke():
    data = request.json or {}
    kind, value = data.get("kind"), data.get("value", "").strip()
    if kind == "key":
        with db() as c: cur = c.execute("DELETE FROM keys WHERE code=?", (value.upper(),))
    elif kind == "web":
        with db() as c: cur = c.execute("DELETE FROM web_users WHERE session_token=?", (value,))
    else:
        return jsonify(ok=False, error="kind must be key or web"), 400
    return jsonify(ok=bool(cur.rowcount))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

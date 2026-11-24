import os, sqlite3, secrets, string
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DB_PATH = os.environ.get("DB_PATH", "vip_bot.db")
CHANNEL = os.environ.get("CHANNEL_USERNAME", "@Dark_Alamin_Vai")

def now(): return datetime.now(timezone.utc)
def db():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS keys(code TEXT PRIMARY KEY,days INTEGER NOT NULL,created_by INTEGER NOT NULL,created_at TEXT NOT NULL,used_by INTEGER,used_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,expires_at TEXT NOT NULL,activated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS web_users(id INTEGER PRIMARY KEY AUTOINCREMENT,session_token TEXT UNIQUE,expires_at TEXT NOT NULL,created_at TEXT NOT NULL)""")
def admin(uid): return uid in ADMIN_IDS
def keygen():
    s=''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(12))
    return "DARK-"+"-".join(s[i:i+4] for i in range(0,12,4))
async def start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(f"🌙 DARK ALAMIN VIP\\n\\nVIP Key পেতে অ্যাডমিনের সাথে যোগাযোগ করুন।\\nWebsite/Channel: {CHANNEL}\\nKey থাকলে এখানে পাঠান।")
async def panel(u,ctx):
    if not admin(u.effective_user.id): return await u.message.reply_text("⛔ Access denied")
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Generate 30-day Key",callback_data="gen")],[InlineKeyboardButton("Statistics",callback_data="stats")]])
    await u.message.reply_text("🛠 DARK ALAMIN ADMIN PANEL",reply_markup=kb)
async def gen(u,ctx):
    if not admin(u.effective_user.id): return await u.message.reply_text("⛔ Access denied")
    try: days=int(ctx.args[0]) if ctx.args else 30
    except ValueError: days=0
    if not 1<=days<=3650: return await u.message.reply_text("ব্যবহার: /genkey 30")
    code=keygen()
    with db() as c: c.execute("INSERT INTO keys VALUES(?,?,?,?,NULL,NULL)",(code,days,u.effective_user.id,now().isoformat()))
    await u.message.reply_text(f"নতুন VIP Key: {code}\\nমেয়াদ: {days} দিন")
async def stats(u,ctx):
    if not admin(u.effective_user.id): return await u.message.reply_text("⛔ Access denied")
    with db() as c:
        k=c.execute("SELECT COUNT(*) n FROM keys").fetchone()["n"]
        free=c.execute("SELECT COUNT(*) n FROM keys WHERE used_by IS NULL").fetchone()["n"]
        users=c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
    await u.message.reply_text(f"📊 মোট Key: {k}\\nঅব্যবহৃত: {free}\\nBot VIP users: {users}")
async def on_callback(u,ctx):
    q=u.callback_query; await q.answer()
    if not admin(q.from_user.id): return await q.edit_message_text("⛔ Access denied")
    if q.data=="gen": await q.edit_message_text("৩০ দিনের Key: /genkey 30")
    elif q.data=="stats":
        with db() as c:
            k=c.execute("SELECT COUNT(*) n FROM keys").fetchone()["n"]
            free=c.execute("SELECT COUNT(*) n FROM keys WHERE used_by IS NULL").fetchone()["n"]
            users=c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        await q.edit_message_text(f"মোট Key: {k}\\nঅব্যবহৃত: {free}\\nVIP users: {users}")
async def redeem(u,ctx):
    user=u.effective_user; code=u.message.text.strip().upper()
    with db() as c:
        row=c.execute("SELECT * FROM keys WHERE code=?",(code,)).fetchone()
        if not row: return await u.message.reply_text("❌ Key পাওয়া যায়নি।")
        if row["used_by"] is not None: return await u.message.reply_text("❌ Key আগে ব্যবহার হয়েছে।")
        exp=now()+timedelta(days=row["days"])
        c.execute("UPDATE keys SET used_by=?,used_at=? WHERE code=? AND used_by IS NULL",(user.id,now().isoformat(),code))
        c.execute("""INSERT INTO users VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,expires_at=excluded.expires_at,activated_at=excluded.activated_at""",(user.id,user.username or "",exp.isoformat(),now().isoformat()))
    await u.message.reply_text(f"✅ VIP চালু হয়েছে!\\nমেয়াদ: {row['days']} দিন\\nশেষ: {exp.strftime('%Y-%m-%d %H:%M UTC')}")
def main():
    init(); app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("admin",panel))
    app.add_handler(CommandHandler("genkey",gen)); app.add_handler(CommandHandler("stats",stats))
    app.add_handler(CallbackQueryHandler(on_callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,redeem))
    print("DARK ALAMIN bot started"); app.run_polling()
if __name__=="__main__": main()

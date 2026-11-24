# DARK ALAMIN — Website + Telegram VIP Bot

এই প্রজেক্টে VIP Key login website এবং Telegram bot আছে। দুইটিই একই SQLite database (`vip_bot.db`) ব্যবহার করে। Website থেকে তৈরি করা key Telegram bot-এ এবং bot থেকে তৈরি করা key website-এ redeem করা যায়।

## চালানোর আগে
- Python 3.10 বা নতুন সংস্করণ
- BotFather থেকে Telegram bot token
- নিজের numeric Telegram user ID
- শক্তিশালী web admin password এবং Flask secret

## ইনস্টল
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Environment variables সেট করুন
`.env.example`-এর মান কপি করে নিজের hosting provider-এর Environment Variables-এ বসান। `.env` ফাইল ব্যবহার করলে `python-dotenv` যোগ করে load করতে হবে; সহজভাবে shell-এ export করা যায়।

Linux/macOS:
```bash
export BOT_TOKEN="BOTFATHER_TOKEN"
export ADMIN_IDS="YOUR_NUMERIC_TELEGRAM_ID"
export WEB_ADMIN_PASSWORD="A_LONG_UNIQUE_PASSWORD"
export FLASK_SECRET="A_LONG_RANDOM_SECRET"
export CHANNEL_USERNAME="@Dark_Alamin_Vai"
export DB_PATH="vip_bot.db"
```

Windows PowerShell:
```powershell
$env:BOT_TOKEN="BOTFATHER_TOKEN"
$env:ADMIN_IDS="YOUR_NUMERIC_TELEGRAM_ID"
$env:WEB_ADMIN_PASSWORD="A_LONG_UNIQUE_PASSWORD"
$env:FLASK_SECRET="A_LONG_RANDOM_SECRET"
$env:CHANNEL_USERNAME="@Dark_Alamin_Vai"
$env:DB_PATH="vip_bot.db"
```

## দুটি process চালান
Terminal 1:
```bash
python app.py
```
Website: `http://localhost:5000`

Terminal 2:
```bash
python bot.py
```

Production hosting-এ Flask-এর জন্য:
```bash
gunicorn -w 1 -b 0.0.0.0:$PORT app:app
```
Telegram bot আলাদা worker/service হিসেবে `python bot.py` চালান। দুটো process-কে একই persistent disk/database path দিতে হবে। SQLite file shared network filesystem-এ না রাখাই ভালো; single server persistent disk ব্যবহার করুন।

## Admin
- Website admin panel: `WEB_ADMIN_PASSWORD`
- Telegram admin: `ADMIN_IDS`-এ numeric user ID
- Bot commands: `/admin`, `/genkey 30`, `/stats`

## নিরাপত্তা ও সীমাবদ্ধতা
- HTTPS-সহ hosting ব্যবহার করুন।
- Bot token, admin password, Flask secret কখনো public করবেন না।
- Database file নিয়মিত backup করুন।
- Website-এ redeem করা key-ও একবার ব্যবহারযোগ্য; bot user এবং website session আলাদা ধরনের access record রাখে।
- Website admin panel-এর বর্তমান সংস্করণে key generate ও statistics আছে; key delete/revoke API আছে কিন্তু UI-তে revoke control নেই।
- Channel join বাধ্যতামূলক যাচাই এই সংস্করণে নেই। চাইলে পরের ধাপে যোগ করা যাবে।
- এটি বৈধ VIP সদস্যপদ/কনটেন্ট অ্যাক্সেসের জন্য; অন্যের অ্যাকাউন্টে অননুমোদিত প্রবেশের জন্য নয়।

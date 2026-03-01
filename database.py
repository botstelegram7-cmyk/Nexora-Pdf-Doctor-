"""
Database layer — SQLite by default, MongoDB if MONGODB_URL is set.
"""
import sqlite3, os, datetime
from config import MONGODB_URL

# ── MongoDB ──────────────────────────────────────────────────────────────────
_mongo_db = None
if MONGODB_URL:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _mongo_client = AsyncIOMotorClient(MONGODB_URL)
        _mongo_db = _mongo_client["pdf_doctor"]
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"⚠️ MongoDB failed: {e}, falling back to SQLite")
        _mongo_db = None

# ── SQLite ────────────────────────────────────────────────────────────────────
_SQLITE_PATH = "data/pdf_doctor.db"
os.makedirs("data", exist_ok=True)

def _get_conn():
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite():
    with _get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            name        TEXT,
            username    TEXT,
            joined_at   TEXT,
            plan        TEXT DEFAULT 'free',
            plan_expiry TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_usage (
            user_id INTEGER,
            date    TEXT,
            count   INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        );
        CREATE TABLE IF NOT EXISTS payment_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            plan        TEXT,
            screenshot_file_id TEXT,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT
        );
        """)

init_sqlite()

# ── Helpers ───────────────────────────────────────────────────────────────────

async def ensure_user(user_id: int, name: str, username: str):
    if _mongo_db:
        await _mongo_db.users.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"user_id": user_id, "name": name, "username": username,
                              "joined_at": _now(), "plan": "free", "plan_expiry": None}},
            upsert=True
        )
    else:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)",
                (user_id, name, username, _now(), "free", None)
            )

async def get_user(user_id: int) -> dict | None:
    if _mongo_db:
        doc = await _mongo_db.users.find_one({"user_id": user_id})
        return doc
    else:
        with _get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
            return dict(row) if row else None

async def set_premium(user_id: int, plan: str, expiry: datetime.datetime):
    expiry_str = expiry.isoformat()
    if _mongo_db:
        await _mongo_db.users.update_one(
            {"user_id": user_id},
            {"$set": {"plan": plan, "plan_expiry": expiry_str}},
            upsert=True
        )
    else:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE users SET plan=?, plan_expiry=? WHERE user_id=?",
                (plan, expiry_str, user_id)
            )

async def get_plan(user_id: int) -> str:
    """Returns 'free', 'basic', or 'pro'"""
    user = await get_user(user_id)
    if not user:
        return "free"
    plan = user.get("plan", "free")
    expiry = user.get("plan_expiry")
    if plan != "free" and expiry:
        if datetime.datetime.fromisoformat(expiry) < datetime.datetime.now():
            await _expire_plan(user_id)
            return "free"
    return plan

async def _expire_plan(user_id: int):
    if _mongo_db:
        await _mongo_db.users.update_one({"user_id": user_id}, {"$set": {"plan": "free", "plan_expiry": None}})
    else:
        with _get_conn() as conn:
            conn.execute("UPDATE users SET plan='free', plan_expiry=NULL WHERE user_id=?", (user_id,))

async def get_usage(user_id: int) -> int:
    today = datetime.date.today().isoformat()
    if _mongo_db:
        doc = await _mongo_db.daily_usage.find_one({"user_id": user_id, "date": today})
        return doc["count"] if doc else 0
    else:
        with _get_conn() as conn:
            row = conn.execute("SELECT count FROM daily_usage WHERE user_id=? AND date=?",
                               (user_id, today)).fetchone()
            return row["count"] if row else 0

async def increment_usage(user_id: int):
    today = datetime.date.today().isoformat()
    if _mongo_db:
        await _mongo_db.daily_usage.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {"count": 1}},
            upsert=True
        )
    else:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO daily_usage(user_id,date,count) VALUES(?,?,1) "
                "ON CONFLICT(user_id,date) DO UPDATE SET count=count+1",
                (user_id, today)
            )

async def save_payment_request(user_id: int, plan: str, file_id: str):
    if _mongo_db:
        await _mongo_db.payment_requests.insert_one(
            {"user_id": user_id, "plan": plan, "screenshot_file_id": file_id,
             "status": "pending", "created_at": _now()}
        )
    else:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO payment_requests(user_id,plan,screenshot_file_id,status,created_at) VALUES(?,?,?,?,?)",
                (user_id, plan, file_id, "pending", _now())
            )

async def get_all_users() -> list:
    if _mongo_db:
        return await _mongo_db.users.find({}).to_list(None)
    else:
        with _get_conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]

def _now():
    return datetime.datetime.now().isoformat()

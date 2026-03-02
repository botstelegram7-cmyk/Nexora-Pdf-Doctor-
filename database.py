"""
Database v4 — SQLite (default) or MongoDB.
New: per-feature usage tracking, monthly stats, referrals, dashboard.
"""
import sqlite3, os, datetime
from config import MONGODB_URL

_mongo_db = None
if MONGODB_URL:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _mongo_client = AsyncIOMotorClient(MONGODB_URL)
        _mongo_db = _mongo_client["pdf_doctor"]
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"⚠️ MongoDB failed: {e}, using SQLite")

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
            plan_expiry TEXT,
            referrer_id INTEGER DEFAULT NULL,
            total_ops   INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS daily_usage (
            user_id INTEGER,
            date    TEXT,
            count   INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        );
        CREATE TABLE IF NOT EXISTS feature_usage (
            user_id  INTEGER,
            date     TEXT,
            feature  TEXT,
            count    INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date, feature)
        );
        CREATE TABLE IF NOT EXISTS monthly_stats (
            month    TEXT,
            feature  TEXT,
            count    INTEGER DEFAULT 0,
            PRIMARY KEY (month, feature)
        );
        CREATE TABLE IF NOT EXISTS payment_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            plan        TEXT,
            screenshot_file_id TEXT,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id  INTEGER,
            referred_id  INTEGER,
            created_at   TEXT,
            PRIMARY KEY (referred_id)
        );
        """)

init_sqlite()

def _now():
    return datetime.datetime.now().isoformat()

def _today():
    return datetime.date.today().isoformat()

def _this_month():
    return datetime.date.today().strftime("%Y-%m")


# ── User Management ───────────────────────────────────────────────────────────

async def ensure_user(user_id: int, name: str, username: str, referrer_id: int = None):
    if _mongo_db:
        await _mongo_db.users.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"user_id": user_id, "name": name, "username": username,
                              "joined_at": _now(), "plan": "free", "plan_expiry": None,
                              "referrer_id": referrer_id, "total_ops": 0}},
            upsert=True
        )
        if referrer_id:
            await _mongo_db.referrals.update_one(
                {"referred_id": user_id},
                {"$setOnInsert": {"referrer_id": referrer_id, "referred_id": user_id, "created_at": _now()}},
                upsert=True
            )
    else:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users(user_id,name,username,joined_at,plan,plan_expiry,referrer_id,total_ops) VALUES(?,?,?,?,?,?,?,?)",
                (user_id, name, username, _now(), "free", None, referrer_id, 0)
            )
            if referrer_id:
                conn.execute(
                    "INSERT OR IGNORE INTO referrals(referrer_id,referred_id,created_at) VALUES(?,?,?)",
                    (referrer_id, user_id, _now())
                )

async def get_user(user_id: int) -> dict | None:
    if _mongo_db:
        return await _mongo_db.users.find_one({"user_id": user_id})
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

async def get_plan(user_id: int) -> str:
    user = await get_user(user_id)
    if not user:
        return "free"
    plan   = user.get("plan", "free")
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

async def set_premium(user_id: int, plan: str, expiry: datetime.datetime):
    expiry_str = expiry.isoformat()
    if _mongo_db:
        await _mongo_db.users.update_one(
            {"user_id": user_id},
            {"$set": {"plan": plan, "plan_expiry": expiry_str}}, upsert=True
        )
    else:
        with _get_conn() as conn:
            conn.execute("UPDATE users SET plan=?, plan_expiry=? WHERE user_id=?",
                         (plan, expiry_str, user_id))

async def get_all_users() -> list:
    if _mongo_db:
        return await _mongo_db.users.find({}).to_list(None)
    with _get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]


# ── Usage Tracking ─────────────────────────────────────────────────────────────

async def get_usage(user_id: int) -> int:
    """Total daily usage."""
    today = _today()
    if _mongo_db:
        doc = await _mongo_db.daily_usage.find_one({"user_id": user_id, "date": today})
        return doc["count"] if doc else 0
    with _get_conn() as conn:
        row = conn.execute("SELECT count FROM daily_usage WHERE user_id=? AND date=?",
                           (user_id, today)).fetchone()
        return row["count"] if row else 0

async def get_feature_usage(user_id: int, feature: str) -> int:
    """Per-feature daily usage."""
    today = _today()
    if _mongo_db:
        doc = await _mongo_db.feature_usage.find_one({"user_id": user_id, "date": today, "feature": feature})
        return doc["count"] if doc else 0
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM feature_usage WHERE user_id=? AND date=? AND feature=?",
            (user_id, today, feature)
        ).fetchone()
        return row["count"] if row else 0

async def increment_usage(user_id: int, feature: str = "general"):
    """Increment both total and per-feature usage."""
    today = _today()
    month = _this_month()
    if _mongo_db:
        await _mongo_db.daily_usage.update_one(
            {"user_id": user_id, "date": today}, {"$inc": {"count": 1}}, upsert=True)
        await _mongo_db.feature_usage.update_one(
            {"user_id": user_id, "date": today, "feature": feature}, {"$inc": {"count": 1}}, upsert=True)
        await _mongo_db.monthly_stats.update_one(
            {"month": month, "feature": feature}, {"$inc": {"count": 1}}, upsert=True)
        await _mongo_db.users.update_one({"user_id": user_id}, {"$inc": {"total_ops": 1}})
    else:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO daily_usage(user_id,date,count) VALUES(?,?,1) "
                "ON CONFLICT(user_id,date) DO UPDATE SET count=count+1",
                (user_id, today))
            conn.execute(
                "INSERT INTO feature_usage(user_id,date,feature,count) VALUES(?,?,?,1) "
                "ON CONFLICT(user_id,date,feature) DO UPDATE SET count=count+1",
                (user_id, today, feature))
            conn.execute(
                "INSERT INTO monthly_stats(month,feature,count) VALUES(?,?,1) "
                "ON CONFLICT(month,feature) DO UPDATE SET count=count+1",
                (month, feature))
            conn.execute("UPDATE users SET total_ops=total_ops+1 WHERE user_id=?", (user_id,))

async def check_feature_limit(user_id: int, feature: str) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).
    Checks per-feature limit for user's plan.
    """
    from config import FEATURE_LIMITS
    plan   = await get_plan(user_id)
    limits = FEATURE_LIMITS.get(feature, {"free": 3, "basic": 30, "pro": None})
    limit  = limits.get(plan)

    if limit is None:
        return True, ""   # Unlimited

    if limit == 0:
        plan_needed = "Pro" if limits.get("pro") is None else "Basic"
        return False, f"🔒 <b>{feature.title()}</b> requires <b>{plan_needed} plan</b>!\nUse /premium to upgrade."

    used = await get_feature_usage(user_id, feature)
    if used >= limit:
        return False, (
            f"⚠️ <b>Daily limit reached for {feature.title()}!</b>\n\n"
            f"📊 Used: <b>{used}/{limit}</b> today\n"
            f"🔄 Resets at midnight\n\n"
            f"💎 Upgrade to get more:\n"
            f"  ⭐ Basic: {FEATURE_LIMITS.get(feature, {}).get('basic', '?')} ops/day\n"
            f"  👑 Pro: Unlimited\n\n"
            f"Use /premium to upgrade!"
        )
    return True, ""


# ── Dashboard Stats ────────────────────────────────────────────────────────────

async def get_user_dashboard(user_id: int) -> dict:
    """Get stats for /dashboard command."""
    today = _today()
    month = _this_month()

    if _mongo_db:
        # Today's usage by feature
        today_features = {}
        async for doc in _mongo_db.feature_usage.find({"user_id": user_id, "date": today}):
            today_features[doc["feature"]] = doc["count"]

        # This month's usage
        month_total = 0
        async for doc in _mongo_db.daily_usage.find(
            {"user_id": user_id, "date": {"$gte": month + "-01"}}
        ):
            month_total += doc.get("count", 0)

        user = await get_user(user_id) or {}
        total_ops = user.get("total_ops", 0)

        # Referral count
        ref_count = await _mongo_db.referrals.count_documents({"referrer_id": user_id})
    else:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT feature, count FROM feature_usage WHERE user_id=? AND date=?",
                (user_id, today)
            ).fetchall()
            today_features = {r["feature"]: r["count"] for r in rows}

            month_row = conn.execute(
                "SELECT SUM(count) as total FROM daily_usage WHERE user_id=? AND date LIKE ?",
                (user_id, month + "%")
            ).fetchone()
            month_total = month_row["total"] or 0

            user = await get_user(user_id) or {}
            total_ops = user.get("total_ops", 0)

            ref_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id=?", (user_id,)
            ).fetchone()
            ref_count = ref_row["cnt"] if ref_row else 0

    return {
        "today_features": today_features,
        "month_total":    month_total,
        "total_ops":      total_ops,
        "ref_count":      ref_count,
    }


async def get_admin_stats() -> dict:
    """Full stats for admin panel."""
    today = _today()
    month = _this_month()

    if _mongo_db:
        total_users   = await _mongo_db.users.count_documents({})
        free_users    = await _mongo_db.users.count_documents({"plan": "free"})
        basic_users   = await _mongo_db.users.count_documents({"plan": "basic"})
        pro_users     = await _mongo_db.users.count_documents({"plan": "pro"})
        today_active  = await _mongo_db.daily_usage.count_documents({"date": today})
        today_ops_doc = await _mongo_db.daily_usage.aggregate(
            [{"$match": {"date": today}}, {"$group": {"_id": None, "total": {"$sum": "$count"}}}]
        ).to_list(None)
        today_ops = today_ops_doc[0]["total"] if today_ops_doc else 0

        month_stats_docs = await _mongo_db.monthly_stats.find({"month": month}).to_list(None)
        month_stats = {d["feature"]: d["count"] for d in month_stats_docs}
        pending_payments = await _mongo_db.payment_requests.count_documents({"status": "pending"})
    else:
        with _get_conn() as conn:
            total_users  = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            free_users   = conn.execute("SELECT COUNT(*) as c FROM users WHERE plan='free'").fetchone()["c"]
            basic_users  = conn.execute("SELECT COUNT(*) as c FROM users WHERE plan='basic'").fetchone()["c"]
            pro_users    = conn.execute("SELECT COUNT(*) as c FROM users WHERE plan='pro'").fetchone()["c"]
            today_active = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM daily_usage WHERE date=?", (today,)).fetchone()["c"]
            today_ops    = conn.execute("SELECT SUM(count) as s FROM daily_usage WHERE date=?", (today,)).fetchone()["s"] or 0

            rows = conn.execute("SELECT feature, count FROM monthly_stats WHERE month=?", (month,)).fetchall()
            month_stats = {r["feature"]: r["count"] for r in rows}

            pending_payments = conn.execute(
                "SELECT COUNT(*) as c FROM payment_requests WHERE status='pending'"
            ).fetchone()["c"]

    return {
        "total_users":      total_users,
        "free_users":       free_users,
        "basic_users":      basic_users,
        "pro_users":        pro_users,
        "today_active":     today_active,
        "today_ops":        today_ops,
        "month_stats":      month_stats,
        "pending_payments": pending_payments,
        "today":            today,
        "month":            month,
    }


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

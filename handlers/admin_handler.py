"""
Admin Panel v4 — Beautiful web dashboard served at /admin
Access: http://yourserver.com/admin?secret=YOUR_ADMIN_SECRET
"""
from aiohttp import web
from database import get_admin_stats, get_all_users
from config import ADMIN_SECRET, BOT_VERSION

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nexora Admin Panel</title>
<style>
  :root{{--bg:#0f0f1a;--card:#1a1a2e;--accent:#6c63ff;--green:#00d4aa;--red:#ff4757;--yellow:#ffa502;--text:#e8e8f0;--sub:#8888aa}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}}
  .header{{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px 30px;border-bottom:1px solid #2a2a4a;display:flex;justify-content:space-between;align-items:center}}
  .header h1{{font-size:1.5rem;color:var(--accent)}}
  .header span{{color:var(--sub);font-size:.85rem}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;padding:30px}}
  .card{{background:var(--card);border-radius:16px;padding:24px;border:1px solid #2a2a4a;transition:.3s}}
  .card:hover{{border-color:var(--accent);transform:translateY(-2px)}}
  .card .label{{color:var(--sub);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}}
  .card .value{{font-size:2rem;font-weight:700}}
  .card .sub{{color:var(--sub);font-size:.8rem;margin-top:4px}}
  .card.green .value{{color:var(--green)}}
  .card.yellow .value{{color:var(--yellow)}}
  .card.red .value{{color:var(--red)}}
  .card.accent .value{{color:var(--accent)}}
  .section{{padding:0 30px 30px}}
  .section h2{{font-size:1.1rem;color:var(--sub);margin-bottom:16px;text-transform:uppercase;letter-spacing:.08em}}
  .bar-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
  .bar-label{{width:120px;font-size:.85rem;color:var(--text);text-align:right}}
  .bar-outer{{flex:1;background:#2a2a4a;border-radius:999px;height:10px;overflow:hidden}}
  .bar-inner{{height:100%;border-radius:999px;background:linear-gradient(90deg,var(--accent),var(--green));transition:.5s}}
  .bar-count{{width:60px;font-size:.8rem;color:var(--sub)}}
  .users-table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  .users-table th{{text-align:left;color:var(--sub);padding:8px 12px;border-bottom:1px solid #2a2a4a;font-weight:500}}
  .users-table td{{padding:8px 12px;border-bottom:1px solid #1a1a2e}}
  .badge{{padding:2px 8px;border-radius:999px;font-size:.75rem;font-weight:600}}
  .badge.free{{background:#2a2a4a;color:var(--sub)}}
  .badge.basic{{background:#1a3a2a;color:var(--green)}}
  .badge.pro{{background:#2a1a4a;color:var(--accent)}}
  .footer{{text-align:center;padding:20px;color:var(--sub);font-size:.8rem;border-top:1px solid #2a2a4a}}
  .refresh-btn{{background:var(--accent);color:white;border:none;padding:8px 20px;border-radius:8px;cursor:pointer;font-size:.85rem;transition:.2s}}
  .refresh-btn:hover{{opacity:.8}}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>🤖 Nexora Admin Panel</h1>
    <span>PDF Doctor Bot v{version} · {today}</span>
  </div>
  <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
</div>

<div class="grid">
  <div class="card accent">
    <div class="label">Total Users</div>
    <div class="value">{total_users}</div>
    <div class="sub">All registered</div>
  </div>
  <div class="card green">
    <div class="label">Active Today</div>
    <div class="value">{today_active}</div>
    <div class="sub">Unique users</div>
  </div>
  <div class="card yellow">
    <div class="label">Operations Today</div>
    <div class="value">{today_ops}</div>
    <div class="sub">Total processed</div>
  </div>
  <div class="card red">
    <div class="label">Pending Payments</div>
    <div class="value">{pending_payments}</div>
    <div class="sub">Awaiting approval</div>
  </div>
</div>

<div class="grid" style="grid-template-columns:repeat(3,1fr)">
  <div class="card">
    <div class="label">🆓 Free Users</div>
    <div class="value" style="color:var(--sub)">{free_users}</div>
    <div class="sub">{free_pct}% of total</div>
  </div>
  <div class="card">
    <div class="label">⭐ Basic Users</div>
    <div class="value" style="color:var(--green)">{basic_users}</div>
    <div class="sub">{basic_pct}% of total</div>
  </div>
  <div class="card">
    <div class="label">👑 Pro Users</div>
    <div class="value" style="color:var(--accent)">{pro_users}</div>
    <div class="sub">{pro_pct}% of total</div>
  </div>
</div>

<div class="section">
  <h2>📊 Top Features This Month</h2>
  {feature_bars}
</div>

<div class="section">
  <h2>👤 Recent Users</h2>
  <div style="background:var(--card);border-radius:16px;border:1px solid #2a2a4a;overflow:hidden">
  <table class="users-table">
    <tr><th>User ID</th><th>Name</th><th>Plan</th><th>Joined</th><th>Total Ops</th></tr>
    {user_rows}
  </table>
  </div>
</div>

<div class="footer">
  Nexora PDF Doctor Bot v{version} · Admin Panel · Auto-refresh every 60s
  <script>setTimeout(()=>location.reload(),60000)</script>
</div>
</body></html>"""


async def admin_panel(request: web.Request) -> web.Response:
    """Serve the admin web dashboard."""
    secret = request.query.get("secret", "")
    if secret != ADMIN_SECRET:
        return web.Response(
            text="<h1>🔒 Access Denied</h1><p>Pass ?secret=YOUR_SECRET in URL</p>",
            content_type="text/html", status=403
        )

    stats = await get_admin_stats()
    users = await get_all_users()

    total = max(stats["total_users"], 1)
    free_pct  = round(stats["free_users"]  / total * 100)
    basic_pct = round(stats["basic_users"] / total * 100)
    pro_pct   = round(stats["pro_users"]   / total * 100)

    # Feature bars
    month_stats = stats["month_stats"]
    top_features = sorted(month_stats.items(), key=lambda x: x[1], reverse=True)[:12]
    max_count = max((v for _, v in top_features), default=1)
    bars = ""
    for feat, cnt in top_features:
        pct = round(cnt / max_count * 100)
        bars += f"""<div class="bar-row">
          <div class="bar-label">{feat.title()}</div>
          <div class="bar-outer"><div class="bar-inner" style="width:{pct}%"></div></div>
          <div class="bar-count">{cnt}</div>
        </div>"""
    if not bars:
        bars = '<p style="color:#555">No data yet this month</p>'

    # User rows (last 20)
    user_rows = ""
    plan_badge = {"free": "free", "basic": "basic", "pro": "pro"}
    for u in sorted(users, key=lambda x: x.get("joined_at", ""), reverse=True)[:20]:
        plan = u.get("plan", "free")
        badge_cls = plan_badge.get(plan, "free")
        name = str(u.get("name", "Unknown"))[:20]
        joined = str(u.get("joined_at", ""))[:10]
        total_ops = u.get("total_ops", 0)
        user_rows += (
            f"<tr><td><code>{u.get('user_id','?')}</code></td>"
            f"<td>{name}</td>"
            f"<td><span class='badge {badge_cls}'>{plan.upper()}</span></td>"
            f"<td>{joined}</td>"
            f"<td>{total_ops}</td></tr>"
        )
    if not user_rows:
        user_rows = "<tr><td colspan='5' style='color:#555;text-align:center'>No users yet</td></tr>"

    html = ADMIN_HTML.format(
        version=BOT_VERSION,
        today=stats["today"],
        total_users=stats["total_users"],
        today_active=stats["today_active"],
        today_ops=stats["today_ops"],
        pending_payments=stats["pending_payments"],
        free_users=stats["free_users"],  free_pct=free_pct,
        basic_users=stats["basic_users"],basic_pct=basic_pct,
        pro_users=stats["pro_users"],    pro_pct=pro_pct,
        feature_bars=bars,
        user_rows=user_rows,
    )
    return web.Response(text=html, content_type="text/html")

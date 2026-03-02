"""
Progress Bar Utility — animated progress via message editing.
"""
import asyncio

BLOCKS_TOTAL = 10

def _bar(pct: int) -> str:
    filled = round(pct / 100 * BLOCKS_TOTAL)
    bar = "🟩" * filled + "⬛" * (BLOCKS_TOTAL - filled)
    return f"{bar} <b>{pct}%</b>"

class ProgressMsg:
    """Edit a message to show a progress bar."""

    def __init__(self, message, title: str = "Processing"):
        self.msg   = message
        self.title = title
        self._pct  = 0

    async def update(self, pct: int, detail: str = ""):
        pct = max(0, min(100, pct))
        if pct == self._pct:
            return
        self._pct = pct
        text = f"⚙️ <b>{self.title}</b>\n\n{_bar(pct)}"
        if detail:
            text += f"\n<i>{detail}</i>"
        try:
            await self.msg.edit_text(text, parse_mode="HTML")
        except Exception:
            pass

    async def done(self, caption: str = "✅ Done!"):
        try:
            await self.msg.edit_text(
                f"✅ <b>{self.title}</b>\n\n{_bar(100)}\n\n{caption}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    async def fail(self, error: str):
        try:
            await self.msg.edit_text(
                f"❌ <b>{self.title} Failed</b>\n\n<code>{error[:200]}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass

    async def delete(self):
        try:
            await self.msg.delete()
        except Exception:
            pass


async def make_progress(update, title: str) -> ProgressMsg:
    """Create and return a ProgressMsg."""
    msg = await update.message.reply_text(
        f"⚙️ <b>{title}</b>\n\n{_bar(0)}\n<i>Starting...</i>",
        parse_mode="HTML"
    )
    return ProgressMsg(msg, title)

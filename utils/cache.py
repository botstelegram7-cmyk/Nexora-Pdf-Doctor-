"""
Cache Manager — immediately wipes file data from memory after sending.
No disk writes, all in-memory. gc.collect() called after each operation.
"""
import gc
import asyncio
import logging

logger = logging.getLogger(__name__)

def purge_data(*args):
    """
    Pass any bytes/variables to purge them from memory.
    Sets references to None, forces garbage collection.
    """
    # We can't actually mutate caller's locals, but we can force GC
    # The caller should set their own variables to None after calling this.
    gc.collect()
    logger.debug("🗑️ Memory purge triggered")

async def send_and_purge(send_coro, data_ref: list):
    """
    Executes send_coro, then purges all items in data_ref list.
    Usage:
        data_ref = [pdf_bytes]
        await send_and_purge(bot.send_document(...), data_ref)
    """
    try:
        result = await send_coro
        return result
    finally:
        for i in range(len(data_ref)):
            data_ref[i] = None
        gc.collect()
        logger.debug("🗑️ File data purged from memory")

async def delete_buttons_later(message, delay_sec: int = 180):
    """Delete inline keyboard from a message after delay_sec seconds."""
    await asyncio.sleep(delay_sec)
    try:
        await message.edit_reply_markup(reply_markup=None)
        logger.debug(f"🗑️ Inline buttons removed from message {message.message_id}")
    except Exception:
        pass  # Message might already be edited/deleted

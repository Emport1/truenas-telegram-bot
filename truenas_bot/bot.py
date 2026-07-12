from __future__ import annotations

import asyncio
import io
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import Settings
from .render import render_json, render_markdown
from .twitter import XApiError, XClient, extract_post_id

log = logging.getLogger(__name__)


class BotService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.x = XClient(settings.x_auth_token, settings.x_ct0, settings.x_max_replies, settings.x_account_db)
        self.lock = asyncio.Lock()

    def allowed(self, update: Update) -> bool:
        return bool(update.effective_user and update.effective_user.id in self.settings.allowed_user_ids)

    async def reject(self, update: Update) -> None:
        log.warning("Rejected Telegram user id=%s", update.effective_user.id if update.effective_user else None)
        if update.effective_message:
            await update.effective_message.reply_text("Not authorized.")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return await self.reject(update)
        await update.effective_message.reply_text("Ready. Send /twitter <x.com or twitter.com status URL>.")

    async def twitter(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return await self.reject(update)
        raw = " ".join(context.args)
        try:
            post_id = extract_post_id(raw)
        except ValueError as exc:
            return await update.effective_message.reply_text(str(exc))
        if self.lock.locked():
            return await update.effective_message.reply_text("Another collection is running; try again shortly.")
        notice = await update.effective_message.reply_text("Collecting the conversation from X…")
        try:
            async with self.lock:
                conversation = await self.x.conversation(post_id)
            md = render_markdown(conversation).encode()
            js = render_json(conversation).encode()
            caption = f"Collected {len(conversation.replies)} replies. " + ("Visible reply traversal finished." if conversation.complete else "X omitted replies or the configured limit was reached.")
            await update.effective_message.reply_document(io.BytesIO(md), filename=f"x-{post_id}-tree.md", caption=caption)
            await update.effective_message.reply_document(io.BytesIO(js), filename=f"x-{post_id}-graph.json")
            await notice.delete()
        except XApiError as exc:
            await notice.edit_text(f"Could not collect replies: {exc}")
        except Exception:
            log.exception("Unexpected collection failure")
            await notice.edit_text("Collection failed unexpectedly. Check the app logs.")

    async def plain_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.allowed(update):
            return await self.reject(update)
        context.args = [update.effective_message.text]
        await self.twitter(update, context)


def build_application(settings: Settings) -> Application:
    service = BotService(settings)
    app = Application.builder().token(settings.telegram_token).post_shutdown(lambda _: service.x.close()).build()
    app.add_handler(CommandHandler("start", service.start))
    app.add_handler(CommandHandler("help", service.start))
    app.add_handler(CommandHandler("twitter", service.twitter))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"https?://(?:www\.)?(?:x|twitter)\.com/"), service.plain_url))
    return app

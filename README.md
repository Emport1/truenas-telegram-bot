# TrueNAS Telegram bot

A private, long-polling Telegram bot for TrueNAS SCALE. Version 0.1 implements:

```text
/twitter https://x.com/user/status/123
```

It uses a free, authenticated X web session through `twscrape`, follows the reply timeline, reconstructs reply-to relationships, and sends both an AI-readable Markdown tree and lossless JSON graph. A bare X/Twitter status URL also works.

## Important free-collector limitations

This version has no X API fee. It uses the undocumented GraphQL interface used by x.com, so X can break or rate-limit it without notice. It needs cookies from an ordinary X account. Use a separate read-only account: unofficial automation can invalidate its session or result in suspension. The bot never posts, likes, follows, or modifies the account.

X itself can omit low-quality/spam replies from timelines. Protected, deleted, blocked, withheld, and otherwise inaccessible posts cannot be returned. “Complete” means the visible timeline finished without hitting the configured limit, not that hidden posts were recovered.

## Create credentials

1. In Telegram, message `@BotFather`, run `/newbot`, and copy the bot token.
2. Find your numeric Telegram user ID (for example with `@userinfobot`). This ID is the access control; do not use your username.
3. Sign into a separate X account in a desktop browser. On x.com open Developer Tools (F12), select **Application > Cookies > https://x.com**, and copy the values—not the whole rows—of `auth_token` and `ct0`.

Never paste tokens into chat, source control, screenshots, or TrueNAS app logs.

## Test on a computer

```powershell
Copy-Item .env.example .env
# Edit .env locally, then:
docker compose up --build
```

Message the bot with `/start`, followed by `/twitter <URL>`. Stop it with Ctrl+C. Only one poller may use a bot token at once.

Run unit tests without credentials:

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[test]"
.venv\Scripts\pytest
```

## Deploy on TrueNAS SCALE (24.10 or newer)

TrueNAS can deploy Compose YAML, but its UI cannot build this local source directory by itself. The repeatable deployment path is:

1. Build and publish the image to a private container registry, or build it on a trusted machine and push it. Change `image:` in `truenas-compose.yaml` from the placeholder to that image tag.
2. In TrueNAS, open **Apps > Discover Apps > ⋮ > Install via YAML** and name it `telegram-truenas-bot`.
3. Paste `truenas-compose.yaml`, replace its four `REPLACE_...` values (`Telegram token`, allowed numeric user ID, `auth_token`, and `ct0`), then save. Treat the YAML as secret because it now contains credentials.
4. Open the app logs. A healthy bot logs startup and begins long polling. No inbound port, host networking, privileged mode, TrueNAS API key, or dataset mount is needed.

The bot runs as TrueNAS Apps UID/GID 568, with a read-only filesystem and no Linux capabilities. Its small X session database and generated output are held only in RAM; credentials are reloaded from the app environment after each restart.

## Operations

- Rotate a leaked Telegram token through BotFather and replace it in TrueNAS.
- If X cookies leak, sign out that X session (or all sessions), sign in again, and replace both cookie values in TrueNAS.
- Add family/admin accounts only by appending their numeric IDs to `TELEGRAM_ALLOWED_USER_IDS`.
- Adjust `X_MAX_REPLIES` to cap runtime and memory use. A capped result is marked truncated.

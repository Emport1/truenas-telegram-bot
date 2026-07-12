# GitHub and TrueNAS deployment

## 1. Publish the image

1. On GitHub, create a repository named `truenas-telegram-bot`. Public is simplest; this repository contains no credentials.
2. Upload this project, including the hidden `.github/workflows/publish.yml` file. Do **not** upload `.env`.
3. Commit to the `main` branch. Open the repository's **Actions** tab and wait for **Test and publish container** to finish successfully.
4. Open the repository owner profile, select **Packages**, then `truenas-telegram-bot`. Under **Package settings > Danger Zone**, change package visibility to **Public**. The image contains code only, never credentials.
5. Your image name is `ghcr.io/emport1/truenas-telegram-bot:latest`.

## 2. Obtain the two X cookies locally

Use a separate X account. In Chrome/Edge:

1. Sign in at `https://x.com`.
2. Press F12 and open **Application** (use the `>>` menu if hidden).
3. Expand **Cookies**, select `https://x.com`, and copy the **Value** for `auth_token`.
4. Copy the **Value** for `ct0`.

These values grant access to that X session. Never put them in GitHub, screenshots, chat, or logs.

## 3. Obtain the Telegram numeric ID

Message `@userinfobot` from the Telegram account allowed to control the bot and copy its numeric `Id`. The bot token comes from `@BotFather`.

## 4. Install on TrueNAS 25.10

1. From PowerShell in this project directory, run `./scripts/configure-deployment.ps1`. Enter the numeric Telegram ID, Telegram token, `auth_token`, and `ct0` when prompted. Secret input stays hidden.
2. The helper creates the git-ignored `truenas-compose.private.yaml`. Open that file only to copy its contents.
3. In TrueNAS open **Apps > Discover Apps > ⋮ > Install via YAML**.
4. Name the app `telegram-truenas-bot`, paste the private YAML, and click **Save**.
5. Select the installed app and open **Workloads > Logs**. A healthy app starts Telegram long polling without an exception.
6. In Telegram send `/start`, then `/twitter https://x.com/.../status/...`.

The YAML contains live credentials. Keep your edited copy private and do not commit it. The repository's template contains placeholders only.

## Updating

Push code changes to `main`, wait for the GitHub Action, then select the app in TrueNAS and use **Update** or restart it after pulling the updated `latest` image. For reproducible deployments, use the generated `sha-...` image tag instead of `latest`.

# Server setup (stub) — B-fast, PAPER ONLY

Target: one always-on Linux machine in Sydney (cloud VM, e.g. 2 vCPU / 4 GB / 40 GB,
or a home mini PC), Docker Engine + Compose v2, Tailscale. FD v3.0 §19.2, §21.1 BF0.
This build cannot trade real money; the live gateway port is not used.

## 1. Owner provides (never through chat)

| Item | How |
| --- | --- |
| IBKR Pro individual **cash** account with ASX permission, paper account enabled | IBKR portal (BF0, 20-27 Nov) |
| Paper username + password | typed by the owner **on the server** into `deploy/.env` (username) and `deploy/secrets/tws_password` (chmod 600); never sent to the agent |
| Paper account id (`DU...`) | `config/bfast.yaml` `broker.account_id` (not secret) |
| Telegram bot | create with @BotFather; token typed into `deploy/secrets/telegram_bot_token`; the owner's chat id into `telegram.allowed_chat_ids` |
| Second factor | a TOTP seed generated on the server into `deploy/secrets/totp_seed` and added to the owner's authenticator app by QR on the server screen |
| EODHD token | `deploy/secrets/eodhd_api_token` (B1 connector; B-fast reads the forward store) |
| Dead-man check-in URL | `deploy/secrets/healthchecks_url` |

## 2. Machine

1. Ubuntu 24.04 LTS, unattended security upgrades, UFW default deny inbound, **no
   inbound public port** (checklist item 9: confirm with an external scan).
2. Tailscale for SSH; disable password SSH.
3. Docker Engine and Compose v2 from Docker's apt repository.
4. Durable volume for `/srv` (Postgres data, forward store copy, outputs); nightly
   encrypted off-site backup (restic or rclone) and one restore drill (checklist 9).

## 3. Deploy

```bash
git clone <owner's GitHub remote> /srv/asx-trader && cd /srv/asx-trader/deploy
cp .env.example .env && chmod 600 .env          # fill IBKR_PAPER_USERID, paths
mkdir -p secrets && chmod 700 secrets            # one file per secret, chmod 600
docker compose pull && docker compose build
docker compose up -d
docker compose logs -f gw-paper                  # paper login headless (IBKR 2FA on first login)
docker compose run --rm trader trader-bf validate-config
docker compose run --rm trader trader-bf emg2-list --asof 2026-11-30
```

## 4. Reality spike (BF0, O-1 to O-3) — on the paper account, recorded in `NEXT.md`

- one paper buy and one sell of a band-C share; `LOC` accepted or refused, cut-off;
- an order found by `orderRef` after a gateway restart;
- executions readable (API and Flex); account tags `SettledCash` / `AvailableFunds`;
- delayed quotes without an ASX subscription (`reqMarketDataType(3)`).

## 5. Not here yet

Scheduler (runner), backups, heartbeat and the live gateway are listed in `NEXT.md`.

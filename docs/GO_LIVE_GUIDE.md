# Go-live guide for the owner (EMG2-18 book, paper first)

Plain English, step by step, written to be done in one sitting (about 3 hours, plus
IBKR's waiting times). Accurate to branch `bigwins-fast` as of 22 Nov 2026; file names
are given so anything here can be checked against the code. Since 22 Nov 2026 you run
the book from the **Big Wins app** on your phone (approvals, alerts, controls); Telegram
is optional (appendix T).

**What this build can and cannot do.** It runs the EMG2-18 book on an **IBKR paper
account only**. It cannot place a real-money order: `LIVE_TRADING_ENABLED` is hard-coded
`False`, `broker.allow_live` can only be `false` (`trader/bfast_config.py`), and the
IBKR adapter refuses a live port, an account id that does not start with `DU`, and a
gateway that manages any non-`DU` account (`trader/broker/ibkr.py`). Real money comes
later through a separate, reviewed code change, after the checklist in part E.

**The one rule about secrets.** Passwords, tokens and the authenticator seed are typed
by you, **on the server**, into files under `deploy/secrets/`. Never paste them into a
chat (with me or anyone), an email, or a file in git. The code reads them only from
those files (Docker secrets under `/run/secrets`, `trader/secrets.py`); there is no
config field or environment variable for them. Your IBKR account id (`DU...`) and your
Tailscale log-in are not secrets; they go in `config/bfast.local.yaml` on the server
(not in git; laid over `config/bfast.yaml`).

Contents: A. IBKR - B. Server - C. The phone app, alerts and the authenticator - D. First
messages, approving in the app, the controls - E. What is left before go-live -
**F. Emergencies (from a borrowed device)** - T. Telegram (optional). The one-page card
for your second person is `docs/EMERGENCY_CARD.md`.

---

## A. Interactive Brokers (IBKR)

You do these in the IBKR web portal (Client Portal) and, for one step, the TWS desktop
program. Menu names move around in IBKR's portal; if a name below differs, search the
portal's settings for the words in quotes.

### A1. The account

1. Open (or confirm you have) an **IBKR Pro, individual, cash account** (not margin) in
   Australian dollars. Owner decision D-5 / "Later the same day" in
   `OWNER_DECISIONS_2026-11-19.md`.
2. **Trading permissions**: "Stocks" for **Australia (ASX)**. The A200 fund (an ETF on
   the ASX) is covered by the same permission.
3. Fund it later: the **A$10,000** deposit is a go-live item (part E), not needed for
   paper.

### A2. Pricing: choose TIERED

Settings > Account Settings > "Pricing" (IBKR Pro: Fixed or Tiered) > **Tiered**.
At this book's turnover tiered is about A$710 a year against about A$845 fixed
(report 91; `NEXT.md` "What the owner must provide"). The paper account follows the
pricing plan of the live account; the simulated twin assumes IBKR's commission
(`trader/orders.py`, `CommissionModel`).

### A3. The paper account

1. Settings > Account Settings > "Paper Trading Account": **create / enable** it. IBKR
   gives it its own **username** and an account id starting with **DU** (for example
   `DU1234567`). Set a password for the paper username.
2. **Cash on the paper account: exactly A$10,000, the same as the journal deposit.**
   IBKR starts a paper account with a large made-up balance (often US$1,000,000). The
   trader reconciles every day, to the cent, its own journal cash against the paper
   account's cash (`trader/reconcile.py`, `trader/runner.py`); its loss rule (L11) and
   the A$10,000 cap work on a A$10,000 book. Any difference is a reconciliation break:
   the book halts (`HALTED_INTEGRITY`) and nothing is sent. So:
   - **Base currency AUD.** Log in to Client Portal **with the paper username**:
     Settings > Account Settings > "Base Currency" (Configuration) > **AUD**.
   - **Reset the balance.** Log in to Client Portal with your **live** username:
     Settings > Account Settings > "Paper Trading Account" > **"Reset Paper Trading
     Account"** (IBKR's wording varies: look for "reset" and "net liquidation value" /
     "starting balance"). Enter **10000** (AUD), confirm. A reset clears all paper
     positions and orders and usually takes effect the **next day** (overnight).
   - **Check** the next day in the paper Portal (Portfolio / Account summary): cash
     **A$10,000.00**, no positions, nothing in other currencies. Then the deposits are
     recorded with exactly the same amount (E1.2): `trader-bf deposit --book
     EMG2_18_PAPER --amount 10000`, and `trader-bf status` shows `EMG2_18_PAPER: cash
     A$10000`. The first 16:30 reconciliation compares the two.
   - If IBKR does not let you choose A$10,000 (only fixed amounts, or USD), **do not
     start**: tell me what the page offers. Starting with a different paper balance and
     a A$10,000 journal breaks the reconciliation on day one, by design.
   - Reset again (same steps) **after the paper dry run** (E3) and before the official
     paper start, so the official book starts from A$10,000 cash and no holdings.
3. "Share real-time market data subscriptions with paper account": **Yes** (see A5).

### A4. Order precautions: maximum order value above A$10,000

IBKR has "precautionary settings" that reject an order above a set value or size. The
system needs **one order of about A$9,900**: at a FUND start the whole book goes into
A200 in one order (band-trend switch L15, BF-D28, `config/bfast.yaml`
`band_trend.fund_order_max_aud: 10000`), and a large sell can also pass A$800 (BF-D3).
Share buys stay limited to A$800 by the system itself (`risk.order_value_max_aud`).

1. In TWS (desktop), logged in **with the paper username**: Global Configuration >
   Presets > Stocks > "Precautionary Settings":
   - **Total Value Limit** (maximum order value): **11,000** (AUD) - above A$10,000, but
     still a ceiling;
   - **Size Limit** (shares per order): **1,000,000**. Band-C shares can cost under one
     cent, so a A$550 parcel can be 100,000+ shares; the value limit is the real guard;
   - leave the other checks on.
2. Global Configuration > API > Settings: leave **"Read-Only API" off** (the gateway
   must place orders; `deploy/docker-compose.yml` sets `READ_ONLY_API: "no"`).
3. **Photograph** the precaution screen (go-live checklist item 7).
4. Do the same on the live username before real money (part E).

`[checked in the reality spike]`: the gateway runs in a container
(`gnzsnz/ib-gateway`), so I confirm on the paper gateway that an order of about
A$9,900 is accepted and that one above A$11,000 is rejected by IBKR.

### A5. Market data (bid/ask for ASX)

The system does **not** need live prices to trade: decisions use the evening's closing
prices from the data store, and orders are "limit on close" (LOC) orders into the ASX
closing auction (`config/bfast.yaml` `execution.order_type: LOC`). It does ask IBKR for
a quote just before each order and records bid, ask and mid (BF-D22, journal table
`bf_order_quotes`) so the real cost of each fill can be measured. The adapter asks for
"delayed if not subscribed" data (`IbkrSettings.market_data_type = 3`,
`trader/broker/ibkr.py`).

- **Without an ASX subscription**: quotes are about 20 minutes delayed and may have no
  bid/ask; the order still goes, and the cost reading says "no two-sided quote".
- **With one** (Settings > User Settings > "Market Data Subscriptions"; the ASX
  "Total"/Level 1 non-professional package; check the monthly price shown): real-time
  bid/ask. Share it with the paper account (A3.3).
- One IBKR login uses live data at a time: if you are logged in to the live account on
  your phone, the paper gateway may fall back to delayed data. That is harmless.

My recommendation: subscribe to ASX Level 1 before real money, so the cost of the first
real fills can be measured. In the reality spike I record whether the paper gateway
gets live or delayed quotes.

### A6. Flex Web Service token and the Activity Flex query

The trader downloads IBKR's own daily statement (Activity Flex, XML) for the paper
account and books dividends, corporate actions and the tax view from it (BF-D23,
BF-D27, BF-D29). It needs a **token** and a **query id**.

Log in to Client Portal **with the paper username** (the query must be of the `DU`
account; a statement of any other account is refused, `trader/flex_pull.py`
`check_paper`).

**1. The query.** Performance & Reports > Flex Queries > "Activity Flex Query" > Create
(+). Name it `bigwins-paper`. Choose these **sections** (the parser is
`trader/data/flex.py` `parse_statements`; "select all" fields in each is the simplest -
extra fields are ignored, missing ones are not):

| Section | Option(s) | Fields the code reads (must be ticked) |
| --- | --- | --- |
| **Open Positions** | **Summary** | symbol, conid, assetCategory, currency, position, markPrice, reportDate, levelOfDetail |
| **Trades** | **Execution** | ibExecID, tradeID, symbol, buySell, quantity, tradePrice, ibCommission, tradeDate, dateTime, settleDateTarget (orderReference if offered; optional) |
| **Cash Transactions** | Dividends, Payment In Lieu Of Dividends, Withholding Tax, Deposits & Withdrawals, Broker Interest Paid/Received, Other Fees; level **Detail** | transactionID, type, amount, currency, dateTime, settleDate, symbol, description, **exDate**, **payDate**, reportDate |
| **Corporate Actions** | (all) | transactionID, actionID, type, symbol, conid, quantity, amount, proceeds, value, reportDate, dateTime, description, levelOfDetail |

Account Information may be added; nothing else is needed.

**Delivery configuration** of the query:
- Format: **XML**;
- Period: **Last Business Day** (the trader overrides it with explicit from/to dates);
- Date format: **yyyyMMdd** (the parser accepts `yyyyMMdd` or `yyyy-MM-dd` only);
  Time format: **HHmmss**; Date/Time separator: **; (semi-colon)**;
- Profit and loss: default; Include canceled trades: **No**; Include currency rates:
  No; Breakout by day: No.

Save. The list of queries shows the **Query ID** (a number) next to `bigwins-paper`.

**2. The token.** On the Flex Queries page (or Settings > Account Settings > Reporting):
"Flex Web Service Configuration" > **enable**, then **generate a token**. Choose the
longest validity offered (up to a year) and put a reminder in your calendar a week
before it ends. If you can restrict it to an IP address, use the server's public IP
(part B). Keep the token on screen; you type it into the server in step B6.

When the token expires or is refused, the trader pages you ("PAGE IBKR Flex statement
... refused"); the reconciliation still runs.

---

## B. The server (BinaryLane, Singapore region, Sydney time)

### B1. Order the server

BinaryLane > new server: **Singapore region** (the server's clock is set to Sydney time by the bootstrap), **2 vCPU / 4 GB RAM**, at least **40 GB** disk,
**Ubuntu 24.04 LTS**, with an SSH key (from your laptop) rather than a password. Note
its public IP.

### B2. Tailscale, firewall, updates

**Shortcut:** `deploy/server_bootstrap.sh` does B2, B3, the folders of B5 and the key of B4
in one go (paste it into the server as root). The steps below are what it runs.

Log in once with `ssh root@<public IP>`, then:

```bash
apt update && apt -y full-upgrade && apt -y install unattended-upgrades ufw git qrencode
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --ssh            # opens a login link: approve it in your Tailscale account
ufw default deny incoming && ufw default allow outgoing && ufw enable
timedatectl                   # "System clock synchronized: yes" (the authenticator codes need it)
```

Install Tailscale on your laptop and phone too. From now on connect with
`ssh root@<server's Tailscale name>`; the server has **no open inbound port** (UFW denies
all; the compose file publishes only the read-only phone page, and only on the server's
own loopback address 127.0.0.1, reached through Tailscale: D5). In BinaryLane you can
also turn off password log-in. (Go-live item 9 includes an outside port scan; I do it.)

### B3. Docker

```bash
curl -fsSL https://get.docker.com | sh
docker compose version        # Compose v2
```

### B4. Get the code (private repository)

The repository is private, so the server gets a **read-only deploy key**:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/bigwins_deploy -N ''
cat ~/.ssh/bigwins_deploy.pub          # the PUBLIC key: safe to copy
```

GitHub > `mcpaulcary-del/bigwins-trader` > Settings > Deploy keys > Add deploy key:
paste the public key, title "sydney server", **leave "Allow write access" off**. Then:

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/bigwins_deploy' \
  git clone -b bigwins-fast git@github.com:mcpaulcary-del/bigwins-trader.git /srv/asx-trader
cd /srv/asx-trader && git log --oneline -1
```

### B5. Folders and `deploy/.env`

The trader container mounts five host folders (`deploy/docker-compose.yml`, service
`trader`). Create them:

```bash
mkdir -p /srv/bigwins_forward/data/eodhd /srv/ref /srv/record/68_forward_record /srv/flex/inbox
chown 10001:10001 /srv/flex/inbox      # the trader runs as uid 10001 and writes here
# after the store has been copied in from the record (see below):
chown -R 10001:10001 /srv/bigwins_forward/data/eodhd   # the daily refresh appends to it
cd /srv/asx-trader/deploy
cp .env.example .env && chmod 600 .env
nano .env
```

`deploy/.env` (no passwords in it):

| Variable | Value | What it is |
| --- | --- | --- |
| `IBKR_PAPER_USERID` | your **paper** username | the gateway logs in with it |
| `FORWARD_STORE` | `/srv/bigwins_forward/data/eodhd` | the daily price store (config `data.forward_store`); writable: the trader appends each session's EODHD bulk file (BF-D31) |
| `REF_DIR` | `/srv/ref` | holds `etp_list.txt` (config `data.etp_list`) |
| `RECORD_DIR` | `/srv/record/68_forward_record` | the record's folder with `CORPORATE_ACTIONS.csv` (read-only; `data.corporate_actions_csv`, BF-D23) |
| `FLEX_INBOX` | `/srv/flex/inbox` | IBKR Flex XML files; the trader writes them (`data.flex_inbox`, BF-D27) |
| `INFO_ARCHIVE_DIR` | optional, default `/var/lib/bigwins/info` | the private announcements archive (BF-D78); outside the repository, read-only in the app; written only by the archive job, which is off until you switch it on (part C10) |

The **frozen LIC list** needs nothing from you: it is `config/lic_list.csv` in the
repository (69 codes), pinned by SHA-256 in `config/bfast.yaml`
(`data.lic_list_sha256: af441f28...`). Do not edit it. If it is missing or changed, the
trader refuses every decision and order and pages you (BF-D21); `$TRADER_BF_LIC_LIST`
is only for tests outside the container.

The three data folders (`FORWARD_STORE`, `REF_DIR`, `RECORD_DIR`) are filled once from
the research record; I set that up with you in the reality-spike session. From then on
the trader **refreshes the price store itself** every trading day (BF-D31,
`trader/store_refresh.py`): after the ASX close (17:35, 18:35, ... 22:05 Sydney) it
downloads EODHD's end-of-day bulk file for the ASX, plus that day's dividends and
splits, and appends them to `FORWARD_STORE`, with the key from the `eodhd_api_token`
secret file only. Each request is counted in the database before it is sent (EODHD
counts a bulk request as 100 calls; `data.store_refresh.calls_per_day: 100000` is the
daily ceiling - lower it if your EODHD plan allows fewer calls). A day already in the
store is not fetched again. If the day's prices are still missing at 22:05, or the key
is missing or refused, or the budget is used up, you get `PAGE price store not
refreshed for <date> ...` and **no decision is made on stale prices** (the 22:20
decision waits until 23:40, then records a rule-14 data block and pages you; holdings
are kept).

### B6. The secret files

Compose needs **twelve** files in `deploy/secrets/` (review F16: the eight you type below plus four that `bigwins update` makes itself: `vapid_private_key`, `app_proxy_key`, `worker_job_key` and `app_passphrase`, which holds `none` until you set your passphrase, BF-D83; thirteen with Telegram on). Optional, read only by the server worker and never by a container: `healthchecks_backup_url` (C5), `healthchecks_daily_url` (C5), `healthchecks_presence_url` (F8), `github_ci_token` (C7 step 9, only if the repository is private) and `healthchecks_record_url` (C10: one outside check per paper-record job, BF-D93). Exactly these names
(`deploy/docker-compose.yml` `secrets:`; the closed list in `trader/secrets.py`). A
missing file stops `docker compose up`.

Type each value yourself; `read -rs` keeps it off the screen and out of the shell
history:

```bash
cd /srv/asx-trader/deploy
mkdir -p secrets && chmod 700 secrets
put() { read -rsp "$1: " v; printf '%s' "$v" > "secrets/$1"; unset v; echo; }
put tws_password          # the IBKR PAPER password (used only by the gateway container)
put ibkr_flex_token       # the Flex Web Service token (A6.2)
put ibkr_flex_query_id    # the query id number (A6.1)
put eodhd_api_token       # the EODHD data token (for the price-store refresh)
put healthchecks_url      # your healthchecks.io ping URL (C5), or type: none
openssl rand -hex 24 > secrets/db_password                   # database password, made here
openssl ecparam -name prime256v1 -genkey -noout | openssl pkcs8 -topk8 -nocrypt -out secrets/vapid_private_key  # phone-alert key (or: bigwins vapid)
for n in app_proxy_key worker_job_key db_dashboard_password; do openssl rand -hex 32 > secrets/$n; done  # app keys (bigwins update makes them too)
python3 -c 'import base64,os;print(base64.b32encode(os.urandom(20)).decode())' > secrets/totp_seed
chmod 444 secrets/*        # see the note below
ls -l secrets              # eleven files, none empty, all -r--r--r--
./check_secrets.sh         # BF-D33: "ok: deploy/secrets is 700 and its 8 files are 444, none empty"
```

Note on permissions: Docker passes these files into the containers as bind mounts
with the server's owner and mode, and every container runs as its own non-root user
(the trader as uid 10001, Postgres as uid 999, the gateway as its own user). So the
**files** must be `444` (readable by any user, writable by none) and the **folder**
`secrets/` must be `700` (only root on the server can even list it; the containers do
not see the folder, only their own files). `chmod 600` files (the old advice) are
unreadable inside the containers.

The stack checks this at every start (BF-D33): a one-shot service `secrets-check` runs
first as uid 10001 with no network, checks all eleven files (present, non-empty, `444`,
readable) **without reading them**, and the gateway, database and trader start only if
it passes. If one is wrong, `docker compose up -d` stops with an error and
`docker compose logs secrets-check` says exactly which file and how to fix it, e.g.

```
SECRET CHECK FAILED: secret db_password: mode 0600 is not readable by other users; the
containers run as other uids (trader 10001) - on the server: cd /srv/asx-trader/deploy &&
chmod 700 secrets && chmod 444 secrets/* (docs/GO_LIVE_GUIDE.md B6), then docker compose up -d
```

The trader checks its own seven files again when it starts (`trader-bf check-secrets`,
also run by `trader-bf run`). `./check_secrets.sh` on the server also checks the folder
mode, which the containers cannot see.

| File | Used by | Read in |
| --- | --- | --- |
| `tws_password` | gw-paper (IB Gateway login) | `deploy/docker-compose.yml` (`TWS_PASSWORD_FILE`) |
| `db_password` | db and trader | compose; `trader/bfast_cli.py` `_journal_from_config` |
| `vapid_private_key` | trader (phone alerts, BF-D40) | `trader/app_notify.py` `WebPush`; made on the server by `bigwins vapid` (and by `bigwins update` if missing) |
| `telegram_bot_token` | trader, **only with Telegram on** (appendix T) | `trader/approval.py` `TelegramTransport` |
| `totp_seed` | trader | `trader/approval.py` `TotpVerifier` |
| `ibkr_flex_token`, `ibkr_flex_query_id` | trader | `trader/flex_pull.py` (read at each pull) |
| `eodhd_api_token` | trader (price-store refresh, BF-D31); the paper record's download jobs (BF-D93: the file is mounted read-only into the record container, never passed on a command line or in the environment) | `trader/store_refresh.py` (read at each refresh); `record/tools/eodhd_shim.py` |
| `app_proxy_key` | dashboard and trader (signed app actions, BF-D46) | made by `bigwins update` |
| `worker_job_key` | trader and the root host worker (signed server jobs, BF-D48) | made by `bigwins update` |
| `db_dashboard_password` | the dashboard's SELECT-only database role (BF-D52) | made by `bigwins update`; the `db-roles` service sets it |
| `healthchecks_url` | dead-man heartbeat (BF-D41), `none` = off | `trader/heartbeat.py` (pinged every 5 minutes); before the trader runs, the server worker pings it instead (BF-D87) |
| `app_passphrase` | trader: the passphrase you keep in your head (BF-D83), stored only as a hash; `none` = not set | `trader/passphrase.py`; set with `bigwins secret app_passphrase` (typed twice, never shown) |
| `healthchecks_backup_url` | server worker only: pinged after each good backup (C5) | `deploy/bigwins.sh` `hc_backup_ping` |
| `healthchecks_daily_url` | server worker only: pinged after each good daily cycle (C5) | `deploy/bigwins.sh` `daily_ping` |
| `healthchecks_presence_url` | server worker only: pinged once a day while you have used the app in the last 14 days; your second contact is on its alerts (F8) | `deploy/bigwins.sh` `presence_ping` |
| `healthchecks_record_url` | server worker only, optional: your healthchecks.io **project ping URL** (`https://hc-ping.com/<ping key>`; healthchecks.io > Project > Settings > Ping key). The worker pings one check per paper-record job under it (`bigwins-daily`, `bigwins-archive`, ...; each is created by its first ping), with a start, a success or a failure signal (BF-D93) | `deploy/record.sh` `rec_ping` |
| `github_ci_token` | server worker only, optional: a read-only GitHub token (Actions: read, this repository only) so the automatic app updates can read the CI result while the repository is private; not needed while it is public (BF-D90) | `deploy/autoupdate.py` `ci_status` |

### B7. Your settings in `config/bfast.local.yaml` (this server only)

Server-only settings go in `config/bfast.local.yaml`, which is not in git and is laid
over `config/bfast.yaml` (so `bigwins update` never conflicts with them):

```bash
cd /srv/asx-trader && nano config/bfast.local.yaml
```

```yaml
broker:
  account_id: DU1234567       # your paper id; the trader refuses anything not DU...
tax:
  marginal_rate: 0.345        # optional: your marginal rate incl. Medicare, for the Tax screen
```

Your Tailscale log-in (who may approve in the app) is added there by `bigwins` option 11
(C2). `trader-bf run` refuses to start without the account id. (If you edited
`config/bfast.yaml` itself earlier, move those lines here and run
`git checkout config/bfast.yaml`; `bigwins update` says so if needed.)

### B8. First start (paper)

```bash
bigwins ibkr          # the PAPER user name and the DU... account id (written safely)
bigwins secret tws_password
bigwins update        # builds and starts the stack; the trader only checks and waits
bigwins status        # every service "Up"; the trader "idle (sleep)"
bigwins logs          # ends with: ok: book EMG2_18_PAPER, mode paper, cap A$10000
```

If IBKR asks for a second factor at the paper log-in, approve it on IBKR Mobile. **Do not
log in to TWS or the Client Portal trading screen with the paper user name while the
gateway runs** (review F12): IBKR allows one session per user name, and your log-in
throws the gateway out (it logs back in at the next restart, possibly after the 15:45 send).

At this point the trader **only checks its config and waits**. After the reality spike
(part E) the trader is started with `bigwins start-trader <date>` (it asks for a yes;
it sets `TRADER_CMD` in `deploy/.env`, nothing in the compose file is edited); that is
when the messages in part D begin.

---

## C. The phone app, alerts and the authenticator

The Big Wins app is a private web app on your server, reached only through your own
Tailscale account (`tailscale serve`, HTTPS; nothing is open to the internet). You view
the book, approve orders, get alerts and control the trader and the server from it.

### C1. Put the app on your phone

1. On your phone: install the **Tailscale** app and sign in with the same account as the
   server (B2). Turn it on.
2. On the server: `bigwins` > **9) Turn on the phone app** (it runs `tailscale serve --bg
   8080`). It prints the address, like `https://bigwins.<your-tailnet>.ts.net`. If
   Tailscale asks you to enable HTTPS certificates, click its link, allow it, choose 9 again.
3. On the phone, open that address. **iPhone**: Safari > Share > **Add to Home Screen**.
   **Android**: Chrome menu (⋮) > **Add to Home screen**. From now on open Big Wins from
   its icon (alerts on iPhone work only from the home-screen icon).

Before the first trading day it says "Waiting for the first trading day"; that is normal.

### C2. Allow your phone to act (approve, pause...)

Viewing works for any device on your tailnet; **acting** needs your Tailscale log-in on
the server's allow-list. Until it is set, every action is off and the app says so.

1. On the server: `bigwins` > **11) Allow my phone to act**. It reads your log-in and the
   app's address from Tailscale (`tailscale status`), shows them, and after you type `y`
   writes them to `config/bfast.local.yaml` (`app: allowed_logins` and `public_host`;
   this server only, never in git). Only requests from your own app's address count.
2. `bigwins` > **4) Restart the trader** (it restarts the app too).

### C3. Turn on alerts

1. In the app: **Inbox** > **Alerts on this phone** (or Settings > Turn on alerts).
2. Type your 6-digit code (a new device needs it; at most 5 devices), tap **🔔 Turn on
   alerts**, then **Allow**. A test alert arrives: "Alerts are on for
   this phone."
3. Approval requests and PAGE alerts always arrive, at high priority; you can switch the
   daily report and other messages on or off on the same screen. Every message is also
   kept in the app's **Inbox** (with filters: alerts, approvals, reports, your actions).

The alert key is made on the server (`bigwins vapid`, or automatically by `bigwins
update`). If you ever make a new key, tap "Turn on alerts" again on each phone.

### C4. The authenticator (second factor)

Approving, refusing, resuming, continuing, code changes and server jobs need a 6-digit
one-time code from an authenticator app (`trader/approval.py`: RFC 6238, SHA-1, 30
seconds, each code accepted once, in the app and in Telegram alike). On the server, show
the seed you created in B6 as a QR code and scan it with Google Authenticator, Microsoft
Authenticator or 1Password:

```bash
qrencode -t ansiutf8 "otpauth://totp/bigwins-trader?secret=$(cat /srv/asx-trader/deploy/secrets/totp_seed)&issuer=bigwins"
clear
```

The app now shows "bigwins-trader" with a 6-digit code. Keep a **paper backup** of the
seed (print the QR or write the letters down) somewhere safe: if you lose your phone,
nobody can re-arm the system or approve an order without it.

**A new seed (BF-D83)**: `bigwins new-totp` (or menu 17) makes a new seed, shows its QR
code once on the screen, clears the screen and restarts the trader and the app. From then
on only the new codes work; delete the old "bigwins-trader" entry in your authenticator.
Use it after a lost phone (F1) or a lost authenticator (F2). Older backups still hold the
old seed: after any restore, run `bigwins new-totp` again.

**Your passphrase (BF-D83, before real money)**: `bigwins secret app_passphrase` (menu 18).
Choose a few words you will remember (at least 12 characters) and keep it **in your
head**, not on the phone. The app then asks for it, besides the 6-digit code, when you
resume or continue, approve an update, roll back, show the backup key, start Claude
remote control and unlock actions. Approvals and refusals still need only the code. A
wrong passphrase counts like a wrong code (3 in 15 minutes lock code actions). Restart
the trader after setting it (menu 4). Server > Health says "Passphrase: not set" until
then.

**Lock actions (BF-D83)**: Home or Controls > **Lock actions** is one tap. While locked,
approvals, refusals, re-arming, code changes and server jobs are refused until you tap
**Unlock** and enter your code (and passphrase). Pause, Kill and Stop always work with one
tap, locked or not. Use it when the phone may be out of your hands (travel, repairs, a
night out), and as the first step if you think someone else has it.

### C5. Strongly recommended: healthchecks.io (tells you if the server goes quiet)

The app cannot tell you that the server is down, so the trader "checks in" with
healthchecks.io every 5 minutes; if the check-ins stop, healthchecks.io emails you (or
pushes to its own app).

1. Sign up free at healthchecks.io, **Add Check**: period 5 minutes, grace 15 minutes.
2. Copy its ping URL (`https://hc-ping.com/...`; keep it private).
3. On the server: `bigwins` > 5) Add/replace a secret > `healthchecks_url`, paste it.
   Restart the trader. The Server tab shows "Heartbeat OK".

Type `none` instead to keep it off (not recommended: without it nothing tells you that
the whole server is down).

**Second check for backups (optional, review F9)**: add a second check (period 1 day,
grace 2 hours) and store its ping URL as the secret `healthchecks_backup_url`; the
worker pings it after every good backup, so a week without backups emails you even if
the app is down. The app itself pages when the last good backup is over 26 hours old,
when the server worker has been silent for 5 minutes, when the disk is over 80% full
and when less than 10% of memory is free.

**Daily-cycle check (strongly recommended, BF-D77 / BF-D81)**: one more free check
that says "the trader finished its day". The app's own alarm runs inside the trader, so
if the trader or the whole server stops, this outside check is the only thing that can
tell you. Set it up **after the paper trader has started** (before
that there is no daily cycle, and the check would alarm):

1. On healthchecks.io, **Add Check**, name it "Big Wins daily cycle". Choose
   **Simple**: period **1 day**, grace **3 hours**. (The server pings it once a day,
   shortly after 23:00 Sydney, also on weekends and public holidays.)
2. Under **Notifications** turn on the healthchecks.io phone app or email (free).
3. Copy the check's ping URL. It is a secret: never paste it into a chat, a message or
   GitHub.
4. On the server: `bigwins` > 5) Add/replace a secret > `healthchecks_daily_url`, paste
   it. Nothing else to restart: the server worker pings after the next good daily cycle,
   and the app's Server > Health shows "Daily-cycle check: set up".

The app's own missed-job alarm (Server > Health) also pushes one alert to your phone
for each late or failed job (daily run, price download, nightly backup, weekly restore
test, announcements archive), as long as the server is up.

### C5b. Tailscale: disable key expiry for the server (review F8)

Tailscale admin console > **Machines** > the server > **...** > **Disable key expiry**.
Without it the server's key expires after 180 days: it drops off your tailnet and the
phone app stops working until you log the server in again.

### C6. Server worker and Claude on the server

Who is trusted: anyone with root on the server (it runs Tailscale, Docker, the worker
and Claude, and can read every secret). Keep root to yourself. The app's actions are
signed between its parts and the worker runs only jobs the trader signed, for the exact
commit you approved; an approved update expires after 12 hours. A rollback does not undo
database migrations (the app asks before rolling back across one).

- `sudo bigwins install-worker` (once): a small service that sends the server's status
  to the app's **Server** tab every 30 seconds and runs the server jobs you ask for in
  the app (restart, update, go back a version, checks, Claude remote control; each
  needs your code).
- **Ask Claude about the server**: Server tab > Start / check… (code) starts Claude Code
  in remote-control mode on the server; then tap **Open Claude** and continue in the
  official Claude app (signed in with your Claude account). The **first sign-in is done
  once in Termius**: `tmux attach -t remote`, follow the sign-in, then Ctrl-b d to leave
  it running. The Big Wins app never runs Claude or any command itself.
  **It stops by itself after 2 hours** (BF-D85; the server worker ends the session; a
  different number of hours goes in `/etc/bigwins/claude_remote_hours`, root only). On a
  live book it is **off** unless you switch it on deliberately on the server
  (`touch /etc/bigwins/claude_remote_live`). It runs as root on purpose: Claude is there to
  look after the server (Docker, the services, the checks), and a user that may run Docker
  is as powerful as root anyway, so a "non-root" Claude would protect nothing. The
  protections are instead: your code and passphrase to start it, the 2-hour stop, off when
  live, and your Claude account's own 2-step verification.

### C7. Upgrading a server that already runs an earlier build

**Owner upgrade sequence (from any earlier build; BF-D61)**, on the server as root,
outside ASX hours (10:00-16:15 Sydney):

1. `git -C /srv/asx-trader pull --ff-only && bigwins update`
   (the first line fetches the new menu itself; `bigwins update` then runs the new
   steps: makes the new keys `app_proxy_key`, `worker_job_key`, `db_dashboard_password`
   and the alert key if missing, rebuilds and restarts; the `db-roles` service creates
   the dashboard's read-only database role).
2. `bigwins` > **11) Allow my phone to act** (writes your log-in and the app's address).
3. `sudo bigwins install-worker` (again: the worker unit has a longer time-out now).
4. `bigwins` > **4) Restart the trader** (restarts the app too).
5. On the phone, open the app > Server > Trader controls and test Pause (one tap: "PAUSED"),
   then Resume with your code; Turn on alerts needs your code too.
6. **After the full-review update (22 Nov 2026, BF-D69..BF-D72)**: run `sudo bigwins
   install-worker` once more (it adds the weekly restore test and builder prune), disable
   the Tailscale key expiry (C5b), and in the app check Backups > the recovery key's
   fingerprint (show and save the key if the screen asks). The update refuses to restart
   the trader if the record checks fail (`trader-bf golden-check`, when the record's
   price store is on the server) and pages instead.

7. **After the scoreboard / Health / announcements update (24 Nov 2026, BF-D75..BF-D81)**:
   `git -C /srv/asx-trader pull --ff-only && bigwins update`. The server worker adds its
   two new timers by itself within a minute (the announcements archive at 07:40 and the
   previous-version twin at 01:20, Tuesday to Saturday); Server > Health says "Timer not
   installed" if it could not, and then `sudo bigwins install-worker` fixes it. The archive
   stays off until part C10. Strongly recommended: the daily-cycle check (C5).

   **This update counts as a trading / infrastructure update** (BF-D81): it changes files
   the trader runs (`trader/bfast_cli.py`, the action server, the config schema, deploy
   scripts), so the app shows it as a strategy update and the strategy id changes, although
   no trading rule or parameter changes (the strategy hash and the strategy settings hash
   stay the same). Deploy it **before the paper trader's first decision (30 Nov)**: before
   the trader has started there is no book, so nothing happens. If the paper trader is
   already running in `update_mode: immediate`, an out-of-cycle decision follows the update
   (same rules, so the same list; its orders still need your approval, and you may refuse
   them), and "Results by strategy version" starts a new segment with the same version
   name.

8. **After the disaster-recovery update (24 Nov 2026, BF-D82..BF-D87)**, outside ASX
   hours: `git -C /srv/asx-trader pull --ff-only && bigwins update` (it makes the
   `app_passphrase` placeholder, rebuilds and restarts; like C7 step 7 it counts as a
   trading / infrastructure update although no trading rule changes: the strategy hash
   and the strategy settings hash stay the same). Then, from the phone, the owner steps
   of part F0 (passphrase, presence check with your second contact, Tailscale device
   approval). From now on the worker pings the heartbeat even before the paper trader
   starts, so a dead server is caught today; the 14-day presence clock starts when the
   paper trader runs.

9. **Automatic app updates (25 Nov 2026, BF-D90), once by hand.** This update changes the
   server scripts, so it cannot apply itself; after it, app-only updates do. In Termius, as
   root (any time while only the demo runs; otherwise outside 10:00-16:15):
   1. `git -C /srv/asx-trader pull --ff-only && bigwins update`
      (in demo mode this also rebuilds and restarts the demo app; with the trader set up it
      rebuilds and restarts as before).
   2. `bigwins autoupdate status`. If it says **timer: NOT installed** (it should appear by
      itself within a minute when the server worker is installed), run
      `sudo bigwins install-worker` and answer `y`.

   That is all. From then on the server looks at GitHub every 30 minutes (at :07 and :37)
   and **applies app-only updates by itself** (screens, documents, research pages) outside
   ASX hours, once GitHub CI has passed for that exact commit and the commit is at least
   1 hour old here; it rebuilds and restarts **only the app** (the demo container, or the
   dashboard), checks that it answers, and goes back to the previous version by itself if
   it does not (and pages you). Anything else (trading code, settings, deploy scripts, the
   worker and this auto-updater, timers, compose, the Dockerfile, secrets handling) still
   waits for you: with the trader running you get one push "Update ready: <title> — tap to
   review and approve" and approve it in Server > Strategy with your 6-digit code (and
   passphrase). **In demo mode there is no trader to approve in**: the demo app shows
   "Update ready on the server: …" at the top, and you apply it in Termius with
   `bigwins update` (one line; it rebuilds the demo too).
   - Switch: `bigwins autoupdate off` / `on` / `status`, or in the app Settings >
     Automatic app updates (6-digit code; turning it on also asks for the passphrase).
   - Health shows "Auto-update: on, last applied <title> at <time>, next check <time>";
     each automatic update is in the Inbox (once the paper trader runs).
   - CI result: read from GitHub's public API (the repository is public today; no key).
     If the repository is made private, auto-updates wait with "GitHub CI result not
     known" until you add a read-only token: github.com > Settings > Developer settings >
     Fine-grained tokens > Generate: repository `bigwins-trader` only, permission
     **Actions: read-only**, expiry 1 year; then `bigwins secret github_ci_token` and paste
     it.

### C8. Backups (server + OneDrive) and the recovery key

1. On the server, once: `apt install age rclone` (if not there yet).
2. `sudo bigwins install-worker` (again): it also installs the nightly backup at 23:30.
3. `bigwins update` makes the backup recovery key (root only).
4. **Connect OneDrive** (once, about 5 minutes). On a Windows laptop: download rclone from
   rclone.org/downloads, unzip it, open a Command Prompt in that folder and run
   `rclone authorize "onedrive"`; sign in to Microsoft in the browser and allow access;
   copy the whole token line it prints. On the server: `bigwins` > **14) Connect
   OneDrive** and answer rclone's questions as the screen says (paste the token when
   asked). A phone alone cannot do this step (rclone needs a computer with a browser).
5. In the app: Server > **Backups** > **Show recovery key…** (your code), then **Show the
   key now**, and save it in your password manager. Then **Back up now…** and
   **Restore test…**: both should say OK.

Every night the server keeps an encrypted copy in `/var/backups/bigwins` and in OneDrive
folder "Big Wins server backups" (30 daily, 12 monthly), plus a readable page of the day in
"…/reports/YYYY/". A failed backup or restore test sends a PAGE.

**OneDrive access (security review M4)**: `bigwins onedrive` gives the server a token for
your **whole** OneDrive. If you prefer, make a free Microsoft account used only for the
backups (and keep its password in your password manager), or keep using your own and
accept that the server could read the rest of your OneDrive. Your choice; the default
is your own account. Backups are always encrypted before they leave the server.

**Recommended: a backups-only Microsoft account (DR review S3).** About 10 minutes,
needs a computer once (the `rclone authorize` step):
1. signup.live.com: a new free Outlook address used only for this, a long password in your
   password manager, 2-step verification on (Microsoft Authenticator or SMS), and the
   recovery code printed and kept with your other backup codes.
2. On the server: `rclone config delete bigwins-onedrive`, then `bigwins onedrive` again,
   signing in with the **new** account on the computer.
3. Copy the last few archives across once (OneDrive web: share the folder "Big Wins server
   backups" from the old account to the new one, or just let the new one fill up over a
   few nights while the old copies remain).
4. In your main Microsoft account: account.microsoft.com > Privacy > Apps and services:
   remove the old "rclone" access.
If someone gets into your main Microsoft account they then cannot touch the backups, and
the server's token can no longer read your own files.

**A second off-site copy, not Microsoft (BF-D86, before real money)**: `bigwins offsite2`
connects a free Backblaze B2 bucket (10 GB free; the archives are about 20-100 MB each).
It is done **entirely from the phone** (a key id and a key typed in Termius, no browser
step), and the same encrypted archive and the same retention go there every night. It is
also the easiest restore source when your Microsoft account is not available (F4).

**Also in each archive (BF-D86)**: the deployed code as a git bundle (`code.bundle`, so a
restore does not need GitHub) and the private announcements archive (up to 500 MB; above
that it is left out and the Backups result says so). The **weekly restore test** now also
downloads the newest archive from OneDrive and checks it, so a OneDrive copy that cannot
be opened is paged.

The backups screen shows the recovery key's **fingerprint**; until the key with that
fingerprint has been shown (and saved) the screen and the inbox remind you. A new key is
never made silently while backups exist; a rotation is `bigwins new-backup-key`
(old backups then still need the old key). A restore test runs by itself every Sunday.

### C9. If the server dies

From a phone only: follow **F4** (no computer and no `rclone authorize` needed). The
steps below are the computer route.

You need: the recovery key (password manager), OneDrive access (or a copy of the backup
files) and a computer with Termius.

1. Order a new BinaryLane server and run the bootstrap and parts B1-B5 of this guide
   (Tailscale, Docker, the code in `/srv/asx-trader`, `bigwins` installed). You do not
   type the secrets again: they come back from the backup.
2. `apt install age rclone`, then `bigwins onedrive` (as in C8 step 4).
3. `bigwins restore` and paste the recovery key when asked. It fetches the latest backup
   from OneDrive, decrypts it and puts back the journal, settings (incl.
   `bfast.local.yaml`), the secret files and `.env`, the forward record, the price store,
   the trader's reports and the worker's notes, then starts everything.
4. `bigwins` > 11 (allow my phone), `sudo bigwins install-worker`, then check the app.
   IBKR: log in to the paper gateway again if it asks (IBKR Mobile).

---

### C10. The paper record and the announcements archive on this server (BF-D78, BF-D93)

Owner decision 24 Nov 2026: the only automated access to asx.com.au is the private
archive (the previous trading day's announcement list, the director-interest and
capital-raising notices and, since 25 Nov, the price-sensitive announcements of band C
companies and paper holdings: at most 60 a day, one request every 2 seconds, never in ASX
hours), plus ASIC's daily short positions. It is for your own use only, is never shared,
and feeds no strategy.

Owner decision 27 Nov 2026 ("move as much as we can to server and automated"): the paper
record and its daily jobs move from the research environment to this server, and the
archive moves with them. **You do not edit any file for this.** The whole move is in
`docs/RECORD_ON_SERVER.md` (one page, phone-friendly). In short:

1. `sudo bigwins record view on`: the app shows the real paper record from a read-only
   copy at once (no job runs here yet).
2. Sat 12 Dec: `sudo bigwins record seed`, then `sudo bigwins record shadow on`: the
   parallel week. The record's own job collects the announcements into the shadow's
   folder (the older host job `bigwins info-archive` stands down, so the ASX site is
   asked once a day from this server, never twice).
3. Sat 19 Dec: `sudo bigwins record cutover` (12 characters to compare). That command
   copies the archive's history into `/var/lib/bigwins/info`, sets `RECORD_DIR`, switches
   `info_archive.archive_enabled` on in `config/bfast.local.yaml`, runs the record-data
   checks, restarts the trader and the app, and makes a backup.

From then on Server > Health shows "Paper record: written on this server", the last day
stored and any missed trading days; each share's page shows its last 90 days of
headlines, director trades and the short position.

## D. First messages, approving in the app, and the controls

### D1. The daily rhythm (Sydney time, ASX trading days; `trader/bf_app.py` `DAY_JOBS`)

| Time | What happens | What you see (Inbox + alert) |
| --- | --- | --- |
| 13:05-16:25 | downloads the IBKR Flex statement (up to 5 tries) | a PAGE only if still missing at 16:25 |
| 14:30 | reminder | "Reminder: 1 order(s) of ... are not approved ..." if you have not approved |
| **15:20** | **approval deadline** | a later approval is refused; unapproved orders lapse, never sent |
| 15:45 | sends approved orders (LOC, into the closing auction) | "...-C: sent 1, not approved 0, held/rejected 0" |
| 16:20 | collects fills | |
| 16:30 | reconciles journal v IBKR to the unit and the cent | a PAGE only on a break |
| 17:35-22:05 | downloads the day's EODHD prices into the price store | a PAGE only if still missing at 22:05 (then no decision on stale prices) |
| 22:20 | month-end (or start) decision; in state EMG2 a share is sold only after 6 month-ends held and outside the top 40% of band C (sell rule C6, BF-D35) | "Decision ...: N orders" with an alert, for the **next** session |
| 22:25 | in FUND state only: the fund sweep (BF-D34) | "Fund sweep ..." to approve, only when needed |
| 22:45 | daily report | the report (every trading day) |

Your actions in the app are handled within a second or two (the trader wakes for them).

### D2. Approving in the app

When a decision has orders, you get an alert ("Decision 2026-11-30 (start...): 1
order(s)"). Tap it, or open the app: **Home** shows "N orders waiting for your approval".

1. Tap **✅ Approve all** (or open **See each order** to approve or veto one at a time).
2. The next screen shows exactly what will happen, e.g. "Approve all 18 orders of
   EMG2_18_PAPER-2026-11-30-R — total ≈ A$9,900", with each order (buy/sell, shares,
   limit, value). Check it.
3. Type the 6-digit code from your authenticator and tap **Approve all 18 orders**.
4. "Done: approved all 18 orders of ..." The approval is in the journal as yours
   (`app:<your log-in>`), and in the Inbox under "My actions".

The rules are exactly those of the old Telegram commands (same code check, each code
works once in the app or Telegram; the same 15:20 deadline; an old, refused or fully
approved batch is refused). If you do nothing, you get a reminder at 14:30 and at 15:45
the orders lapse: never sent later or automatically (L8). **Refuse** does the same with
the code and sends nothing of that batch. After 5 wrong codes in 15 minutes, code
actions lock for 15 minutes and you get a PAGE (Pause, Kill and Stop still work).

The start (D2 of the old guide still applies in substance): at a FUND start the canary
is one A200 order of about A$9,600; its PAGE line ("fund buy A200 ... above the L10
share-order limit") is expected. After the fill and a clean reconciliation: "Canary
filled and reconciled to the cent; no other start orders."

### D3. The controls (Home > Controls, or Server > Trader controls)

| Button | Code | What it does |
| --- | --- | --- |
| ⏸ Pause buying now | no, one tap | buys stop; registered sells go on |
| 🛑 Kill… | no, but a "Yes, KILL" screen | stops all new orders and cancels open orders at IBKR |
| ✋ Stop (L11)… | no, but a "Yes, STOP" screen | the loss rule's "owner says stop": buys stay paused, no automatic resume |
| ▶️ Resume… | yes | re-arms after pause, kill, stop or a halt |
| ✔️ Continue (L11)… | yes | your confirmation at loss-rule stage 3 (value below A$5,000) |
| 📊 Status | no | shows the safety level |
| Code changes: Confirm… / Undo… / Record a code change… | yes | the old `/idmap` and `/idmap_reject` (BF-D19, BF-D25) |
| Approve / Veto (Orders > a batch) | yes | one order; a sell cannot be vetoed alone |

The paper book's controls never stop the simulated twin or the random twins (BF-D16).

### D4. Alerts you may see

`PAGE` alerts need a look; `PAGE HIGH PRIORITY` needs you the same day: a reconciliation
break (`HALTED_INTEGRITY`: nothing is sent until you Resume after we have looked); the
loss-rule stages (A$7,000 check, A$6,000 buys paused, A$5,000 needs Continue); a missing
Flex statement; a code change to confirm; a refused LIC list; a job that failed; app code
actions locked.

### D5. The rest of the app

- **Home** starts with the **scoreboard** (BF-D75): Big Wins after *all* costs
  (brokerage and the spread are inside the account value; the fixed running costs and,
  if your tax rate is set, the estimated tax on realised gains are taken off) against
  the same money put into A200 on day one, in dollars and %, with one plain sentence
  ("Behind A200 by $X after all costs"). "What is counted" opens the sums. Then value,
  today, since start, drawdown from peak; the chart with 1M / 3M / 6M / All; the twin
  check; a red line if a scheduled job is late; and, folded away, **Research lines
  (information only)**: the other paper strategies, never ranked, each "mostly luck at
  this stage".
- **Holdings**: tap a share for its price since you bought it, gain, days held, why it
  was chosen (rank and scores at the decision) and where it stands on sell rule C6.
  **Tax**: per financial year, gains parcel by parcel, the 50% discount, losses carried
  forward, dividends, what selling today would mean, and an EOFY CSV for your accountant
  ("Estimate for your records — not tax advice. Paper account: no real tax.").
- **Orders**: every decision; tap one for each order's path (proposed, approved, sent,
  filled) with prices and brokerage.
- **Server**: the machine, containers, last log lines, heartbeat; Restart / Update / Re-run
  checks / Refresh prices (each with your code; restart and update during ASX hours need
  "Do it anyway").
- **Strategy** (Server > Strategy): the running version, release notes, results by
  version. When the server sees a new version on GitHub it shows "Strategy update
  available" (or "App-only update") with what changes, why and how it was tested.
  **Approve update…** (code) queues it. In `strategy.update_mode: immediate` (the default
  while paper) it is applied once the ASX is closed and no order is working, and that
  evening at 22:20 the trader makes an out-of-cycle decision with the new rules: its
  orders come to you for approval as usual. In `next_decision` mode the new rules start
  at the next month-end (not in the 24 hours before one unless you tick the override).
  **Go back to the previous version…** returns to the version before the last update.
  (Live later: daily strategy changes raise costs and tax; immediate mode on real money
  will need a deliberate config change.)
- **Server > Health** (BF-D77): each scheduled job against its timetable (daily run,
  price download, backup, restore test, announcements, previous-version twin), free
  disk (warning under 2 GB), backups, prices and EODHD calls used today, the
  announcements archive (last day, missed trading days), the outside alarms and the
  versions. One push per late or failed job.
- **Server > Running costs** (BF-D76): brokerage and fees, the modelled spread and the
  fixed costs by month, for this financial year and since the start, in $ and % of the
  account, with a one-line verdict. **Edit the amounts** sets the server, price-data and
  other costs a year (no code needed: nothing trades on them).
- **Server > Weekly digest** (BF-D79): every Friday after the 22:45 report a digest lands
  in the Inbox: the week against A200 after costs, the research lines (unranked), the
  data collected, the week's alerts and anything that needs you.
- **A share's page** (BF-D78): after the archive is switched on (C10), the last 90 days
  of announcements with capital raisings, trading halts and takeovers marked, director
  trades read from the notices (on-market buy or sell with number and value; option and
  rights issues are "not a buy"; anything unsure says "unclear") and ASIC's short
  position. "Not collected yet" until then.
- **Strategy > Did the last update help?** (BF-D80): after each strategy update the
  server also runs the previous version on paper; both simulated twins start from the
  update day with $10,000, and the screen shows which is ahead.
- **Settings** (gear): alerts, who may act, the go-live checklist items the app can see
  (including the disaster-recovery items of E2).
- **Server > Health, "You · owner presence"** (BF-D82): days since your last action, the
  day buying would pause by itself, and **I'm here**; "Phone and update safety" (the
  passphrase, Lock, update signatures, Claude remote); **Renewal dates** (the Flex token,
  your payment card, BinaryLane), edited like the running costs.

---

## E. What is left before go-live

**Timeline (owner decision, 22 Nov 2026):** paper trading runs until about the **end of
February 2027**; real money (A$10,000) starts around **March 2027**, not in December.

### E1. What I (Claude) do next, and what you see

1. **Reality spike on the paper gateway** (go-live item 1). Needs the server, the
   paper log-in and the Flex token from parts A-C. I check: LOC orders accepted and
   their cut-off (else the system switches to a 15:30 limit order,
   `execution.order_type: LMT`); funds from auction sales; finding an order again after
   a gateway restart; the account values IBKR reports; live v delayed quotes (A5); the
   Flex download against the real service and its timing; the order precautions (A4);
   the paper account's cash v the A$10,000 journal deposit (A3.2); that each container
   reads its secret files (B6); the daily price-store refresh (BF-D31) against the real
   EODHD service and its timing.
   `trader-bf deposit` / `kill` / `pause` / `status` act on the server's database, the
   same journal the running trader uses (BF-D30); they are run inside the trader
   container, e.g. `docker compose exec trader trader-bf status`. **You see**: one or two small paper orders I ask you to approve in
   the app, and a written result in `NEXT.md`.
2. **Start the runner**: record the A$10,000 paper deposits (paper book and twin:
   `docker compose exec trader trader-bf deposit --book EMG2_18_PAPER --amount 10000`,
   the same with `--book EMG2_18_SIM`; the command prints `journal: postgresql+psycopg://trader@db...`
   and the new cash, BF-D30), switch
   the compose command to `trader-bf run --start <start date>`. **You see**: the
   messages of part D from that evening (the trader is started with
   `bigwins start-trader <date>`).
3. **Five reconciled paper dry runs** (go-live item 2): five sessions with orders where
   the journal equals IBKR to the unit and the cent each day. Because the book will
   probably sit in A200 (one order, then none until the state changes), the dry run
   uses a **paper-only forced-state mode** (BF-D32; plan in E3 below) so those sessions
   carry real 18-share buys and sells, plus one session with the FUND switch. **You
   see**: approval requests (`/ok`), the 16:30 result and the 22:45 report each of those
   days; every decision message of a forced day says `state: EMG2 FORCED (paper dry
   run, BF-D32; the L15 rule says FUND ...)`.
4. **Kill drill from your phone** (go-live item 4): on a drill day, after the 15:45 send
   and before the auction (about 16:10), I ask you to tap **Controls > Kill > Yes** in the
   app. Expected within 60 seconds: "KILLED: no new orders; 1 open order(s) cancelled",
   and the order shows as cancelled in the IBKR Mobile app. Then **Controls > Resume** with
   your 6-digit code -> NORMAL. We also try **Pause**, **Stop**, **Continue** (only offered
   in an L11 stage-3 episode) and a wrong code once each.
5. **Heartbeat and backups** (items 9-10): the dead-man check-in is built (BF-D41;
   C5), five days without a miss; nightly encrypted off-site copy of the database and
   one restore drill; an outside port scan showing nothing open. **You see**: an email
   from healthchecks.io if the server ever goes quiet.

### E2. What you do

| # | Item | When |
| --- | --- | --- |
| - | **2-step verification** on every account: Google, Microsoft (OneDrive), GitHub, BinaryLane, Tailscale, IBKR, Claude, EODHD, healthchecks.io | now |
| - | **IBKR Mobile as the fallback**: install it, log in with the live user name, and practise once on paper: cancel an open order and sell one holding from the app (if the server is down on an order day, this is how you act) | before real money |
| - | **Rotate every secret seen during set-up** (chat screenshots, pasted values): EODHD token, Flex token, healthchecks URLs, the paper password; then `bigwins secret <name>` and restart | before real money |
| - | **Calendar reminders**: the Flex token's expiry date (IBKR shows it), card expiries for BinaryLane / EODHD / Claude, the Tailscale key expiry if you did not disable it (C5b) | now |
| - | **Recovery key saved** (Backups > Show recovery key, fingerprint matches) and a **restore drill on a second server, from the phone only, timed** (F4; fill in the timing table there) | before real money |
| - | **Passphrase set** (`bigwins secret app_passphrase`, C4); Health shows "Passphrase: set" | before real money |
| - | **Update signatures enforced** (F5b: the engineer's signing key on the server, `bigwins signing enforce`); Health shows "Update signatures: enforce" | before real money |
| - | **Signing enforced before live auto-updates** (BF-D90): on a live book the server applies NOTHING by itself until `bigwins signing enforce`; then app-only updates still wait 24 hours, outside ASX hours, after CI. Decide at go-live whether automatic app updates stay on (`bigwins autoupdate on`) or off (`bigwins autoupdate off`; the default on a live book is off) | before real money |
| - | **Second contact added** to the owner-presence check on healthchecks.io, and the emergency card (`docs/EMERGENCY_CARD.md`) filled in by hand and given to them (F8) | before real money |
| - | **Break-glass root password tested** in the BinaryLane web console (F3) | before real money |
| - | **IBKR trading-only user** for the live gateway (F7) | before real money |
| - | **Telegram token revoked** (BotFather `/revoke`), whether or not Telegram is on | before real money (now is better) |
| - | **Tailscale**: device approval on, SSH limited to your named devices (F10); a second off-site copy (`bigwins offsite2`, C8) | before real money |
| - | **Retail / wholesale resolved** with IBKR (retail), and your **TFN** given to IBKR | before funding |
| - | **Early-close days**: 24 and 31 December are not order days (orders go the next full session); nothing to do | info |
| - | **Live items** (a separate reviewed change, go-live item 6): a live Flex query and token; a separate live journal database; the dry-run book reset; `strategy.update_mode: next_decision` for live (immediate is refused for live); the order precautions also set for the live user in the gateway; the gateway image re-pinned; **a separate gateway user name for live** (IBKR: Settings > Users > add a user), whose 2FA IBKR asks you to re-approve about once a week on IBKR Mobile | before real money |
| 7 | Order precautions set on paper **and later on the live username**, Total Value Limit above A$10,000; photographed (A4) | now (paper); before real money (live) |
| - | If you keep Telegram on (appendix T): **fresh bot token** (BotFather `/revoke`, then a new `telegram_bot_token`; no screenshots): the set-up tokens of 21-22 Nov 2026 were seen in chat screenshots. With Telegram off, revoke the old token anyway | before real money |
| 8 | **A$10,000 deposited and settled** in the live account | before real money |
| 13 | Sign the risk statement; this is no more than 5% of your investable assets | before real money |
| 14 | Confirm the parcel method (FIFO, the default) with your accountant; after 30 June 2027 give them `trader-bf tax-report --fy 2026-27` (BF-D29) | before the first sale / after the FY |
| 15 | Be reachable by 15:20 on order days through April 2027 (orders need your approval in the app) | ongoing |
| - | Answer the open decisions in `NEXT.md` (staged loss-rule interpretations, HGO -> KAN, BF-D24 demerged shares) | before go-live |
| - | Market data: decide on the ASX Level 1 subscription (A5) | before real money |

### E3. The paper dry-run plan (BF-D32)

On the record's data the L15 state is FUND, so a normal start places one A200 order and
then nothing until the state changes: not enough for go-live item 2. For the dry run
only, `config/bfast.yaml` gets a `paper_dry_run` block that adds decisions on chosen
evenings with the band-trend state **forced to EMG2** (or left to the rule with `REAL`):

```yaml
paper_dry_run:                 # BF-D32: PAPER ONLY; remove it after the dry run
  until: 2026-12-18            # trader-bf run refuses to start after this date
  decisions:
    2026-12-01: EMG2           # start decision (trader-bf run --start 2026-12-01)
    2026-12-04: REAL           # the rule's own state (FUND): the FUND switch
    2026-12-11: EMG2           # forced EMG2 again: switch back into shares
```

(dates illustrative: S, S+3 and S+8 sessions; I set the real ones with you.) What
happens, each session approved by you with `/ok` and reconciled at 16:30:

| Session | Orders | Exercises |
| --- | --- | --- |
| S+1 | canary: one share buy | L6 canary, LOC fill, recon |
| S+2 | the other 17 share buys (A$500-A$800 each) | an 18-share buy flow, start-day limits |
| S+4 | all 18 shares sold; the one A200 buy when the sale money allows (BF-D28) | **the FUND switch**, an 18-share sell flow, the large paged fund order |
| S+5..S+7 | unfilled sells carried (L7), the A200 buy if it waited for funds | carries, auction-sale funds (O-2) |
| S+9 | A200 sold; the EMG2-18 picks bought as funds settle (D+1..D+4) | the switch back, a second 18-share buy flow |

That is at least five sessions with orders, plus the FUND switch. The twin and its 100
random twins take the same forced decisions, so the L13 comparison stays meaningful.

**Guards.** The block is accepted only with `mode: paper`, `allow_live: false` and a
`DU...` account (the config schema); the app refuses a forced state with any broker that
is not paper, and `trader-bf run` refuses the block after `until`. The forced state is
shown in every decision message and recorded in the journal (`bt:<day>` has
`forced_from`).

**Keep it out of the record.** Run the dry run in its own database so the official paper
book starts clean: in `deploy/.env` set `JOURNAL_DB=ledger_bf_dryrun`, then

```bash
docker compose exec db createdb -U trader ledger_bf_dryrun
docker compose up -d trader
docker compose exec trader trader-bf deposit --book EMG2_18_PAPER --amount 10000
docker compose exec trader trader-bf deposit --book EMG2_18_SIM --amount 10000
```

**After the dry run**: delete the `paper_dry_run` block, set `JOURNAL_DB=ledger_bf_paper`,
reset the paper account to A$10,000 cash with no holdings (A3.2), record the two
deposits in `ledger_bf_paper`, and start the official paper book
(`trader-bf run --start <date>`, normally a FUND start as in D2).

Real money needs, after all of the above, a separate reviewed code change that adds
the live gateway with its own guards (go-live item 6); nothing in this build can do it.

---

## F. Emergencies, from a borrowed device (disaster recovery, BF-D82..BF-D87)

Written for a phone, and for the day your own phone is gone: every step says where to tap
and works from a friend's phone, a hotel computer or a library. Keep a printed copy of
this part with your backup codes. **While the book is paper, nothing here can lose money**:
the worst outcome is a gap in the paper record and some keys to replace. The system fails
safe: no order is sent without your approval, all orders are day-only, and if you, the
phone, Tailscale or the server disappear, the book just holds what it has. Nothing is ever
sold automatically.

What you need for most of this, kept **away from the phone** (paper at home, plus a
sealed copy somewhere else):
- the **backup codes** of Google, Microsoft, GitHub, BinaryLane, Tailscale's sign-in
  account, IBKR, Claude, healthchecks.io (each site's "2-step verification > backup codes");
- your **password manager's** master password (and its own recovery kit);
- the **break-glass root password** of the server (F3);
- the **backup recovery key** (in the password manager; Backups > Show recovery key);
- the **authenticator seed** on paper (C4), if you made one;
- your **passphrase** (in your head).

### F0. Do these now (once, about an hour, from the phone)

1. **Screen locks**: a strong phone lock (6+ digits or a pattern you do not use
   elsewhere), and the app lock inside Termius (Settings > Security > PIN / fingerprint),
   your authenticator app and IBKR Mobile.
2. **Find My Device**: Android Settings > Google > Find My Device: on. Try it once at
   `android.com/find` from another device.
3. **2-step verification and backup codes on paper** for every account in the list above.
4. **Passphrase**: in Termius, `bigwins secret app_passphrase`, then menu 4 (restart). See C4.
5. **Owner-presence check with your second contact** (F8, 10 minutes).
6. **Tailscale**: device approval on and SSH limited to your devices (F10, 15 minutes).
7. **Break-glass root password** set and tested in the BinaryLane console (F3, 10 minutes).
8. **Second off-site copy** of the backups: `bigwins offsite2` (C8, 15 minutes).
9. **Renewal dates**: Server > Health > Renewal dates > Edit the dates (Flex token, your
   payment card, the BinaryLane card).
10. **Emergency card**: print `docs/EMERGENCY_CARD.md`, fill in the blanks **by hand**
    (names and numbers never go into the computer files), give it to your second person.
11. Telegram > @BotFather > `/revoke` the old bot token (one minute), whether or not you use
    Telegram.

### F1. Lost or stolen phone

Do these in order; each one cuts something off. The first three take about 15 minutes.

1. **Lock or erase the phone**: open `android.com/find`, sign in to Google (use a backup
   code if it asks for your phone), choose the phone, **Secure device** (locks it and shows
   a message) or **Erase device** if you will not get it back.
2. **Cut it off from the server**: open `login.tailscale.com/admin/machines`, sign in,
   find the phone, tap **...** > **Remove**. From this moment the phone cannot open the
   Big Wins app or Termius. (Device approval, F10, stops it being added back.)
3. **Your accounts**: change the Google password and sign out everywhere
   (`myaccount.google.com/security` > Your devices > Manage all devices > the phone >
   Sign out; then "Password"). Then the same for GitHub (`github.com/settings/sessions`),
   Microsoft (`account.microsoft.com` > Security > Sign out everywhere), Claude
   (claude.ai > Settings > log out of all devices) and BinaryLane.
4. **After real money**: phone IBKR (the number on your emergency card) and ask them to
   restrict the account until you have a new phone. IBKR Mobile was your second factor:
   see F7.
5. **On a new phone** (or a trusted computer), later, with Tailscale signed in again:
   - Termius: `bigwins new-totp`, scan the QR, delete the old entry (the thief's codes stop
     working);
   - if you think your passphrase was seen: `bigwins secret app_passphrase`;
   - new app keys: `cd /srv/asx-trader/deploy && rm secrets/app_proxy_key
     secrets/worker_job_key && bigwins update` (it makes new ones and restarts);
   - in the app: Settings > Alerts > **Turn alerts off on all devices**, then Turn on alerts
     on the new phone;
   - IBKR: register IBKR Mobile (IB Key) on the new phone (IBKR's help guides you).

What a thief with the **unlocked** phone could do before step 2: approve the orders the
strategy proposes, and Pause / Kill. With your **passphrase** set they cannot re-arm,
update, roll back, show the backup key or start Claude; with **Lock actions** on they
cannot even approve. Through Termius they would have the whole server: that is why the
phone lock and Termius's own PIN matter, and why step 2 comes first.

### F2. Lost authenticator (the phone is fine, or a new phone)

- If you kept the seed on paper (C4): add it again in the authenticator app (enter the
  key by hand: account `bigwins-trader`, the letters, time based).
- If not: in Termius `bigwins new-totp`, scan the new QR (C4). Nothing is approved in the
  meantime; unapproved orders lapse and the book holds.
- No Termius either? Use the BinaryLane console (F3) and type `bigwins new-totp` there.

### F3. Tailscale logged out, expired or its account locked: the break-glass console

Without Tailscale there is no app and no SSH: the server has no open port (B2). The way
in is BinaryLane's **web console**, which shows the server's screen in your browser, and
it needs a root password.

**Set it up now (DR review S1, 10 minutes):**
1. In Termius: `passwd root` and type a long password you can type on a phone keyboard
   (for example six random words with spaces removed). Store it in your password manager
   and on the paper kept with your backup codes (not on the emergency card).
2. Test it: BinaryLane website > Servers > your server > **Console** > log in as `root`
   with that password > type `tailscale status` > it lists your devices > type `exit`.
3. Write the date you tested it on your own paper. Test again every 6 months.

**When Tailscale is not working:**
1. BinaryLane > Servers > your server > Console > log in as root.
2. Type `tailscale up --ssh --force-reauth`. It prints a login link: type that link into
   the borrowed device's browser (or a phone browser), sign in to your Tailscale account
   and approve. The server is back on your tailnet.
3. If the phone app's address changed: `bigwins app` and then `bigwins login`
   (menu 9 and 11), then menu 4.
4. If your Tailscale **account** is locked: recover the account you sign in to Tailscale
   with (usually Google; use its backup codes), then repeat. Tailscale support:
   `tailscale.com/contact/support`. Meanwhile the trader keeps running, nothing is
   approved, unapproved orders lapse, the book holds.

### F4. Server dead, or BinaryLane suspended: restore from the phone only

Order of work and the time each step took in the drill (fill in the last column during
the **second-server drill**, a go-live item; do it once on paper, before real money):

| Step | What | Expected | Drill |
| --- | --- | --- | --- |
| A | New BinaryLane server | 10 min | |
| B | Tailscale on it (console) | 10 min | |
| C | Bootstrap and the code | 20 min | |
| D | The backup archive onto the server | 10-20 min | |
| E | `bigwins restore` | 15 min | |
| F | App, alerts, worker, checks | 15 min | |

**A. A new server**: BinaryLane > Create server: Singapore region, Ubuntu 24.04, 2 vCPU /
4 GB, 40 GB; choose **password** log-in (a phone has no SSH key) and type a new
break-glass root password (store it). If the account is suspended (card failure): pay the
balance or add prepaid credit first (Account > Billing), then the old server may simply
come back: check before rebuilding.

**B. Tailscale**: Console > log in as root > type (short on purpose, the console has no
paste):
```
curl -fsSL https://tailscale.com/install.sh | sh && tailscale up --ssh
```
Open the login link it prints on your phone, approve. In the Tailscale admin, approve
the new device (F10) and disable its key expiry (C5b); remove the dead server's machine.
From now on use **Termius** over Tailscale (paste works there).

**C. Bootstrap and the code**: on the phone open the GitHub app (or github.com) >
`bigwins-trader` > branch `bigwins-fast` > `deploy/server_bootstrap.sh` > copy its raw
text; in Termius paste it into `nano /root/bootstrap.sh`, save, `bash /root/bootstrap.sh`.
It prints a public deploy key: GitHub > the repository > Settings > Deploy keys > Add
(read-only), then clone as it says and run the bootstrap once more.
**If GitHub is not available**, skip the clone: do D first, then in Termius
```
age -d -i <(cat) /var/backups/bigwins/bigwins-YYYYMMDD-HHMMSS.tar.age | tar -xzf - -C /root code.bundle
git clone /root/code.bundle /srv/asx-trader
bash /srv/asx-trader/deploy/server_bootstrap.sh
```
(paste the recovery key when the first line waits, then press Ctrl-D). The archive holds
the exact code that ran (BF-D86). When GitHub is back, your engineer points the server
at it again (`git remote set-url origin` and the deploy key).

**D. The newest backup onto the server.** Choose the first route that works:
1. **Second off-site copy (B2)**, if you set it up (C8): `bigwins offsite2` and type the
   bucket's key id and key again (from your password manager). `bigwins restore` then
   finds the archives itself. No file handling at all.
2. **Termius SFTP (the main route)**: OneDrive app on the phone > "Big Wins server
   backups" > archives > the newest `bigwins-YYYYMMDD-HHMMSS.tar.age` > ⋮ > **Download**
   (it lands in Downloads). In Termius: `mkdir -p /var/backups/bigwins`, then open the
   host's **SFTP** view, go to `/var/backups/bigwins` and **upload** the file from
   Downloads.
3. **A share link**: OneDrive app > the archive > Share > Copy link (anyone with the link).
   In Termius: `bigwins fetch-archive '<the link>' bigwins-YYYYMMDD-HHMMSS.tar.age`. It
   keeps the file only if it is a real encrypted archive. **Delete the share link** in
   OneDrive afterwards (the archive is encrypted, but do not leave it shared).
OneDrive itself (`bigwins onedrive`) needs a computer once; reconnect it later at home.
Until then the nightly backups go to the server and to B2.

**E. Restore**: `bigwins restore`, answer y, **paste the recovery key** from the password
manager. It checks the key, the signed manifest and the journal's row counts before it
changes anything, puts back the journal, settings, secret files, `.env`, record, price
store, Flex inbox, the info archive and the worker's notes, checks out the backup's code
commit, and starts everything.

**F. Finish**: `bigwins app` (menu 9: the phone app on the new Tailscale name),
`bigwins login` (menu 11), `sudo bigwins install-worker`, menu 4. On the phone: open the
new app address, Add to Home screen, **Turn on alerts**, Server > Health (every job and
the heartbeat green), Backups > **Back up now** and **Restore test**. healthchecks.io needs
nothing (the URLs come back from the backup). IBKR: approve the paper gateway's log-in on
IBKR Mobile if it asks. Then `bigwins new-totp` only if the phone was lost too.

### F5. GitHub locked, or someone else pushing code

- **Locked out of GitHub**: nothing stops. The trader keeps running the code it has; there
  are no updates until you are back in; a restore uses the code inside the backup (F4 C).
  Recover with GitHub's backup codes (`github.com/login` > "Use a recovery code").
- **Someone else may have pushed code**: the app tells you about **every** new commit
  ("Update ready ... New code on GitHub (not applied)"). **Do not approve an update you did
  not expect.** Nothing that touches trading code, settings or the server changes until you
  approve it in the app (with your code and passphrase; app-only updates: see the next
  bullet), and
  with signing enforced (F5b) the server refuses code that your engineer did not sign.
  Then: change the GitHub password, check 2-step verification, and look at the repository's
  Settings: **Deploy keys** (exactly one, "sydney server", read-only), **Collaborators**
  (only you), and your account's Settings > Developer settings > tokens (delete any you do
  not know). Tell your engineer.
- The **"CI passed"** label on an update is information only: anyone who can push can
  fake it. The signature is what counts.
- **Automatic app updates (BF-D90)**: while paper, app-only commits (screens, documents,
  research pages) are applied **without your approval** after 1 hour, outside ASX hours,
  once GitHub CI has passed, even unsigned (warn mode). So if someone else may be pushing
  code: first `bigwins autoupdate off` (Termius) or Settings > Automatic app updates > Turn
  off (code), then the steps above. The new-code alert for such a commit says "New app
  update on GitHub ... applies by itself"; an update that needs you says "Update ready".

**What automatic updates can and cannot do (BF-D90).** *Can*: move the server to a newer
commit of `bigwins-fast` that only changes the app's screens (`trader/dashboard.py`,
`app_pages.py`, the other display-only files), `docs/`, `tests/` or `research/`; rebuild
the image; restart the app (dashboard or demo container); roll itself back and page you if
the app does not answer. *Cannot*: change trading code, the strategy or its settings (the
strategy hash and the settings hash cannot change: every input of both needs approval),
the config, database migrations, deploy scripts, the server worker or the auto-updater
itself, the timers, compose, the Dockerfile, dependencies, CI workflows or anything about
secrets; restart the trader; apply during ASX hours (09:30-16:30 Sydney on trading days),
apply a commit that is not a fast-forward, that CI failed, or (signing enforced) that your
engineer did not sign. **On a live book** it applies nothing until signing is enforced
(`bigwins signing enforce`), and then only commits it has known for 24 hours; it is off by
default when live. App-only display code that the trader process also loads (alerts, the
digest) takes effect only at the trader's next restart.

**F5b. The engineer's signing key (before real money; until then the server only warns).**
The server checks every update with `git verify-commit` against a public key kept on the
server in a root-only file (`/etc/bigwins/allowed_signers`, outside the repository and
outside GitHub), before it moves to the new code, both for the app's Approve update and
for `bigwins update`.
- *Engineer, once*: make an SSH signing key on a computer you control (not GitHub, not a
  shared or cloud machine; a hardware key such as a YubiKey is better):
  `ssh-keygen -t ed25519 -C bigwins-release -f ~/.ssh/bigwins_release`. Keep the private
  half there only, with a passphrase. Send the owner the **public** line
  (`~/.ssh/bigwins_release.pub`, starts `ssh-ed25519`); it is not secret.
- *Engineer, each release*: review the changes, then sign the commit the server will run
  (for example an empty release commit on top:
  `git -c gpg.format=ssh -c user.signingkey=~/.ssh/bigwins_release.pub commit --allow-empty -S -m "release: <what>"`)
  and push it. The server checks the newest commit only: a commit's signature covers the
  whole code at that point.
- *Owner, once (Termius)*: `bigwins signing key` and paste the public line; `bigwins
  signing status` says "warn". When a signed release has arrived and Server > Strategy
  shows "Signed", switch to `bigwins signing enforce`. From then on an unsigned update is
  refused with "not signed by the engineer's key". `bigwins signing warn` goes back.
- *Owner, in GitHub (web)*: Settings > Branches > add a rule for `bigwins-fast`: require
  signed commits, no force pushes, no deletion.
- *Live minimum age*: on a live book the server applies an update only after it has known
  that commit for 24 hours (0 on paper); a different number goes in
  `/etc/bigwins/update_min_age_hours`. That gives you a day to notice an alert you did not
  expect.

### F6. Google or Microsoft account taken over

- **Google** (probably also your Tailscale sign-in): recover it with the backup codes,
  change the password, Security > "Sign out of all other sessions", check the recovery
  phone and email. Then the Tailscale admin: Machines (remove anything you do not know;
  with device approval nothing new got in), Users. Then F1 step 5 (new authenticator seed,
  new app keys) if you think they reached the server. A passkey or a hardware key on Google
  makes this much harder (Security > Passkeys).
- **Microsoft** (OneDrive): they cannot read the backups (encrypted), but they could
  delete them; the server keeps 7 days and B2 keeps its own copies. Recover the account,
  change the password, Security > "Sign out everywhere", Privacy > Apps and services >
  remove "rclone", then reconnect later with `bigwins onedrive` (a computer). A
  backups-only Microsoft account (C8) keeps this away from your own files.

### F7. IBKR down, or you cannot reach IBKR (live)

- Every order is a **DAY** order: nothing is left working overnight. If the server or
  IBKR is down on an order day, nothing is sent and the book holds. Usually: do nothing.
- To act yourself: IBKR Mobile, or the Client Portal in a browser
  (`interactivebrokers.com.au` > Log in): cancel an open order or sell a holding. Practise
  it once on paper (E2).
- **If the phone is gone**: IBKR Mobile was your second factor (IB Key) for the Client
  Portal, so you cannot log in. Phone IBKR (the number on your emergency card; IBKR
  Australia client services, from the IBKR website's contact page) and ask them to
  verify you and reset the second factor, or to place / cancel an order for you.
- **The gateway's weekly approval**: the live gateway's user name asks for a confirmation
  on IBKR Mobile about once a week. If the phone is gone, the gateway stays logged out
  after the next weekly check: the trader cannot send anything, and the book holds. That is
  safe. It comes back when you approve on the new phone.
- **A trading-only user for the gateway (before real money)**: Client Portal > Settings >
  Users & Access Rights > add a user for the gateway with **trading rights only**: ASX
  stocks and ETFs; no deposits, withdrawals or transfers, no account management, no
  changes to users. Its password goes in `tws_password` (live, later). If that password
  ever leaks, nobody can move money with it.

### F8. Owner unreachable: the 14-day rule (owner decision, 24 Nov 2026)

What happens if you do nothing in the app for 14 days (BF-D82):
- day 10: a warning push to your phone ("buying pauses on ...");
- day 14: **buying pauses** by itself (safety level HALTED_BUYS; a stricter level such as
  KILLED is never lowered). **Nothing is sold automatically.** Sells, and the loss rule's
  wind-down, still need your approval as always; unapproved orders lapse;
- the same day the server stops its daily "I am here" ping to healthchecks.io, so your
  **second contact** gets an email the next day. They also get one if the whole server
  stops for about two days;
- when you are back: Controls > **Resume** with your code (and passphrase). That is the
  only way buying starts again.

"An action" is anything you do in the app that the server accepts: approve, refuse, Pause,
Status, a setting, Lock, or the **I'm here** button (Home, or Server > Health). Opening a
page does not count (any device on your tailnet could open one, and the app refreshes
itself). Server > Health shows the days since your last action and the date the pause
would start. In paper mode it runs the same way and the messages say "paper". The number
of days is `app.presence_days` (default 14) in `config/bfast.local.yaml`.

**Set up the second contact (10 minutes, phone):**
1. healthchecks.io (the same free account as C5) > **Add Check**. Name: "Big Wins owner
   presence". Schedule: **Simple**, period **1 day**, grace **1 day**. Save.
2. **Integrations** > Add Integration > **Email** > your second contact's email address >
   Save. They get a confirmation email and must click it once. (Also add your own email or
   the healthchecks app.)
3. Open the new check > Notifications: turn on that email for **this check only** (turn it
   off on your other checks, so the heartbeat does not email them).
4. Copy the check's ping URL (a secret). In Termius: `bigwins secret
   healthchecks_presence_url` and paste it. Nothing to restart. Server > Health shows
   "Owner-presence check: set up" and the last ping day.
5. Give your second contact the filled-in emergency card and tell them what the email
   means: "Either I have not used the app for two weeks, or the server has stopped. It is
   paper only: do nothing to the account; try to reach me."

### F9. A secret leaked (seen in a screenshot, a chat, a lost device)

| Secret | Where it is used | How to replace it (Termius unless said) |
| --- | --- | --- |
| authenticator seed (`totp_seed`) | 6-digit codes | `bigwins new-totp`, rescan |
| your passphrase (`app_passphrase`) | risky app actions | `bigwins secret app_passphrase`, menu 4 |
| IBKR paper password (`tws_password`) | the gateway | change it in the IBKR portal (paper user), then `bigwins secret tws_password`, menu 4 |
| Flex token (`ibkr_flex_token`) | daily statement | IBKR > Flex Web Service > generate a new token (the old one stops), `bigwins secret ibkr_flex_token`; update Renewal dates |
| EODHD token (`eodhd_api_token`) | price download | EODHD dashboard > API key > regenerate, `bigwins secret eodhd_api_token` |
| healthchecks URLs (`healthchecks_url`, `_backup_url`, `_daily_url`, `_presence_url`) | outside alarms | healthchecks.io: make a new check like the old one, delete the old one, `bigwins secret <name>` with the new URL |
| Telegram token (`telegram_bot_token`) | Telegram (optional) | @BotFather > `/revoke`; if used: `bigwins secret telegram_bot_token` |
| app keys (`app_proxy_key`, `worker_job_key`, `db_dashboard_password`) | inside the server | `cd /srv/asx-trader/deploy && rm secrets/<name> && bigwins update` (made again) |
| phone-alert key (`vapid_private_key`) | push alerts | `bigwins vapid`, menu 4, then Turn on alerts on each phone |
| database password (`db_password`) | the journal | cannot simply be retyped (B6 F17): ask your engineer |
| backup recovery key | opens the backups | `bigwins new-backup-key`, then show and save the new one (old backups still need the old key: keep both) |
| GitHub deploy key | the server reads GitHub | `ssh-keygen -t ed25519 -f ~/.ssh/bigwins_deploy -N '' ` (overwrite), replace it in GitHub > Settings > Deploy keys |
| OneDrive token (rclone) | backups | Microsoft > Apps and services > remove rclone; `bigwins onedrive` (computer) |
| B2 key | second copy | Backblaze > App keys > delete, add a new one, `bigwins offsite2` |
| break-glass root password | BinaryLane console | `passwd root`, test it (F3) |

Before real money, replace every secret that was ever seen in a chat or a screenshot
(E2).

### F10. Tailscale: device approval and SSH only from your own devices (DR review M3)

Tailscale is the front door: whoever is on your tailnet can open the app, and Tailscale
SSH gives your devices root on the server (`tailscale up --ssh`, B2). Two settings keep
strangers out even if they get into the account you sign in to Tailscale with.

**Write down (on your own paper)**: which account you sign in to Tailscale with (for
example your Google account) and that its recovery is that account's backup codes.

**1. Device approval**: Tailscale admin (`login.tailscale.com/admin/settings/device-management`)
> **Device approval** > on. From then on a new device joins only after you approve it in
the admin page (Machines > the device > Approve).

**2. SSH only from your named devices, with a re-check every hour**: Admin > **Access
controls** > the policy file. This example replaces the default "everyone reaches
everything" policy. Fill in the placeholders from Admin > Machines (each machine's
100.x.y.z address); keep the comments out if the editor complains:

```json
{
  // your machines, by their Tailscale addresses (Admin > Machines)
  "hosts": {
    "bigwins-server": "100.X.X.X",
    "owner-phone":    "100.Y.Y.Y",
    "owner-laptop":   "100.Z.Z.Z"
  },
  "acls": [
    // the Big Wins app (HTTPS) from any of your devices
    {"action": "accept", "src": ["autogroup:member"], "dst": ["bigwins-server:443"]},
    // SSH (Termius) only from these two devices
    {"action": "accept", "src": ["owner-phone", "owner-laptop"], "dst": ["bigwins-server:22"]}
  ],
  "ssh": [
    // Tailscale SSH as root: you sign in again once an hour
    {"action": "check", "src": ["autogroup:member"], "dst": ["autogroup:self"],
     "users": ["root", "autogroup:nonroot"], "checkPeriod": "1h"}
  ]
}
```

Save, then **test at once**: open the app on the phone, and Termius from the phone (it may
ask you to sign in to Tailscale in the browser: that is the hourly check). If something no
longer works, Access controls keeps the previous version (restore it), or use the
BinaryLane console (F3). After a new phone or laptop, add its address in `hosts`.
The code does not change `tailscale up --ssh`: Tailscale SSH is what lets you reach the
server from the phone at all, and these two settings are the safe way to narrow it.

---

## T. Appendix: Telegram (optional)

The app replaces Telegram. To use Telegram as well (or instead), set in
`config/bfast.local.yaml`:

```yaml
notify:
  channel: both                 # or telegram (Telegram only)
telegram:
  allowed_chat_ids: [123456789] # your chat id (T2)
```

and add the bot token secret (T1). `bigwins` then adds `deploy/docker-compose.telegram.yml`
by itself, and `check_secrets.sh` / `bigwins status` count the token. Restart the trader.

### T1. The bot

1. In Telegram, open **@BotFather** > `/newbot` > a name > a username ending in `bot`.
2. BotFather replies with the **token**: `bigwins` > 5) Add/replace a secret >
   `telegram_bot_token`. Do not forward the BotFather message to anyone.
3. Open a chat with your new bot and send `hello`.

### T2. Your chat id

Before the trader runs with Telegram on, open in **your own browser** (your token in
place of `<TOKEN>`) `https://api.telegram.org/bot<TOKEN>/getUpdates` and find
`"chat":{"id":123456789`: that is your chat id (not a secret).

### T3. The commands (`trader/approval.py`)

Only your chat id is obeyed. `<code>` is the 6-digit authenticator code (each code works
once, in Telegram or the app).

| Command | Needs a code | What it does |
| --- | --- | --- |
| `/ok <batch> <n> <code>` / `/ok <batch> all <code>` | yes | approves one / every order of the batch (before 15:20) |
| `/veto <batch> <n> <code>` | yes | drops one buy |
| `/refuse <batch> <code>` | yes | refuses the whole batch |
| `/approve <batch> <code>` | yes | approves a batch-mode batch |
| `/pause`, `/kill`, `/stop` | no | as the app's Pause, Kill, Stop |
| `/resume <code>`, `/continue <code>` | yes | re-arm; L11 stage-3 confirmation |
| `/idmap OLD NEW [RATIO] <code>`, `/idmap_reject OLD <code>` | yes | confirm / undo a code change |
| `/status`, `/menu` | no | safety level; the buttons |

**Buttons (BF-D38)**: approval messages carry ✅ Approve all, ❌ Refuse batch, one ✅ n per
order, 📊 Status and ⏸ Pause; `/menu` shows Status, Pause, Kill, Stop, Resume, Continue.
A tap that needs a code asks for it (send the code within 3 minutes); Kill and Stop need
a second confirming tap. Same rules as the typed commands and the app.


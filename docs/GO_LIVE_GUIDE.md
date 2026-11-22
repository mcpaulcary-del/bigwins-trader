# Go-live guide for the owner (EMG2-18 book, paper first)

Plain English, step by step, written to be done in one sitting (about 3 hours, plus
IBKR's waiting times). Accurate to branch `bigwins-fast` as of 19 Nov 2026; file names
are given so anything here can be checked against the code.

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
Telegram chat id are not secrets and go in `config/bfast.yaml`.

Contents: A. IBKR - B. Server - C. Telegram and authenticator - D. First messages and
commands - E. What is left before go-live.

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

## B. The server (BinaryLane, Sydney)

### B1. Order the server

BinaryLane > new server: **Sydney**, **2 vCPU / 4 GB RAM**, at least **40 GB** disk,
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
all; the compose file publishes none, `deploy/docker-compose.yml`). In BinaryLane you can
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

Compose needs **eight** files in `deploy/secrets/`, with exactly these names
(`deploy/docker-compose.yml` `secrets:`; the closed list in `trader/secrets.py`). A
missing file stops `docker compose up`.

Type each value yourself; `read -rs` keeps it off the screen and out of the shell
history:

```bash
cd /srv/asx-trader/deploy
mkdir -p secrets && chmod 700 secrets
put() { read -rsp "$1: " v; printf '%s' "$v" > "secrets/$1"; unset v; echo; }
put tws_password          # the IBKR PAPER password (used only by the gateway container)
put telegram_bot_token    # from @BotFather (part C1)
put ibkr_flex_token       # the Flex Web Service token (A6.2)
put ibkr_flex_query_id    # the query id number (A6.1)
put eodhd_api_token       # the EODHD data token (for the price-store refresh)
put healthchecks_url      # a healthchecks.io ping URL; type: none   until we set it up
openssl rand -hex 24 > secrets/db_password                   # database password, made here
python3 -c 'import base64,os;print(base64.b32encode(os.urandom(20)).decode())' > secrets/totp_seed
chmod 444 secrets/*        # see the note below
ls -l secrets              # eight files, none empty, all -r--r--r--
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
first as uid 10001 with no network, checks all eight files (present, non-empty, `444`,
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
| `telegram_bot_token` | trader | `trader/approval.py` `TelegramTransport` |
| `totp_seed` | trader | `trader/approval.py` `TotpVerifier` |
| `ibkr_flex_token`, `ibkr_flex_query_id` | trader | `trader/flex_pull.py` (read at each pull) |
| `eodhd_api_token` | trader (price-store refresh, BF-D31) | `trader/store_refresh.py` (read at each refresh) |
| `healthchecks_url` | dead-man heartbeat | not read yet (the heartbeat is still to build) |

### B7. Two settings in `config/bfast.yaml`

```bash
cd /srv/asx-trader && nano config/bfast.yaml
```

- `broker.account_id: DU1234567` (your paper id; the trader refuses anything not `DU...`);
- `telegram.allowed_chat_ids: [123456789]` (your chat id from C2; anyone else is
  silently ignored).

Change nothing else. `trader-bf run` refuses to start if either is empty
(`trader/bfast_cli.py` `cmd_run`).

### B8. First start (paper)

```bash
cd /srv/asx-trader/deploy
docker compose build && docker compose up -d
docker compose logs -f gw-paper        # wait for the login; Ctrl-C to stop watching
docker compose logs trader
```

The trader log should end with:

```
ok: book EMG2_18_PAPER, mode paper, cap A$10000
LIC list: frozen record list config/lic_list.csv (69 codes, sha256 af441f284b2d...)
```

If IBKR asks for a second factor at the paper log-in, approve it on IBKR Mobile.

At this point the trader **only checks its config and waits** (compose command
`trader-bf validate-config && exec sleep infinity`). It does not trade or message you
yet. I switch it to `trader-bf run --start <date>` after the reality spike (part E);
that is when the messages in part D begin.

---

## C. Telegram and the authenticator

### C1. The bot

1. In Telegram, open **@BotFather** > `/newbot` > a name (e.g. "Bigwins trader") > a
   username ending in `bot`.
2. BotFather replies with the **token**. Type it into the server (`put
   telegram_bot_token`, B6). Do not forward the BotFather message to anyone.
3. Open a chat with your new bot and send `hello` (the bot must have seen you once).

### C2. Your chat id

Before the trader runs (only one program may read the bot's messages), open this
address in **your own browser**, with your token in place of `<TOKEN>`:

`https://api.telegram.org/bot<TOKEN>/getUpdates`

Find `"chat":{"id":123456789` - that number is your chat id. Put it in
`telegram.allowed_chat_ids` (B7). It is not a secret.

### C3. The authenticator (second factor)

Some commands need a 6-digit one-time code from an authenticator app (`trader/approval.py`:
RFC 6238, SHA-1, 30 seconds, each code accepted once). On the server, show the seed you
created in B6 as a QR code and scan it with Google Authenticator, Microsoft
Authenticator or 1Password:

```bash
qrencode -t ansiutf8 "otpauth://totp/bigwins-trader?secret=$(cat /srv/asx-trader/deploy/secrets/totp_seed)&issuer=bigwins"
clear
```

The app now shows "bigwins-trader" with a 6-digit code. Keep a **paper backup** of the
seed (print the QR or write the letters down) somewhere safe: if you lose your phone,
nobody can re-arm the system or approve an order without it.

---

## D. First messages, the first approval, and the commands

### D1. The daily rhythm (Sydney time, ASX trading days; `trader/bf_app.py` `DAY_JOBS`)

| Time | What happens | What you see |
| --- | --- | --- |
| 10:30, 12:30 | reads your commands | replies to anything you sent |
| 13:05-16:25 | downloads the IBKR Flex statement (up to 5 tries) | a PAGE only if still missing at 16:25 |
| 14:30 | reminder | "Reminder: 1 order(s) of ... are not approved ..." if you have not approved |
| **15:20** | **approval deadline** | a later `/ok` is refused; unapproved orders lapse, never sent |
| 15:45 | sends approved orders (LOC, into the closing auction) | "...-C: sent 1, not approved 0, held/rejected 0" |
| 16:20 | collects fills | |
| 16:30 | reconciles journal v IBKR to the unit and the cent | a PAGE only on a break |
| 17:35-22:05 | downloads the day's EODHD prices, dividends and splits into the price store (hourly until it is there) | a PAGE only if still missing at 22:05 (then no decision on stale prices) |
| 22:20 | month-end (or start) decision; in state EMG2 a share is sold only after 6 month-ends held and outside the top 40% of band C (sell rule C6, BF-D35) | the decision message with orders for the **next** session |
| 22:25 | in FUND state only: a share the switch could not sell (e.g. halted) is offered again, and its cash goes into A200 (BF-D34) | "Fund sweep ..." with orders to approve, only when there is something to sell or invest |
| 22:45 | daily report | the report (every trading day) |

The trader also reads Telegram between jobs, so `/pause` and `/kill` act within
seconds, not at the next tick (`trader/scheduler.py`).

### D2. The start: one A200 order, which is also the canary

On the record's data the band-trend state is **FUND** (band 301-600 index below its
10-month average, BF-D28), so the book very likely starts in the A200 fund, not in
shares. Owner decision "Switch mechanics" 3: at a FUND start the **canary is the single
fund order** and nothing follows it.

**Evening of the start day (22:20)**, for example a start on 30 Nov 2026 (numbers
illustrative; the real message has the real prices):

```
Decision 2026-11-30 (start, canary first); list 3f9a1c0b7d2e; 1 order(s)
state: FUND (band 301-600 index 0.7670 below its 10-month average 0.8580, 2026-11-30)
LIC list: frozen record list config/lic_list.csv (69 codes, sha256 af441f284b2d...)
PAPER
Batch EMG2_18_PAPER-2026-11-30-C (per_order), decision 2026-11-30, execution 2026-12-01:
 1. BUY 64 A200 LOC lim 154.5 (ref 150.00, ~A$9600.00) BT_FUND_BUY [RISK_OK]
Reply /ok EMG2_18_PAPER-2026-11-30-C <n> <code> or /ok EMG2_18_PAPER-2026-11-30-C all <code> by 15:20.
PAGE fund buy A200 A$9888.00 above the L10 share-order limit (L15 band-trend switch, BF-D28)
```

How to read it: one buy of 64 A200 units, a limit of 3% above the reference close (the
L7 band), worth about A$9,600 at the close; about 3% of the cash stays until a later
top-up (BF-D28). The PAGE line is expected: it tells you this one order is above the
A$800 share limit by design. Every message from the paper book says PAPER.

**Next trading day, before 15:20**, approve it. Open your authenticator and send:

```
/ok EMG2_18_PAPER-2026-11-30-C 1 482913
```

(`1` is the order number; `all` approves every order of the batch.) Reply:

```
approved 1: BUY 64 A200
```

If you do nothing, at 14:30 you get a reminder, and at 15:45 the order lapses
(`LAPSED_NO_APPROVAL`): it is never sent later or automatically (L8).

**15:45** `EMG2_18_PAPER-2026-11-30-C: sent 1, not approved 0, held/rejected 0`

**16:30**, after the auction fill and a clean reconciliation:

```
Canary filled and reconciled to the cent; no other start orders.
```

(If the canary does not fill: `PAGE canary did not fill; the start stops here (L6).
Review before a new start.`)

**22:45** the daily report (every trading day; `trader/report.py`):

```
PAPER (IBKR paper account / simulation). No real money is at risk.
Not shown to beat the index.

EMG2_18_PAPER - 2026-12-01 - safety NORMAL
state: FUND (band 301-600 index 0.7670 below its 10-month average 0.8580, 2026-11-30)
Value A$9999.50 (cash A$399.50); capital in A$10000; result -0.01%
Brokerage to date A$6.90 (0.07% of capital)
Simulated twin A$9998.90 (difference A$0.60)
Simulated twin at the 50.0 percentile of 100 random twins (their median A$9998.90; L11 test (b) needs >= 10)
Holdings (1):
  A200           64 @ 150.00 = A$9600.00
Orders today (1):
  EMG2_18_PAPER-2026-11-30-A200-BUY-1 FILLED
Fills today (1):
  +64 A200 @ 149.9 comm A$6.90
```

In FUND state the twin and the 100 random twins hold the fund too, so they move
together. At each month-end the state is checked again; when the band index is back at
or above its average the message says `state: EMG2`, the decision sells A200 and buys
the EMG2-18 picks (up to about 18 orders, each A$500-A$800), and you approve each one
the same way (`/ok <batch> all <code>` approves them all at once).

### D3. The commands (exactly as in `trader/approval.py`)

Only your chat id is obeyed; anyone else is ignored. The command word is not
case-sensitive; copy the batch name exactly as the message shows it.
`<code>` is the 6-digit authenticator code (each code works once).

| Command | Needs a code | What it does | Reply |
| --- | --- | --- | --- |
| `/ok <batch> <n> <code>` | yes | approves order `n` of the batch (before 15:20 on its day) | `approved 1: BUY 64 A200` |
| `/ok <batch> all <code>` | yes | approves every order of the batch | `approved all 18 orders of <batch>` |
| `/kill` | no | stops all new orders and cancels open orders at IBKR (buys and sells) | `KILLED: no new orders; 1 open order(s) cancelled. /resume <code> to re-arm.` |
| `/pause` | no | stops buys; registered sells still go | `PAUSED: buys stop, registered sells proceed. /resume <code> to re-arm.` |
| `/stop` | no | the loss rule's "owner says stop" (L11 d): buys stay paused, no automatic resume; sells go on | `STOP recorded (L11 d): buys stay paused, sells go on. /resume <code> re-arms.` |
| `/continue <code>` | yes | your written confirmation at loss-rule stage 3 (value below A$5,000) | `confirmation recorded (L11 stage 3): buys resume at the next decision if the staged test passes` |
| `/idmap OLD NEW <code>` or `/idmap OLD NEW RATIO <code>` | yes | confirms a code change of a held share (e.g. `/idmap HGO KAN 482913`), optionally with a ratio (`1:10` = 1 new for 10 old) (BF-D19, BF-D25) | `code change HGO -> KAN confirmed` |
| `/idmap_reject OLD <code>` | yes | undoes a recorded code change | `code change HGO -> KAN undone: HGO is carried again at its last mark (review the holding)` |

Also implemented: `/resume <code>` (re-arms after `/pause`, `/kill`, `/stop` or a halt:
`re-armed: NORMAL`), `/status` (`safety NORMAL`), `/veto <batch> <n> <code>` (drops one
**buy**; a sell cannot be vetoed alone), `/refuse <batch> <code>` (refuses a whole
batch). Risk-reducing commands (`/kill`, `/pause`, `/stop`) never need a code; anything
that adds risk or re-arms does. A wrong or reused code gets `refused: ...` and changes
nothing.

The paper book's commands never stop the simulated twin or the random twins (BF-D16);
they keep the comparison going.

### D4. Pages you may see

Messages starting `PAGE` need a look; `PAGE HIGH PRIORITY` needs you the same day.
Examples (all in `trader/bf_app.py`): a reconciliation break (`PAGE EMG2_18_PAPER:
HALTED_INTEGRITY` with the difference - nothing is sent until you `/resume <code>`
after we have looked); the loss rule stages (A$7,000 check, A$6,000 buys paused, A$5,000
needs `/continue`; BF-D15); a missing Flex statement; a code change to confirm with
`/idmap`; a refused LIC list (BF-D21); a job that failed.

---

## E. What is left before go-live

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
   container, e.g. `docker compose exec trader trader-bf status`. **You see**: one or two small paper orders I ask you to approve with
   `/ok`, and a written result in `NEXT.md`.
2. **Start the runner**: record the A$10,000 paper deposits (paper book and twin:
   `docker compose exec trader trader-bf deposit --book EMG2_18_PAPER --amount 10000`,
   the same with `--book EMG2_18_SIM`; the command prints `journal: postgresql+psycopg://trader@db...`
   and the new cash, BF-D30), switch
   the compose command to `trader-bf run --start <start date>`. **You see**: the
   messages of part D from that evening.
3. **Five reconciled paper dry runs** (go-live item 2): five sessions with orders where
   the journal equals IBKR to the unit and the cent each day. Because the book will
   probably sit in A200 (one order, then none until the state changes), the dry run
   uses a **paper-only forced-state mode** (BF-D32; plan in E3 below) so those sessions
   carry real 18-share buys and sells, plus one session with the FUND switch. **You
   see**: approval requests (`/ok`), the 16:30 result and the 22:45 report each of those
   days; every decision message of a forced day says `state: EMG2 FORCED (paper dry
   run, BF-D32; the L15 rule says FUND ...)`.
4. **Kill drill from your phone** (go-live item 4): on a drill day, after the 15:45 send
   and before the auction (about 16:10), I ask you to send `/kill`. Expected within 60
   seconds: `KILLED: no new orders; 1 open order(s) cancelled. ...`, and the order shows
   as cancelled in the IBKR app. Then `/resume <code>` -> `re-armed: NORMAL`. We also try
   `/pause`, `/stop`, `/continue <code>` and a wrong code once each.
5. **Heartbeat and backups** (items 9-10): a dead-man check-in (the `healthchecks_url`
   file), five days without a miss; nightly encrypted off-site copy of the database and
   one restore drill; an outside port scan showing nothing open. **You see**: an email
   from healthchecks.io if the server ever goes quiet.

### E2. What you do

| # | Item | When |
| --- | --- | --- |
| 7 | Order precautions set on paper **and later on the live username**, Total Value Limit above A$10,000; photographed (A4) | now (paper); before real money (live) |
| - | **Fresh Telegram bot token** (BotFather `/revoke`, then `put telegram_bot_token` on the server; no screenshots): the set-up tokens of 21-22 Nov 2026 were seen in chat screenshots | before real money |
| 8 | **A$10,000 deposited and settled** in the live account | before real money |
| 13 | Sign the risk statement; this is no more than 5% of your investable assets | before real money |
| 14 | Confirm the parcel method (FIFO, the default) with your accountant; after 30 June 2027 give them `trader-bf tax-report --fy 2026-27` (BF-D29) | before the first sale / after the FY |
| 15 | Be reachable by 15:20 on order days through April 2027 (orders need your `/ok`) | ongoing |
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

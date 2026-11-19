# Bullet-proofing an IBKR end-of-day trading system: failure cases, controls and spec-ready requirements

Research date 2026-11-13. Claims marked **[U]** are unverified: they come from my background knowledge or a single secondary source. `www.interactivebrokers.com` could not be fetched from this session, so IBKR facts come from search snippets of IBKR docs and knowledge-base pages. Re-check them against the IBKR Australia pages before they become spec text.

## 1. Real failure cases and the control that would have prevented each

| Case | What happened | Preventing control |
|---|---|---|
| Knight Capital, Aug 2012 | New router code reached 7 of 8 servers. A reused flag woke dead "Power Peg" code on the eighth, which sent child orders without counting fills: about 4M executions and ~$460M lost in 45 minutes. The SEC found no second-person deploy review and inadequate erroneous-order controls. ([jrvarma](https://www.jrvarma.in/blog/Y2013/Knight-Capital.html), [The Register](https://www.theregister.com/2013/10/23/lone_sysadmin_caused_462_meeellion_wall_street_crash/)) | Single immutable image, with the version hash asserted at startup. Cumulative-fill check before any child order. Independent turnover and order-count breaker outside the strategy. No reused flags, dead code deleted. A kill switch that needs no diagnosis. |
| IBKR negative oil, Apr 2020 | IBKR's systems could not accept or display negative WTI prices. Customers could not exit, and IBKR took a loss of ~$88M, later revised above $100M. The CFTC found it failed to configure for negative prices. ([IBKR release](https://www.interactivebrokers.co.uk/en/general/about/mediaRelations/04-21-2020.php), [Bloomberg](https://www.bloombergquint.com/markets/oil-crash-busted-a-broker-s-computers-and-inflicted-huge-losses/), [CFTC order](https://cftc.gov/media/6421/enfinteractivebrokersorder092821/download)) | Never hold a contract into its expiry week. Use financially settled micros only, with an exclusion list. Do not assume the broker's risk engine works in extremes. |
| IBKR login outage, 5 Aug 2026 | Users could not log in during US hours while the status page showed green. ([Finance Magnates](https://www.financemagnates.com/forex/interactive-brokers-goes-dark-during-us-trading-hours/)) A [QuantRocket thread](https://support.quantrocket.com/t/interactive-brokers-major-outage/1503) describes Gateway timeouts in an earlier outage. | Treat "cannot connect" as a normal state: skip the cycle, never queue orders blindly. Keep protective orders resting at the exchange or IB server, not in the bot. Use own heartbeat, not the status page. |
| Gateway restart and weekly 2FA | Gateway restarts daily. After IBKR's weekend reset, the first login after 01:00 ET Sunday needs full 2FA, which IBC cannot bypass. ([IBKR Campus](https://www.interactivebrokers.com/campus/?p=259814), [IBC releases](https://github.com/IbcAlpha/IBC/releases)) A missed prompt means a dead system on Monday. | IBC `ColdRestartTime` set to a Sunday time when a human is awake in Sydney, plus `ReloginAfterSecondFactorAuthenticationTimeout=yes`. Telegram alert before and after. A "session authenticated" check hours before the first Monday order. |
| Bad prints, NYSE 3 Jun 2024 | A CTA price-band fault showed Berkshire A down 99.97%. About 40 symbols halted and trades were busted. ([Fortune](https://fortune.com/2024/06/04/warren-buffett-berkshire-hathaway-discount-deals-canceled/), [The Stack](https://thestack.technology/nyse-glitch-cause)) | Reject a bar whose move exceeds N×ATR without confirmation from a second source. Limit orders only, collared to the last validated close. Busted trades appear as execution corrections, so reconcile on T+1. |
| Split or dividend mis-adjustment **[U]** | Vendors routinely apply splits late, twice, or silently restate history. No single incident verified. | Store raw prices and corporate actions separately. Compare share count against broker positions daily; a ratio change such as ×2 or ×0.1 freezes the symbol. Run a nightly history diff. |
| ASX, 16 Nov 2020 | A Trade Refresh release failed on combination orders and the market closed for most of the day. IBM found it was not ready for go-live, and ASIC imposed licence conditions. ([Clifford Chance](https://cliffordchance.com/insights/resources/blogs/regulatory-investigations-financial-crime-insights/2021/08/installation-failure-australian-regulators-release-summary-of-asx-outage-review.html), [RBA](https://rba.gov.au/payments-and-infrastructure/financial-market-infrastructure/clearing-and-settlement-facilities/assessments/2020-2021/operational-incident-management.html)) | Exchange-state awareness: no closing print means no signal. The order stays unsent and the cycle is marked SKIPPED. |
| ASX, 19 Sep 2016 | A database hardware failure caused a bad failover. The market opened at 11:30, closed at 14:05, and some trades were cancelled. ([ASIC 16-454MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2016-releases/16-454mr-asic-reports-on-asx-equity-market-outage-in-september-2016/), [The Register](https://www.theregister.com/2016/09/19/australian_securities_exchange_offline/)) | Validate session completeness before trusting an end-of-day bar. Handle cancelled trades in reconciliation. |
| CME, 27–28 Nov 2025 | A chiller failure at CyrusOne CHI1 halted Globex and EBS for many hours; one outlet says over 10. ([The Trade](https://www.thetradenews.com/cme-group-markets-remain-halted/), [TechRepublic](https://www.techrepublic.com/article/news-global-futures-cme-data-center-cooling-failure/)) | Size futures so that 12 hours without an exit is survivable. Never roll on the last possible day. |
| FTX, Nov 2022 | Withdrawals paused, Chapter 11 filed on 11 Nov, shortfall of up to $8B, customer funds lent to an affiliate. ([The Block](https://www.theblock.co/post/186132/ftx-collapse-timeline-six-days-that-rocked-the-crypto-industry)) | Cap per-venue exposure to an amount you can lose entirely. Prefer regulated wrappers such as spot crypto ETFs or CME micro crypto futures through IBKR. Sweep excess funds off the venue. |
| 3Commas, Dec 2022 | About 100,000 customer API keys leaked and ~$20M was stolen through trades. ([Halborn](https://halborn.com/explained-the-3commas-breach-december-2022/), [Blockworks](https://blockworks.co/news/crypto-trading-bot-platform-3commas-rocked-by-critical-api-leak)) | Keys with no withdrawal rights, IP-allowlisted, and never held by a third-party SaaS. |
| Bybit, Feb 2025 | About $1.5B in ETH was stolen from the exchange. ([ForkLog](https://forklog.com/en/news/api-key-leaks-and-exchange-inaction-a-hapi-analysis-of-the-3commas-incident)) | Same venue cap. |
| PyPI compromises, 2026 | LiteLLM (24 Mar), Telnyx, PyTorch Lightning and the "Hades" `.pth` stealer campaign shipped credential stealers through stolen maintainer tokens. ([BleepingComputer](https://bleepingcomputer.com/news/security/popular-litellm-pypi-package-compromised-in-teampcp-supply-chain-attack), [Akamai](https://www.akamai.com/blog/security-research/2026/mar/telnyx-sdk-pypi-2026-teampcp-supply-chain-attacks), [TuxCare](https://tuxcare.com/?p=35098)) | Hash-pinned lockfile, a delay before adopting new releases, builds off the production host, default-deny egress so a stealer cannot exfiltrate. |
| Retail duplicate fills | A roughly 20-second IB disconnect left a stale order, and the bot's resubmit doubled the position. ([MultiCharts thread](https://www.multicharts.com/discussion/viewtopic.php?p=110226)) | Reconcile before acting after every reconnect. Deterministic `orderRef`. Never resend on timeout. |

## 2. IBKR-specific operational risks

**Order status**
- Duplicate `orderStatus` messages are common, and delivery is not guaranteed. ([IBKR order status](https://www.interactivebrokers.com/docs/tws-api/doc/order-management/order-status))
- `PendingSubmit` means sent but not acknowledged.
- `PreSubmitted` means accepted but not yet elected. This is normal for orders placed outside the session and for IB-simulated order types, so it is a legitimate overnight resting state for an end-of-day system.
- `PendingCancel` and `PreCancelled` can still fill.
- `Inactive` is documented as not transmitted. In practice it also appears on rejections, so treat it as "needs a human" and read the accompanying error. **[U]**
- `ApiPending` is not in the current documented status list, so handle unknown statuses generically. **[U]**
- Treat `execDetails` and `commissionReport` as the truth for fills, and `orderStatus` as advisory.

**Identifiers**
- `orderId` is scoped to an API client and must exceed all earlier IDs. `permId` is unique across the account. ([IBKR order reference](https://www.interactivebrokers.com/docs/tws-api/ref/order))
- Key the ledger on a self-generated intent ID carried in `orderRef`, then bind `permId` on the first callback.
- Use a fixed, unique `clientId` per process. Orders are only modifiable by the clientId that placed them; clientId 0 or the master client sees all. **[U]**
- Placing an order before connect-sync finishes yields error 103, duplicate order id. ([ib_insync issue](https://lightrun.com/answers/erdewit-ib_insync-duplicate-order-id))

**Reconnect and duplicates**
- After any disconnect, including the daily restart, block new orders until open orders, same-day executions and positions are re-pulled and matched to the ledger.
- An unmatched broker order raises an alert and is adopted or cancelled by rule. It is never ignored.
- The practitioner pattern is a reconciliation barrier. ([QuantConnect discussion](https://www.quantconnect.com/forum/discussion/21474/ibkr-on-qc-cloud-supported-reconciliation-barrier-after-reconnect-or-restart/))
- Error-code meanings **[U]**: 1100 connectivity lost; 1101 restored with data lost, so resubscribe; 1102 restored with data kept; 2103/2105 market or historical data farm broken; 2110 Gateway-to-server link broken.
- A farm disconnect does not mean order routing is down. A stale-quote guard is needed for any price-collared order.

**Pacing**
- The message limit is 50 per second, and three breaches terminate the session. Historical data is limited to 60 requests per 10 minutes, with identical requests at least 15 seconds apart (error 162). ([IBKR pacing](https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations), [IBKR Campus](https://www.interactivebrokers.com/campus/ibkr-quant-news/ibkr-api-historical-data-how-to-download-bars-without-pacing-violations/))
- Use a client-side token bucket and cache bars in Postgres.

**Partial fills**
- A DAY order may end partly filled. The state machine needs PARTIAL→EXPIRED, with the remainder re-derived from tomorrow's target-minus-actual and never carried forward as residual quantity.

**US account rules**
- The pattern-day-trader designation and $25k minimum were removed. The SEC approved FINRA's Rule 4210 change on 14 Apr 2026, effective 4 Jun 2026, replacing it with intraday-margin standards; broker rollout is phased. ([ThinkAdvisor](https://www.thinkadvisor.com/amp/2026/04/14/sec-approves-plan-removing-day-trading-limit-for-small-investors/), [tastytrade](https://tastytrade.com/learn/markets/industry/pattern-day-trading/)) IBKR Australia's implementation status is **[U]**.
- A cash account was never subject to the rule, and an end-of-day system does no day trades anyway.
- In a cash account, IBKR flags free riding when a position bought with unsettled funds is sold before settlement. The result is a 90-day "cash up front" restriction. ([IBKR KB 3101](https://ibkb.interactivebrokers.com/de/node/3101))
- US settlement has been T+1 since 28 May 2024 **[U – not re-sourced]**. ASX remains T+2, with T+1 only under discussion alongside CHESS replacement. ([ASX communique](https://www.asx.com.au/content/dam/asx/about/advisory-group/advisory-group-communique-20260211.pdf))
- Control: size buys from settled cash, not available funds, and keep a per-currency settlement calendar.

**FX**
- Since April 2024 cash accounts can buy foreign stock without holding the currency; IBKR converts at a settlement-adjusted rate. ([Mustachian Post forum](https://forum.mustachianpost.com/t/interactive-brokers-changes-in-currency-conversion-for-cash-accounts-in-april-2024/12498?page=2))
- Cash accounts cannot hold a negative non-base balance. Residual foreign balances are not auto-converted. ([IBKR KB 1458](https://ibkb.interactivebrokers.com/node/1458))
- Margin accounts silently create a foreign-currency loan instead.
- Control: explicit FX policy, a per-currency cash ledger, and an alert on any negative currency balance. Confirm IBKR Australia behaviour. **[U]**

**Futures**
- Physically delivered contracts must be closed before IBKR's contract-specific close-out deadline, tied to first position, first notice or last trading day. Otherwise IBKR liquidates without notice. Published dates are best-efforts only. ([IBKR Futures Close Out](https://ndcdyn.interactivebrokers.com/en/trading/futures-close-out.php))
- Prefer cash-settled micros (MES, MNQ). Roll at least 5 business days before the earlier of IBKR's deadline and first notice day. Micro gold (MGC) is deliverable. **[U]**
- Futures need a margin account at IBKR. **[U]**

**Margin**
- IBKR generally issues no margin calls. An account in deficit is liquidated immediately with market orders, across any position, and house margin can rise without notice. ([IBKR KB 1767](https://ibkb.interactivebrokers.com/article/1767), [IB UK risk disclosure](https://www.lynxbroker.com/media/doc/IBUK/1005_IBUK_DISCLOSURE_OF_RISKS_OF_MARGIN_TRADING_ENG.pdf))
- Control: keep an excess-liquidity cushion of at least 50% of net liquidation value. Run a what-if margin check before every order. Alert on cushion daily.

**Corporate actions**
- IBKR also liquidates around expiry and corporate actions (KB 1767).
- Detect by position-versus-ledger diff: splits, code changes, ETF terminations, and dividend-reinvestment or elective events. Freeze the symbol until a human confirms.

**Account-side limits**
- TWS and Gateway order "Precautionary Settings" (size, value, percent-from-market) and account-level restrictions give a third-party safety layer. Exact Risk Navigator limit features are **[U]**.
- IBC `ReadOnlyApi=yes` gives a hard no-trade mode. ([IBC config.ini](https://raw.githubusercontent.com/IbcAlpha/IBC/master/resources/config.ini))

## 3. Engineering practices

- **Reconciliation first.** The broker is the truth for positions, cash and fills. The ledger is the truth for intent. Every run starts by pulling broker state, diffing it, and proceeding only if clean.
- **Target-state orders.** Orders are computed as target minus broker-actual, so a rerun cannot double up.
- **Idempotent state machine with an outbox.** Write the intent row (deterministic key: date + account + symbol + strategy + sequence) in Postgres before any send. A single dispatcher sends and records `permId`. On a crash between write and acknowledgement, look the order up by `orderRef` and never resend blind. The key has a unique constraint.
- **Kill switches at three layers.**
  1. Application: a halt flag in the database and a Telegram `/halt`, checked before every send.
  2. Gateway: IBC `ReadOnlyApi`, or stop the container.
  3. Broker: log in from a phone and cancel all (which kicks the bot session), plus precautionary limits.
  - Starting is harder than stopping. Halt is sticky and needs explicit re-arming.
- **Circuit breakers.** These live in a separate module the strategy cannot bypass, and every trip latches halt:
  - price band against last validated close;
  - maximum order notional;
  - maximum daily turnover as a share of net liquidation value;
  - maximum position change per symbol;
  - maximum order count per day;
  - maximum daily loss;
  - stale-data guard.
- **Deployment.** One image digest, with the code hash logged per run. Sequence: paper account, then shadow mode on live data, then a canary with one user or minimum size for N sessions, then full. No deploys within 2 hours of a run.
- **Testing.**
  - Property-based tests (Hypothesis) on the state machine: no sequence of duplicated, reordered or dropped callbacks yields a ledger position different from the sum of executions, or a second send.
  - Deterministic replay of recorded IB event logs.
  - Fault injection: kill Gateway mid-order, drop the network after send, restart Postgres, skew the clock, fill the disk.
- **Time.** Use chrony. Store UTC. Take exchange calendars from a pinned library and cross-check them against IB contract trading hours every run. Refuse to trade if clock offset exceeds 2 seconds.
- **Backups.** Nightly encrypted `pg_dump` off the VM, plus WAL archiving if affordable. Run a quarterly restore drill onto a fresh VM, with rebuild time measured. The ledger is also rebuildable from IBKR Flex statements. **[U]**
- **Dependencies.** `uv` or pip-tools lock with hashes. Pin the Gateway, IBC and base-image digests. Upgrade deliberately through paper first.
- **Alerts for two amateurs.** Three classes only:
  - PAGE: act today (halt, reconciliation break, 2FA needed, margin cushion).
  - DAILY DIGEST: one message per run, always sent.
  - LOG: everything else.
  - Add a dead-man's switch on an external heartbeat monitor that alerts when the digest does not arrive. Each page links to a one-page runbook. Both users get pages and one acknowledges.
- **Service-level targets.** Run completed by deadline on at least 99% of sessions. Zero unreconciled breaks older than one session. Zero duplicate orders. Session authenticated before Monday open on at least 50 of 52 weeks. Restore under 2 hours.

## 4. Security

**Threat model**
- Credential-stealing dependency.
- VM compromise through an exposed port.
- Telegram account takeover.
- One user's mistake affecting the other.
- Lost 2FA phone.
- Provider-level snapshot access.

**Controls**
- **Broker identity.** A dedicated IBKR secondary username per account for the bot. IBKR states a second user cannot be given funding rights ([IBKR KB 1004](https://ibkb.interactivebrokers.com/node/1004/)); remove account-settings rights too. Enable withdrawal authorisers and bank-instruction locks where offered. IP restriction for logins is **[U]**; request it if available.
- **2FA.** The bot user keeps 2FA on IBKR Mobile, on a device the owner controls. Never weaken it. Document recovery.
- **Blast radius.** With no funding rights, an attacker's worst case is abusive trading, so the per-order and daily limits in section 3 are also security controls. Limits living only in the bot do not survive a VM compromise.
- **Two users.** Separate Gateway containers, API ports bound to an internal Docker network only (never 0.0.0.0), separate database roles and schemas, separate secrets, per-user halt.
- **Secrets.** Stored as files, not in the image or repository, encrypted at rest with sops/age. The decryption key lives on the VM only. Rotate on any dependency incident.
- **VM.** SSH keys only, no root login, no public ports (use WireGuard or Tailscale), unattended security upgrades, full-disk encryption, default-deny egress allowlist (IBKR hosts, Telegram, backup store, data vendor), non-root read-only containers, VNC to Gateway only via SSH tunnel.
- **Supply chain.** Hash-pinned installs. A 14-day quarantine on new versions. `pip-audit`. Build in CI rather than on production. Note `.pth` auto-run vectors. `ib_async` is a community fork, so pin it by hash.
- **Telegram.** Chats are not end-to-end encrypted. Restrict commands to allowlisted numeric user IDs and one chat. No secrets or full account numbers in messages. Destructive direction (halt) takes one step; re-arm and limit changes need a second factor such as a TOTP code or confirmation from the other user. No command exists to raise limits or place discretionary orders. A leaked bot token must be revocable within minutes.

## 5. New failure modes by market

**US ETFs**
- The regular close is 16:00 ET, which is 08:00 AEDT in the northern winter, 07:00 AEDT in the overlap weeks, and 06:00 AEST in the Australian winter.
- Next mismatch windows, derived from the statutory rules: 14 Mar – 4 Apr 2027 and 3 Oct – 7 Nov 2027. Schedule in `America/New_York`, never fixed Sydney cron.
- US holidays and 13:00 ET early closes. **[U – verify per-year calendar]**
- T+1 against ASX T+2 creates settled-cash mismatches when rotating between markets.
- The daily Gateway restart and Sunday 2FA must avoid both markets' order windows.
- Limit-up/limit-down halts and auction imbalances argue for limit-on-close or collared limit orders.
- AUD/USD conversion, W-8BEN and withholding tax, PRIIPs-style product restrictions. **[U]**
- Overnight US session liquidity is thin, so do not use it for exits.

**Futures**
- Roll logic errors (wrong contract month, a roll executed as two unhedged legs).
- Price limits and halts block exits.
- Margin is repriced daily and raised intraday without notice.
- Near-24-hour trading means gaps while the owners sleep.
- Continuous-contract back-adjustment errors in signals.
- Multiplier and tick-size mistakes: MES is $5 per point against ES at $50. **[U]** Assert contract details from the IB API before every order.
- Daily maintenance break at 16:00–17:00 CT. **[U]**
- Expiry and close-out as in section 2.

**Crypto**
- No close: "end of day" needs a defined UTC cut.
- Always-on trading means risk during every outage and upgrade.
- Venue insolvency and withdrawal freezes.
- API-key theft.
- Exchange-initiated socialised losses and auto-deleveraging on perpetuals. **[U]**
- Stablecoin de-peg, large wicks, rapidly changing symbol and precision rules, Australian tax-lot complexity.
- Recommendation: get crypto exposure only through IBKR-listed ETFs or CME micros until the rest is proven. A direct exchange needs a separate adapter and a hard venue cap.

## 6. Ranked risk register

L is likelihood and I is impact, each 1–5.

| # | Risk | L | I | Score | Control | Test |
|---|---|---|---|---|---|---|
| 1 | Sunday 2FA or restart missed, system dead or half-connected | 5 | 3 | 15 | IBC ColdRestart, pre-open auth check, page | Drill: let 2FA time out; expect a page and no orders |
| 2 | Duplicate order after reconnect or crash | 3 | 5 | 15 | Outbox, `orderRef`, reconciliation barrier | Kill the process between send and ack 100 times in paper; zero duplicates |
| 3 | Bad or mis-adjusted data drives a wrong trade | 4 | 4 | 16 | Two-source validation, bands, split detector | Replay with injected 99% print and unadjusted split; symbol frozen |
| 4 | Ledger and broker drift (corporate action, busted trade, manual trade) | 4 | 3 | 12 | Daily three-way reconciliation, freeze on break | Place a manual trade in paper; break detected next run |
| 5 | Runaway or logic bug after deploy | 2 | 5 | 10 | Independent breakers, canary, image hash | Mutant strategy requesting 10× size; blocked and halted |
| 6 | Credential or dependency compromise | 2 | 5 | 10 | No-funding user, egress allowlist, hash pins | Simulated outbound POST to unknown host fails; unpinned install fails CI |
| 7 | Futures expiry, forced liquidation, margin sweep | 2 | 5 | 10 | Roll T-5, cash-settled only, cushion alert | Calendar simulation over 3 years of expiries; never held inside window |
| 8 | DST or holiday scheduling error | 4 | 2 | 8 | Exchange-timezone scheduler, IB hours cross-check | Simulated clock across all four DST transitions and holidays |
| 9 | Settled-cash or free-riding restriction, negative FX balance | 3 | 3 | 9 | Settled-cash sizing, FX policy | Simulate a sell-then-buy rotation; buy sized to settled funds |
| 10 | IBKR, exchange or VM outage at run time | 4 | 2 | 8 | Skip-safe cycle, resting protective orders, dead-man alert | Block network during the run; SKIPPED plus page; next day converges |
| 11 | Data loss or failed restore | 2 | 4 | 8 | Off-site encrypted backup, drill | Quarterly restore to a clean VM within 2 hours |
| 12 | Telegram takeover or mis-command | 2 | 4 | 8 | ID allowlist, halt-only one-step commands | Command from unknown ID ignored and alerted |
| 13 | Alert fatigue, ignored page | 4 | 3 | 12 | Three classes, at most 2 pages a month target, digest | Monthly alert review; unacknowledged page escalates to the second user |
| 14 | Crypto venue failure or key theft | 2 | 5 | 10 | Venue cap, no-withdraw keys, or ETF wrapper | Key permission audit script; cap enforced in sizing |
| 15 | Pacing violation disconnect | 3 | 2 | 6 | Token bucket, bar cache | Burst test stays under 40 messages/s and 50 historical requests per 10 min |
| 16 | User-to-user cross-contamination | 2 | 4 | 8 | Per-user container, port, DB role | User A's database role cannot read schema B; order to wrong account is impossible by configuration |

## 7. Controls checklist

- [ ] Bot IBKR user has no funding or settings rights; withdrawal authoriser set.
- [ ] 2FA device and recovery documented.
- [ ] IBC configured: `ColdRestartTime`, `ReloginAfterSecondFactorAuthenticationTimeout=yes`, `ExistingSessionDetectedAction` chosen deliberately, `AcceptIncomingConnectionAction=reject` with trusted IPs.
- [ ] Gateway precautionary size and value limits set.
- [ ] Reconciliation barrier runs at start, after reconnect and after the run.
- [ ] Intent outbox with unique key; `orderRef` and `permId` bound.
- [ ] Independent breaker module with latching halt.
- [ ] Three kill switches documented and drilled.
- [ ] Data validation: two sources, bands, split detector, session-complete check.
- [ ] Exchange-timezone scheduling with IB trading-hours cross-check.
- [ ] Settled-cash sizing and per-currency ledger.
- [ ] Futures roll calendar and contract-spec assertion.
- [ ] Hash-pinned dependencies, pinned image digests, egress allowlist.
- [ ] Encrypted off-site backups and quarterly restore drill.
- [ ] Dead-man heartbeat, three alert classes, runbooks.
- [ ] Paper, shadow, canary promotion gate.
- [ ] Chaos and property-test suite in CI.
- [ ] Per-user isolation.

## 8. Spec-ready requirements

IDs use a new `BP-` prefix to avoid collisions with the existing spec.

| ID | Requirement | Acceptance test |
|---|---|---|
| BP-ORD-01 | Every order originates from a persisted intent with a unique deterministic key, written before transmission and carried in `orderRef`. | Inserting a duplicate key fails. Crash-injection between commit and send, and between send and ack, 100 iterations each in paper, yields exactly one broker order per intent. |
| BP-ORD-02 | Order state derives from executions; `orderStatus` is advisory; unknown statuses map to NEEDS_REVIEW and page. | Property test: for any permutation or duplication of callbacks, ledger filled quantity equals the sum of unique `execId` quantities. |
| BP-ORD-03 | No order is re-sent on timeout; resolution is by broker lookup. | Simulated ack loss leads to a lookup by `orderRef` and no second `placeOrder`. |
| BP-ORD-04 | Order quantity is target minus broker-actual at send time. | Re-running a completed cycle produces zero orders. |
| BP-REC-01 | A reconciliation barrier (open orders, executions, positions, cash per currency) must pass before any order after start or reconnect. | Forced disconnect mid-cycle: no `placeOrder` precedes RECON_OK in the event log. |
| BP-REC-02 | Any unexplained position, order or cash difference freezes the affected symbol or account and pages within 5 minutes. | A manual paper trade is detected next run; the symbol is excluded and a page is sent. |
| BP-RISK-01 | A breaker module independent of strategy code enforces per-order notional, price band against validated close, daily turnover percentage, per-symbol position change, order count and daily loss. A breach latches HALT. | Each limit breached by fixture gives zero orders sent and HALT persisted across restart. |
| BP-RISK-02 | HALT is settable in one step by either user at the app, gateway and broker layers. Re-arm needs explicit authenticated action and a clean reconciliation. | Drill each layer quarterly; time to halt under 2 minutes; re-arm refused while a break is open. |
| BP-RISK-03 | A pre-trade what-if margin check runs; reject if post-trade excess liquidity is below the configured share of net liquidation value (default 50% for futures accounts). | Fixture order breaching the cushion is rejected and logged. |
| BP-DATA-01 | A bar is tradable only if the session is complete, the timestamp is fresh, and the price agrees with a second source within tolerance or the move is within N×ATR. | Injected 99% print, stale bar and half-day bar each produce NO_TRADE for that symbol. |
| BP-DATA-02 | Raw prices and corporate actions are stored separately; a share-count ratio anomaly against the broker freezes the symbol. | Simulated 2:1 split not in the action table causes a freeze and page. |
| BP-SESS-01 | Gateway authentication state is verified at least 3 hours before each market's first order window; failure pages both users. | Expired session on Sunday yields a page; the Monday run is blocked with an explicit reason. |
| BP-SESS-02 | Restart and 2FA windows are configured outside all order windows for every enabled market. | Static config check in CI across both DST regimes. |
| BP-TIME-01 | Schedules are defined in exchange-local timezones and cross-checked against IB contract trading hours; clock offset over 2 seconds blocks trading. | Simulated dates 2027-03-14, 04-04, 10-03 and 11-07 give correct run times; skewed clock gives NO_TRADE. |
| BP-CASH-01 | Buy sizing uses settled cash per currency; no order may create a negative currency balance in a cash account. | Rotation fixture (sell on T, buy on T) sizes to settled funds only. |
| BP-FUT-01 | Only allowlisted contracts trade; contract multiplier, expiry and currency are asserted from the IB API before each order. | Wrong-multiplier fixture is rejected. |
| BP-FUT-02 | Positions roll or close at least 5 business days before the earlier of the IBKR close-out deadline, first notice day and last trading day; no new entries inside that window. | Three-year calendar simulation shows zero holdings inside the window. |
| BP-CRY-01 | Direct crypto venue exposure is capped at a configured percentage of total equity; API keys are verified to lack withdrawal permission at startup. | A key with withdrawal permission makes the adapter refuse to start. |
| BP-SEC-01 | Bot broker credentials have no funding or settings rights; verified and recorded quarterly. | Checklist evidence, such as a screenshot or permission export, is stored. |
| BP-SEC-02 | No inbound public ports except the VPN; outbound traffic is restricted to an allowlist. | External port scan shows none open; `curl` to a non-allowlisted host fails from every container. |
| BP-SEC-03 | All Python dependencies are installed with hash verification from a lockfile; images are referenced by digest; no version younger than 14 days without an override. | CI fails on an unpinned or unhashed dependency. |
| BP-SEC-04 | Telegram commands are accepted only from allowlisted user IDs and chat; re-arm and limit changes need a second factor; no secrets appear in messages. | Spoofed-ID test is rejected and alerted; log scan finds no secrets. |
| BP-SEC-05 | Each user has an isolated Gateway container, API port, database role and schema, and secrets. | Cross-role SELECT is denied; user A's process cannot reach B's API port. |
| BP-OPS-01 | Every scheduled run emits exactly one digest (OK, SKIPPED or HALTED, with reason); an external dead-man monitor pages if it is absent 30 minutes after the deadline. | Suppressed run leads to an external page. |
| BP-OPS-02 | Encrypted off-site backup runs daily; a restore drill to a clean VM each quarter meets a recovery time of 2 hours or less and data loss of 24 hours or less. | Drill record with timings is stored. |
| BP-OPS-03 | Promotion gate: at least 10 paper sessions and 5 shadow sessions with zero reconciliation breaks, then a canary at minimum size for 5 sessions. | Release checklist is enforced by a deploy script flag. |
| BP-OPS-04 | Every PAGE alert links to a runbook; the page budget is 2 per month, with a monthly review. | Alert catalogue lint: no page without a runbook URL. |
| BP-TEST-01 | CI includes property-based state-machine tests, deterministic replay of recorded IB sessions, and the fault-injection suite: Gateway kill, network drop, database restart, disk full, clock skew. | All pass; the replay output hash is stable across runs. |

**Open items to verify before freezing the spec:** IBKR Australia specifics (cash-account FX behaviour, intraday-margin rollout after the PDT change, futures account-type requirement, IP restrictions, Flex-based ledger rebuild); the exact error-code semantics; and per-contract close-out dates.
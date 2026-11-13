"""Operational constants (spec §0: timeouts, retention, validation statistics).

Strategy, sizing, risk and execution *numbers* are NOT here: they live only in
config/common.yaml (§18, "the YAML wins"). This module holds operational
constants that the spec deliberately keeps out of the YAML.
"""

from __future__ import annotations

from datetime import time
from decimal import Decimal
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

# --- Time (SYS-14) -------------------------------------------------------
ASX_TZ_NAME: Final = "Australia/Sydney"
ASX_TZ: Final = ZoneInfo(ASX_TZ_NAME)

# Normal ASX close (closing single price auction) and half-day close (§5).
NORMAL_CLOSE_TIME: Final = time(16, 10)
HALF_DAY_CLOSE_TIME: Final = time(14, 10)

# --- Money (SYS-13, §12: NUMERIC(18,4) in AUD) ----------------------------
MONEY_PRECISION: Final = 18
MONEY_SCALE: Final = 4
MONEY_QUANTUM: Final = Decimal("0.0001")
CENT: Final = Decimal("0.01")
# Prices are stored at the same scale as money.
PRICE_PRECISION: Final = 18
PRICE_SCALE: Final = 4

# --- Logging (MON-03) -----------------------------------------------------
LOG_RETENTION_DAYS: Final = 90
ACCOUNT_VISIBLE_DIGITS: Final = 3
REDACTED: Final = "***REDACTED***"

# --- Config and secrets (OPS-10, OPS-11, §14) -----------------------------
CONFIG_DIR_DEFAULT: Final = Path("config")
COMMON_CONFIG_NAME: Final = "common.yaml"
# Docker secrets mount point; the only place secrets are read from (OPS-11).
SECRETS_DIR_DEFAULT: Final = Path("/run/secrets")
# Deployed-code SHA file baked into the image at build time (no .git in image).
BUILD_SHA_FILE: Final = Path(__file__).with_name("_build_sha.txt")
GIT_SHA_LENGTH: Final = 40
SHA256_HEX_LENGTH: Final = 64
# Owner-only permissions for per-user config files (§18 comment): no group/other bits.
USER_CONFIG_FORBIDDEN_MODE_BITS: Final = 0o077

# --- Calendar (OPS-05) ----------------------------------------------------
# Number of trading days of tolerance when an event date is an estimate is a
# config value (filters.blackout.estimate_widen); nothing calendar-related is here.

# --- Retention (TAX-08, MON-03) -------------------------------------------
RECORD_RETENTION_YEARS: Final = 7

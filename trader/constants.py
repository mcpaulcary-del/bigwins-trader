"""Operational constants (spec v2.10).

Strategy, sizing, risk and execution *numbers* are NOT here: they live only in
config/common.yaml (§18: "If the text and the YAML differ, the YAML wins").
This module holds operational constants that the spec keeps out of the YAML.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

# --- Time (SYS-14) -------------------------------------------------------
ASX_TZ_NAME: Final = "Australia/Sydney"
ASX_TZ: Final = ZoneInfo(ASX_TZ_NAME)

# Venue timing (auctions, early close, close availability) is config
# (`venue.XASX`, §4/§18), never a constant and never taken from a library.

# --- Money (SYS-13, §12: NUMERIC(18,4) in AUD) ----------------------------
MONEY_PRECISION: Final = 18
MONEY_SCALE: Final = 4
MONEY_QUANTUM: Final = Decimal("0.0001")
CENT: Final = Decimal("0.01")
# Prices are stored at the same scale as money.
PRICE_PRECISION: Final = 18
PRICE_SCALE: Final = 4

# --- Logging (MON-03) -----------------------------------------------------
# Default only; the runner passes `ops.log_retention_days` from common.yaml.
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

# --- Market data (§6, DAT-18) ---------------------------------------------
# Root of the per-user raw-file tree: data/raw/{source}/{fetch_date}/...
DATA_DIR_DEFAULT: Final = Path("data")
# Venue key of the ASX in the `calendar` table (§12: (venue, date) PK).
XASX: Final = "XASX"

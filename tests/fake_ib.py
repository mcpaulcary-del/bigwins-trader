"""The mock gateway now lives in the package (used by the dry-run harness)."""

from trader.broker.mock_gateway import MockGateway as FakeIB

__all__ = ["FakeIB"]

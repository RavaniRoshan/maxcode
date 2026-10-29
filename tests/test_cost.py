# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for token and cost accounting."""

import pytest

from maxcode.config import Pricing
from maxcode.cost import CostMeter


def test_cap_is_reported() -> None:
    meter = CostMeter(
        {"m": Pricing(input_per_mtok_usd=1.0, output_per_mtok_usd=2.0)},
        cap_usd=0.01,
    )
    meter.add("m", 1000, 1000)
    assert not meter.cap_reached
    assert meter.total_usd == pytest.approx(0.003)
    meter.add("m", 10000, 10000)
    assert meter.cap_reached
    assert meter.total_usd >= 0.01


def test_unpriced_model_returns_tokens_only() -> None:
    meter = CostMeter({}, cap_usd=None)
    meter.add("unknown", 10, 20)
    assert meter.tokens_in == 10
    assert meter.tokens_out == 20
    assert meter.total_usd == 0.0
    assert meter.partial is True


def test_missing_counts_are_partial() -> None:
    meter = CostMeter({"m": Pricing(input_per_mtok_usd=1.0, output_per_mtok_usd=1.0)}, cap_usd=1.0)
    meter.add("m", None, 5)
    assert meter.tokens_in == 0
    assert meter.tokens_out == 0
    assert meter.partial is True
    assert not meter.cap_reached

# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Token and cost accounting for one run."""

from maxcode.config import Pricing


class CostMeter:
    """Accumulate token counts and cost, and report when a cap is reached."""

    def __init__(
        self,
        pricing: dict[str, Pricing],
        cap_usd: float | None = None,
    ) -> None:
        self._pricing = pricing
        self._cap = cap_usd
        self._tokens_in = 0
        self._tokens_out = 0
        self._total_usd = 0.0
        self._partial = False
        self._cap_reached = False

    def add(self, model: str, input_tokens: int | None, output_tokens: int | None) -> None:
        """Add one provider or engine call. None means the count was not reported."""
        if input_tokens is None or output_tokens is None:
            self._partial = True
            self._check_cap()
            return
        self._tokens_in += input_tokens
        self._tokens_out += output_tokens
        price = self._pricing.get(model)
        if price is None:
            self._partial = True
        else:
            self._total_usd += (
                input_tokens * price.input_per_mtok_usd / 1_000_000
                + output_tokens * price.output_per_mtok_usd / 1_000_000
            )
        self._check_cap()

    @property
    def tokens_in(self) -> int:
        """Total input tokens across priced and unpriced calls."""
        return self._tokens_in

    @property
    def tokens_out(self) -> int:
        """Total output tokens across priced and unpriced calls."""
        return self._tokens_out

    @property
    def total_usd(self) -> float:
        """Total cost in USD, excluding calls without pricing."""
        return self._total_usd

    @property
    def partial(self) -> bool:
        """True when at least one call lacked a count or a price."""
        return self._partial

    @property
    def cap_usd(self) -> float | None:
        """The configured cap, if any."""
        return self._cap

    @property
    def cap_reached(self) -> bool:
        """True when the accumulated cost has reached the cap."""
        return self._cap_reached

    def _check_cap(self) -> None:
        if self._cap is not None and self._total_usd >= self._cap:
            self._cap_reached = True

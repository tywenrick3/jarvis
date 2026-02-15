"""Lightweight per-session token and cost tracker."""

from dataclasses import dataclass, field
from config import BudgetConfig
from models import ChatResult

# Approximate pricing per 1M tokens (input, output) — update as needed
PRICE_TABLE: dict[str, tuple[float, float]] = {
    "claude-opus-4-6":              (15.00, 75.00),
    "claude-sonnet-4-5-20250929":   (3.00,  15.00),
    "claude-haiku-4-5-20251001":    (0.80,   4.00),
    "gpt-4o":                       (2.50,  10.00),
    "gpt-4o-mini":                  (0.15,   0.60),
    "gpt-5.1":                      (1.25,  10.00),
}


@dataclass
class UsageTracker:
    budget: BudgetConfig
    total_input: int = 0
    total_output: int = 0
    _warned: bool = field(default=False, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output

    @property
    def over_budget(self) -> bool:
        return self.total_tokens >= self.budget.max_tokens_per_session

    def record(self, result: ChatResult, model_name: str | None = None) -> None:
        """Record usage from a ChatResult and print warnings if near budget."""
        self.total_input += result.usage.input_tokens
        self.total_output += result.usage.output_tokens

        pct = (self.total_tokens / self.budget.max_tokens_per_session) * 100
        if pct >= self.budget.warn_at_percent and not self._warned:
            print(f"\n⚠ Token budget {pct:.0f}% used ({self.total_tokens:,} / {self.budget.max_tokens_per_session:,})")
            self._warned = True

        if self.over_budget:
            print(f"\n🛑 Session token budget exceeded ({self.total_tokens:,} / {self.budget.max_tokens_per_session:,})")

    def summary(self, model_name: str | None = None) -> str:
        """Return a human-readable usage summary."""
        lines = [
            f"Tokens: {self.total_input:,} in + {self.total_output:,} out = {self.total_tokens:,} total",
        ]
        if model_name and model_name in PRICE_TABLE:
            inp_price, out_price = PRICE_TABLE[model_name]
            cost = (self.total_input / 1_000_000 * inp_price) + (self.total_output / 1_000_000 * out_price)
            lines.append(f"Estimated cost: ${cost:.4f}")
        return "\n".join(lines)

"""A tiny bank account model."""


class Account:
    """A single bank account."""

    def __init__(self, balance: float = 0.0) -> None:
        if balance < 0:
            raise ValueError("balance must not be negative")
        self.balance = balance

    def deposit(self, amount: float) -> None:
        """Add money to the account."""
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Remove money from the account."""
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance += amount

    def statement(self) -> str:
        """Return a one-line balance statement."""
        return f"balance: {self.balance:.2f}"

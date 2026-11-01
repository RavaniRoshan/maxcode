import pytest
from bank import Account


def test_exact_balance_withdrawal() -> None:
    account = Account(50.0)
    account.withdraw(50.0)
    assert account.balance == 0.0


def test_multiple_withdrawals() -> None:
    account = Account(100.0)
    account.withdraw(10.0)
    account.withdraw(20.0)
    assert account.balance == 70.0


def test_deposit_and_withdraw() -> None:
    account = Account(10.0)
    account.deposit(40.0)
    account.withdraw(25.0)
    assert account.balance == 25.0


def test_negative_withdrawal_rejected() -> None:
    with pytest.raises(ValueError):
        Account(10.0).withdraw(-1.0)


def test_overdraft_rejected() -> None:
    with pytest.raises(ValueError):
        Account(10.0).withdraw(11.0)

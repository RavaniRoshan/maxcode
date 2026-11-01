from bank import Account


def test_withdrawal_reduces_balance() -> None:
    account = Account(100.0)
    account.withdraw(30.0)
    assert account.balance == 70.0


def test_statement_after_withdrawal() -> None:
    account = Account(100.0)
    account.withdraw(30.0)
    assert account.statement() == "balance: 70.00"

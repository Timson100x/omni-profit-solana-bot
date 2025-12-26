from src.monitoring import notifier


def test_telegram_noop():
    # With no credentials set, send_telegram should be a noop and return False
    assert notifier.send_telegram('hello') is False


def test_discord_noop():
    assert notifier.send_discord('hello') is False


def test_notify_critical_no_fail():
    # notify_critical should not raise even if channels missing
    notifier.notify_critical('critical!')
    assert True

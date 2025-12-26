import pytest
import requests
from unittest.mock import patch, Mock

from src.trading.jupiter_client import _request_with_retries, ping_jupiter


def test_request_with_retries_success():
    m = Mock()
    m.raise_for_status.return_value = None
    m.status_code = 200
    with patch('src.trading.jupiter_client.requests.get', return_value=m) as g:
        r = _request_with_retries('http://example', 1, 3, 0.01)
        assert r is m
        g.assert_called()


def test_request_with_retries_fail():
    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError('fail')
    with patch('src.trading.jupiter_client.requests.get', side_effect=_raise):
        r = _request_with_retries('http://example', 0.1, 2, 0.01)
        assert r is None


def test_ping_jupiter_unreachable():
    with patch('src.trading.jupiter_client._request_with_retries', return_value=None):
        assert not ping_jupiter()


def test_ping_jupiter_ok():
    m = Mock()
    m.status_code = 200
    with patch('src.trading.jupiter_client._request_with_retries', return_value=m):
        assert ping_jupiter()

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import address


@pytest.mark.parametrize('db_values,mi_values,expected', [
    ({'pattern': '^123', 'context_info': 'office'}, {'pattern': '^123', 'context_info': 'office'}, True),
    ({'pattern': '^456'}, {'pattern': '^123'}, False),
    ({'context_info': 'new'}, {'context_info': 'old'}, False),
    ({'pattern': None}, {'pattern': '^123'}, False),
    ({'context_info': ''}, {'context_info': 'old'}, False),
    ({'pattern': '', 'context_info': None}, {'pattern': None, 'context_info': ''}, True),
])
async def test_address_requires_reload_when_content_differs(monkeypatch, db_values, mi_values, expected):
    base = {'grp': 1, 'ip': '192.0.2.0', 'mask': 24, 'port': 0, 'proto': 'any'}
    monkeypatch.setattr(address.table_crud, 'fetch', AsyncMock(return_value=[base | {'id': 1} | db_values]))
    monkeypatch.setattr(address.mi, 'call', AsyncMock(side_effect=[
        {'Partitions': []},
        {'Partitions': [{'name': 'default', 'Destinations': [base | {'mask': '255.255.255.0'} | mi_values]}]},
    ]))
    result = await address.list_addresses(SimpleNamespace(mi_host='localhost', mi_port=8888))
    assert result['rows'][0]['in_memory'] is expected
    assert result['rows'][0]['partition'] == 'default'
    assert result['mi_available'] is True
    assert result['memory_only'] == []


@pytest.mark.parametrize('error,expected', [(None, False), ('MI unavailable', None)])
async def test_missing_or_unavailable_runtime_is_not_loaded(monkeypatch, error, expected):
    row = {'id': 1, 'grp': 1, 'ip': '192.0.2.1', 'mask': 32, 'port': 0, 'proto': 'any'}
    monkeypatch.setattr(address.table_crud, 'fetch', AsyncMock(return_value=[row]))
    monkeypatch.setattr(address, 'runtime_state', AsyncMock(return_value=({}, error)))
    result = await address.list_addresses(None)
    assert result['rows'][0]['in_memory'] is expected

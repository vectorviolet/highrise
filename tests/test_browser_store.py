"""Failure outcomes must keep session changes and the last durable save separate."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.browser_store import BrowserStore, WriteOutcome
from app.web_save_data import volume_or_default
from pygamine.assets import save_store
from util import web


@pytest.mark.parametrize("raw", ["{broken", "[]", "null", '{"master_volume": NaN}'])
def test_unreadable_json_is_reported_without_replacing_it(monkeypatch, raw):
    storage = Mock(getItem=Mock(return_value=raw))
    monkeypatch.setattr(save_store, "_browser_storage", lambda: storage)
    store = BrowserStore("highrise-save")
    assert store.invalid
    assert store.outcome == WriteOutcome.FAILED
    assert store.load() == {}
    storage.setItem.assert_not_called()
    storage.removeItem.assert_not_called()


def test_rejected_read_preserves_unknown_save(monkeypatch):
    storage = Mock(getItem=Mock(side_effect=RuntimeError("blocked")))
    monkeypatch.setattr(save_store, "_browser_storage", lambda: storage)
    store = BrowserStore("highrise-save")
    assert store.invalid
    assert store.outcome == WriteOutcome.FAILED
    storage.setItem.assert_not_called()


def test_failed_delete_is_reported_and_new_session_save_can_retry(monkeypatch):
    storage = Mock(
        getItem=Mock(return_value='{"money": 99}'),
        removeItem=Mock(side_effect=RuntimeError("blocked")),
    )
    monkeypatch.setattr(save_store, "_browser_storage", lambda: storage)
    store = BrowserStore("highrise-save")
    assert store.delete() == WriteOutcome.FAILED
    assert not store.present
    assert store.load() == {}
    assert store.save({"money": 1}) == WriteOutcome.DURABLE
    assert json.loads(storage.setItem.call_args.args[1]) == {"money": 1}


@pytest.mark.parametrize(
    "value", [None, "bad", [], {}, True, float("nan"), float("inf"), 10**400]
)
def test_invalid_volumes_use_default(value):
    assert volume_or_default(value, 0.5) == 0.5


@pytest.mark.parametrize("value", [0, 0.25, 1, -1, 2])
def test_numeric_volumes_are_left_for_audio_clamping(value):
    assert volume_or_default(value, 0.5) == value


def test_browser_notice_is_visible_until_cleared(monkeypatch):
    element = SimpleNamespace(style=SimpleNamespace(), setAttribute=Mock())
    document = SimpleNamespace(
        createElement=Mock(return_value=element),
        body=SimpleNamespace(appendChild=Mock()),
    )
    monkeypatch.setattr(web, "_window", lambda: SimpleNamespace(document=document))
    monkeypatch.setattr(web, "_notice", None)
    web.show_notice("Save failed")
    assert element.textContent == "Save failed"
    assert element.style.display == "block"
    element.setAttribute.assert_called_once_with("role", "status")
    web.show_notice("")
    assert element.style.display == "none"
    document.createElement.assert_called_once()

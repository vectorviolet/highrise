"""Session cache and explicit write outcomes around the pinned engine's browser store.

SaveStore currently swallows browser write errors. Keep its namespace/storage
selection, but report those errors and retain unsaved changes for a later retry.
No engine change or filesystem persistence is needed for the browser session.
"""

from copy import deepcopy
from enum import Enum
import json

from pygamine import SaveStore


class WriteOutcome(Enum):
    DURABLE = "durable"
    FAILED = "failed"
    SESSION_ONLY = "session_only"


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"Invalid JSON number: {value}")


class BrowserStore:
    def __init__(self, name: str) -> None:
        store = SaveStore(name)
        # These two fields are from the pinned pygamine 0049da0 implementation.
        self.storage = store._web
        self.key = store._web_key
        self.data: dict = {}
        self.present = False
        self.invalid = False
        self.outcome = WriteOutcome.SESSION_ONLY
        self._read()

    def _read(self) -> None:
        if self.storage is None:
            return
        try:
            raw = self.storage.getItem(self.key)
            self.present = isinstance(raw, str)
            if isinstance(raw, str):
                data = json.loads(raw, parse_constant=_reject_nonfinite)
                if not isinstance(data, dict):
                    raise ValueError("Save must be an object")
                self.data = data
            self.outcome = WriteOutcome.DURABLE
        except Exception:
            # A rejected read is not evidence that no save exists. Preserve it.
            self.invalid = True
            self.outcome = WriteOutcome.FAILED

    def load(self) -> dict:
        return deepcopy(self.data)

    def save(self, data: dict) -> WriteOutcome:
        encoded = json.dumps(data, allow_nan=False)
        self.data = deepcopy(data)
        self.present = True
        self.invalid = False
        return self._write(encoded)

    def update(self, **changes) -> WriteOutcome:
        return self.save(self.data | changes)

    def delete(self) -> WriteOutcome:
        self.data = {}
        self.present = False
        self.invalid = False
        return self._write(None)

    def _write(self, encoded: str | None) -> WriteOutcome:
        if self.storage is None:
            self.outcome = WriteOutcome.SESSION_ONLY
        else:
            try:
                if encoded is None:
                    self.storage.removeItem(self.key)
                else:
                    self.storage.setItem(self.key, encoded)
                self.outcome = WriteOutcome.DURABLE
            except Exception:
                self.outcome = WriteOutcome.FAILED
        return self.outcome

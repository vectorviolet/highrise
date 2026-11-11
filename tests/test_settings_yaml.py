"""config/settings.yaml: PyYAML silently keeps the last of two equal keys, so a duplicate would
make an edit of the first one do nothing."""

from pathlib import Path

import yaml


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    keys = [loader.construct_object(key, deep=deep) for key, _ in node.value]
    duplicates = {key for key in keys if keys.count(key) > 1}
    assert not duplicates, f"duplicate keys: {sorted(duplicates)}"
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def test_settings_has_no_duplicate_keys():
    yaml.load(Path("config/settings.yaml").read_text(encoding="utf-8"), _StrictLoader)

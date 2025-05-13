from pathlib import Path
from typing import Any, TypeVar

import yaml

T = TypeVar("T", bound=dict[str, Any])


def upper_keys(dict_to_upper: T) -> T:  # noqa: UP047
    """Convert to upper keys."""
    for key, value in dict_to_upper.copy().items():
        if isinstance(value, dict):
            upper_keys(value)
        elif isinstance(value, list):
            for list_item in value:
                if isinstance(list_item, dict):
                    upper_keys(list_item)
        dict_to_upper[key.upper()] = dict_to_upper.pop(key)

    return dict_to_upper


def load_yaml_config(config_path: str) -> dict[str, Any]:
    """Load yaml config."""
    with Path.open(Path(config_path)) as file:
        return upper_keys(yaml.safe_load(file))

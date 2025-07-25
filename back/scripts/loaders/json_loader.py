import json
import logging
import re
from io import BytesIO

import pandas as pd

from back.scripts.loaders.base_loader import BaseLoader
from back.scripts.loaders.utils import register_loader

LOGGER = logging.getLogger(__name__)


@register_loader
class JSONLoader(BaseLoader):
    """
    Loader for JSON files.
    """

    file_extensions = {"json"}
    file_media_type_regex = re.compile(r"json", flags=re.IGNORECASE)

    def __init__(self, *args, key: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key

    def process_data(self, data):
        content = None
        try:
            if isinstance(data, str):
                content = json.loads(data)
            elif isinstance(data, bytes):
                # utile dans les cas où l'encodage n'est pas utf-8
                content = json.load(BytesIO(data))
            else:
                raise Exception("Unhandled type")
        except json.JSONDecodeError as e:
            LOGGER.warning(f"Error while reading JSON: {e}. Try JsonL instead.")
            return JSONLLoader(file_url=self.file_url, **self.get_loader_kwargs()).process_data(
                data
            )

        if self.key is not None:
            content = content.get(self.key, {})

        # TODO: voir si avec un peu de retravail, `pd.json_normalize` peut faire la même chose
        df = self._process_dict(content)
        LOGGER.debug(f"JSON Data from {self.file_url} loaded.")
        return df

    def _process_dict(self, json_data: dict | list) -> pd.DataFrame:
        """
        Recursively search the JSON for data to extract.
        dict and list are considered part of the structure and will be flattened.
        """
        items = None
        if isinstance(json_data, list):
            items = json_data
        elif isinstance(json_data, dict):
            for _, v in json_data.items():
                if not isinstance(v, list):
                    continue
                items = v
                break
        if items is None:
            raise RuntimeError("JSON has unexpected format")

        flattened_data = [self._flatten_json(item) for item in items]
        return pd.DataFrame(flattened_data)

    @staticmethod
    def _flatten_json(x: dict | list, prefix: str = "") -> dict:
        flattened = {}

        if isinstance(x, dict):
            for key, value in x.items():
                new_key = f"{prefix}__{key}" if prefix else key

                # Recursively flatten nested dictionaries or lists
                if key == "geometry":
                    flattened.update({key: json.dumps(value)})
                elif isinstance(value, (dict, list)):
                    flattened.update(JSONLoader._flatten_json(value, new_key))
                else:
                    flattened[new_key] = value

        elif isinstance(x, list):
            for i, item in enumerate(x):
                new_key = f"{prefix}__{i}" if prefix else str(i)

                # Recursively flatten list items
                if isinstance(item, (dict, list)):
                    flattened.update(JSONLoader._flatten_json(item, new_key))
                else:
                    flattened[new_key] = item

        # For primitive types, just return the value
        else:
            flattened[prefix] = x

        return flattened


@register_loader
class JSONLLoader(BaseLoader):
    """
    Loader for JSONL files.
    """

    file_extensions = {"jsonl"}

    def process_data(self, data) -> pd.DataFrame:
        df = pd.read_json(BytesIO(data), **self.get_loader_kwargs())
        LOGGER.debug(f"JSONL Data from {self.file_url} loaded.")
        return df

    def get_loader_kwargs(self) -> dict:
        return super().get_loader_kwargs() | {"lines": True}

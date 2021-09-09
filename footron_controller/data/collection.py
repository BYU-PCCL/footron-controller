import json
from dataclasses import dataclass
import types
from typing import List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Collection:
    id: str
    experiences: list


def load_collections_from_fs(path=BASE_DATA_PATH) -> List[Collection]:
    collections_file_path = path.joinpath("collections.json")

    if not collections_file_path.exists():
        return []

    collections = []
    with open(collections_file_path) as collections_file:
        collection_data = json.load(collections_file)

    for key, value in collection_data.items():
        collections.append(Collection(id=key, **value))
    
    return collections

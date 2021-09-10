import json
from dataclasses import dataclass
from typing import Dict, List

from ..constants import BASE_DATA_PATH


@dataclass
class Collection:
    id: str
    experiences: List[str]


def load_collections_from_fs(path=BASE_DATA_PATH) -> Dict[str, Collection]:
    collections_file_path = path.joinpath("collections.json")

    if not collections_file_path.exists():
        return {}

    with open(collections_file_path) as collections_file:
        collection_data = json.load(collections_file)

    return {id: Collection(id=id, **value) for id, value in collection_data.items()}

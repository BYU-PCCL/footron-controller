import json
from dataclasses import dataclass
from typing import List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Collection:
    id: str
    title: str
    description: Optional[str] = None
    artist: Optional[str] = None


def load_collections_from_fs(path=BASE_DATA_PATH) -> List[Collection]:
    collections_file_path = path.joinpath("collections.json")

    if not collections_file_path.exists():
        return []

    collections = []
    with open(collections_file_path) as collections_file:
        collection_data = json.load(collections_file)

    for item in collection_data:
        collections.append(Collection(**item))

    return collections

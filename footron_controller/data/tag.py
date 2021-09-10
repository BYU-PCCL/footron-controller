import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Tag:
    id: str
    experiences: List[str]
    title: str
    description: Optional[str]


def load_tags_from_fs(path=BASE_DATA_PATH) -> Dict[str, Tag]:
    tags_file_path = path.joinpath("tags.json")

    if not tags_file_path.exists():
        return {}

    with open(tags_file_path) as tags_file:
        tag_data = json.load(tags_file)

    return {
        id: Tag(id=id, **value) for id, value in tag_data.items()
    }
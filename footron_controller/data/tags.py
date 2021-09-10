import json
from dataclasses import dataclass
from typing import List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Tag:
    id: str
    experiences: List[str]
    title: str
    description: Optional[str]


def load_tags_from_fs(path=BASE_DATA_PATH) -> List[Tag]:
    tags_file_path = path.joinpath("tags.json")

    if not tags_file_path.exists():
        return []

    tags = []
    with open(tags_file_path) as tags_file:
        tag_data = json.load(tags_file)

    for key, value in tag_data.items():
        tags.append(Tag(id=key, **value))

    return tags

import json
from dataclasses import dataclass
from typing import List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Tag:
    id: str
    experiences: Optional[list]
    title: str
    description: Optional[str]


def load_tags_from_fs(path=BASE_DATA_PATH) -> List[Tag]:
    tags_file_path = path.joinpath("tags.json")

    if not tags_file_path.exists():
        return []

    tags = []
    with open(tags_file_path) as tags_file:
        tag_data = json.load(tags_file)

    for item in tag_data:
        tags.append(Tag(**item))

    return tags
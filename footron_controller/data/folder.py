import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .tag import Tag
from ..constants import BASE_DATA_PATH


@dataclass
class Folder:
    id: str
    tags: List[str]
    title: str
    description: Optional[str]


# def load_folders_from_fs(path=BASE_DATA_PATH) -> Dict[str, Folder]:
#     folders_file_path = path.joinpath("folders.json")

#     if not folders_file_path.exists():
#         return {}

#     with open(folders_file_path) as folders_file:
#         folder_data = json.load(folders_file)

#     return {id: Folder(id=id, **value) for id, value in folder_data.items()}

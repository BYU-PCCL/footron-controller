import json
import multiprocessing
import pickle
import subprocess
from pathlib import Path
from queue import Empty
from typing import Dict, List, Optional

import numpy as np
from foocolor import CorePalette, QuantizerCelebi, score
from PIL import Image
from pydantic import BaseModel, parse_file_as

from ..constants import EXPERIENCE_COLORS_PATH, EXPERIENCES_PATH
from ..experiences import BaseExperience


class CachedColorPalettes(BaseModel):
    primary: Dict[int, str]
    secondary: Dict[int, str]
    tertiary: Dict[int, str]


class ColorCacheItem(BaseModel):
    hash: str
    colors: CachedColorPalettes


class ColorManager:
    def __init__(self):
        self._colors: Dict[str, CachedColorPalettes] = {}
        self._cache: Dict[str, ColorCacheItem] = {}
        self._colors_queue = multiprocessing.Queue()
        self._processing_colors: Dict[str, multiprocessing.Process] = {}

    def __getitem__(self, item) -> CachedColorPalettes:
        return self._colors[item]

    def get(self, experience_id: str) -> Optional[CachedColorPalettes]:
        return self._colors.get(experience_id)

    def _read_color_cache(self):
        if not EXPERIENCE_COLORS_PATH.exists():
            return {}

        return parse_file_as(Dict[str, ColorCacheItem], EXPERIENCE_COLORS_PATH)

    def _save_color_cache(self):
        with open(EXPERIENCE_COLORS_PATH, "w") as colors_file:
            json.dump(
                {key: value.dict() for key, value in self._cache.items()}, colors_file
            )

    def load_queued_colors(self):
        if not self._processing_colors:
            return

        try:
            while True:
                experience_id, hash, colors = self._colors_queue.get_nowait()
                self._colors[experience_id] = colors
                self._processing_colors.pop(experience_id)
                self._cache[experience_id] = ColorCacheItem(hash=hash, colors=colors)
                self._save_color_cache()
        except Empty:
            return

    @staticmethod
    def _process_experience(experience, hash, queue):
        thumb_path = Path(experience["experience_path"]) / "thumb.jpg"
        thumb_image = np.array(Image.open(thumb_path)).reshape(-1, 3)
        quantized = QuantizerCelebi(thumb_image).quantize(128)
        scores = score(quantized.color_to_count, desired=1)
        palette = CorePalette.of(scores[0])
        colors = CachedColorPalettes(
            **{
                sub_palette: {
                    i: f"#{hex(getattr(palette, sub_palette).get(i))[4:]}"
                    for i in range(0, 100 + 1, 5)
                }
                for sub_palette in ["primary", "secondary", "tertiary"]
            }
        )
        queue.put((experience["id"], hash, colors))
        pass

    def _queue_experience_process(self, experience: BaseExperience, hash: str):
        # Use multiprocessing Process to process the experience
        process = multiprocessing.Process(
            target=self._process_experience,
            args=(experience.dict(), hash, self._colors_queue),
        )
        process.start()
        self._processing_colors[experience.id] = process

    def load(self, experiences: List[BaseExperience]):
        self._cache = self._read_color_cache()

        # Iterate over every experience in the experiences directory
        for experience in experiences:
            # We can ignore unlisted experiences because they won't show up in the web
            # interface
            if experience.unlisted:
                continue

            # Get hash of thumb.jpg using sha256sum
            experience_path = experience.experience_path
            hash = (
                subprocess.check_output(
                    ["sha256sum", str(experience_path / "thumb.jpg")]
                )
                .decode("utf-8")
                .split()[0]
            )

            color = self._cache.get(experience.id)

            # If the color is not in the cache, get it from the experience
            if color is None or color.hash != hash:
                # TODO: Make this return default colors instead of nothing
                # Queue up for processing
                self._queue_experience_process(experience, hash)
            else:
                self._colors[experience.id] = color.colors

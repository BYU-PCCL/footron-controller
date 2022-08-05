import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple

from ..constants import PACKAGE_SCRIPTS_PATH

# Store previous Torch CUDA is_available attempts within this duration--note that we
# don't control the frequency of invocations within StabilityManager

_TORCH_FAILS_STACK_DURATION = timedelta(minutes=2)
# The proportion of failed CUDA is_available attempts within the stored attempts after
# which we decide the system is unstable
_TORCH_FAILS_THRESHOLD = 0.4
# We won't make any conclusions on less than 5 elements
_TORCH_FAILS_MIN_ELEMENTS = 5

logger = logging.getLogger(__name__)


class StabilityManager:
    _torch_attempts: List[Tuple[datetime, bool]]

    def __init__(self):
        self._torch_attempts = []

    def _cull_torch_attempts(self):
        cutoff = datetime.now() - _TORCH_FAILS_STACK_DURATION
        while True:
            if not self._torch_attempts:
                break

            when, attempt = self._torch_attempts[-1]
            if when > cutoff:
                break

            self._torch_attempts.pop()

    @staticmethod
    def _torch_cuda_attempt() -> bool:
        response = subprocess.run([PACKAGE_SCRIPTS_PATH / "gpu-stable.py"])

        if response.returncode != 0:
            logger.warning(
                "CUDA stability check failed with non-zero exit code, system may be unstable"
            )
            return False

        return True

    def _is_torch_stable(self) -> bool:
        self._cull_torch_attempts()
        self._torch_attempts.insert(0, (datetime.now(), self._torch_cuda_attempt()))

        total = len(self._torch_attempts)
        if total < _TORCH_FAILS_MIN_ELEMENTS:
            return True

        fail_count = len(list(filter(lambda a: not a[1], self._torch_attempts)))
        return fail_count / total < _TORCH_FAILS_THRESHOLD

    def check_stable(self):
        return self._is_torch_stable()

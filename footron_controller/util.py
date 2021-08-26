import asyncio
import logging
import subprocess
import os

logger = logging.getLogger(__name__)


def _check_pid(pid):
    """ https://stackoverflow.com/a/568285 """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


async def mercilessly_kill_process(process: subprocess.Popen):
    while True:
        process.terminate()
        if not _check_pid(process.pid):
            break
        logger.warning(
            f"Managed process with pid {process.pid} didn't die, trying again in 1s..."
        )
        await asyncio.sleep(1)

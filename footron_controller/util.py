import asyncio
import logging
import subprocess

logger = logging.getLogger(__name__)


async def mercilessly_kill_process(process: subprocess.Popen):
    while True:
        process.terminate()
        if process.poll() is not None:
            break
        logger.warning(
            f"Managed process with PID {process.pid} didn't die, trying again in 1s..."
        )
        await asyncio.sleep(1)

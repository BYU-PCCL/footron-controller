import argparse
import logging
import time
from .timer import Timer


def _log_level(arg):
    level = getattr(logging, arg.upper(), None)
    if level is None:
        raise ValueError(f"Invalid log level '{arg}'")
    return level


parser = argparse.ArgumentParser()
log_level_group = parser.add_mutually_exclusive_group()
log_level_group.add_argument(
    "--level",
    help="set log level ('debug', 'info' (default), 'warning', 'error', 'critical')",
    type=_log_level,
)
log_level_group.add_argument(
    "-v",
    help="set log level to verbose",
    action="store_const",
    const=logging.DEBUG,
)

args = parser.parse_args()
logging.basicConfig(level=args.v or args.level or logging.INFO)

timer = Timer()

while True:
    timer.advance_if_ready()
    time.sleep(1)

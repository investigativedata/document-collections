from pathlib import Path

from memorious.operations.store import _get_directory_path, directory
from servicelayer import env

LIMIT = env.to_int("LIMIT")


def store(context, data):
    directory(context, data)
    if LIMIT:
        path = Path(_get_directory_path(context))
        files = len(list(path.glob("*.json")))
        if files >= LIMIT:
            context.log.info("Limit reached: %d" % files)
            context.crawler.cancel()

from datetime import datetime

from dateparser import parse
from memorious.core import conn
from memorious.operations.store import directory
from servicelayer import env
from servicelayer.cache import make_key

LIMIT = env.to_int("LIMIT")
TIME_LIMIT = env.to_int("TIME_LIMIT")


def store(context, data):
    directory(context, data)
    context.set_tag(data["incremental_key"], True)
    conn.incr(make_key(context.crawler, "run", context.run_id, "documents"))

    if TIME_LIMIT:
        start = parse(
            conn.get(make_key(context.crawler, "run", context.run_id, "start"))
        )
        delta = (datetime.utcnow() - start).seconds / 60
        if delta > TIME_LIMIT:
            context.log.info(
                "Time limit reached: %d / %d minutes" % (delta, TIME_LIMIT)
            )
            context.crawler.cancel()

    if LIMIT:
        documents = int(
            conn.get(make_key(context.crawler, "run", context.run_id, "documents"))
        )
        if documents >= LIMIT:
            context.log.info("Limit reached: %d documents" % documents)
            context.crawler.cancel()

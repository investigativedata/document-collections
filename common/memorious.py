from datetime import datetime

from common.zavod import get_zavod, make_document
from dateparser import parse
from memorious.core import conn
from memorious.operations.store import directory
from servicelayer import env
from servicelayer.cache import make_key

LIMIT = env.to_int("LIMIT")
TIME_LIMIT = env.to_int("TIME_LIMIT")


def init(context, data):
    zavod = get_zavod(context)
    zavod.export_metadata("export/index.json")
    context.emit(data=data)


def store(context, data):
    directory(context, data)
    incremental_key = data.get("incremental_key")
    if incremental_key is not None:
        context.set_tag(incremental_key, True)
    conn.incr(make_key(context.crawler, "run", context.run_id, "documents"))

    if context.params.get("make_proxy"):
        zavod = get_zavod(context)
        proxy = make_document(zavod, data, context.crawler.config)
        zavod.emit(proxy)

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

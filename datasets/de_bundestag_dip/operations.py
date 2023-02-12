from datetime import datetime, timedelta
from typing import Any

from banal import ensure_dict, ensure_list
from common.zavod import get_zavod, make_document, make_folder
from furl import furl
from memorious import settings
from nomenklatura.entity import CE
from servicelayer import env
from servicelayer.cache import make_key
from zavod import Zavod

Data = dict[str, Any]


def init(context, data):
    f = furl(context.params["url"])
    if (
        not env.to_bool("FULL_RUN")
        and not env.to_int("LIMIT")  # noqa
        and not env.to_int("TIME_LIMIT")  # noqa
    ):
        start_date = (
            env.get("START_DATE")
            or (  # noqa
                datetime.now()
                - timedelta(**ensure_dict(context.params.get("timedelta")))  # noqa
            )
            .date()
            .isoformat()
        )
        f.args["f.datum.start"] = start_date
    data["url"] = f.url
    context.emit(data=data)


def parse(context, data):
    res = context.http.rehash(data)
    seen = 0

    for document in ensure_list(res.json["documents"]):
        incremental_key = make_key("skip_incremental", document["id"])
        if settings.INCREMENTAL:
            if context.check_tag(incremental_key):
                context.log.debug(f"Skipping: {incremental_key}")
                seen += 1
                continue

        data["incremental_key"] = incremental_key
        detail_data = parse_drucksache(document)
        context.emit("download", data={**data, **detail_data, **{"meta": document}})

    context.log.info("%d documents already seen." % seen)

    # next page
    fu = furl(data["url"])
    if res.json["cursor"] != fu.args.get("cursor"):
        fu.args["cursor"] = res.json["cursor"]
        context.emit("cursor", data={**data, **{"url": fu.url}})


def enrich(context, data):
    m = data["meta"]

    zavod = get_zavod(context)
    document = make_document(zavod, data, context.crawler.config)
    document.add("title", data["title"])
    document.add("publishedAt", data["published_at"])
    folder = make_folder(
        zavod,
        data["base"],
        f'{m["wahlperiode"]}. Wahlperiode',
        m["dokumentart"],
        m["drucksachetyp"],
    )
    document.add("parent", folder)
    document.add("ancestors", folder)
    document.add("ancestors", folder.get("ancestors"))
    zavod.emit(document)

    for item in ensure_list(m.get("urheber")):
        proxy = make_body(zavod, item)
        role = "Einbringender Urheber" if item.get("einbringer") else "Urheber"
        rel = make_documentation(zavod, document, proxy, role, data)
        zavod.emit(proxy)
        zavod.emit(rel)

    for item in ensure_list(m.get("ressort")):
        proxy = make_body(zavod, item)
        role = "Federführendes Ressort" if item["federfuehrend"] else "Ressort"
        rel = make_documentation(zavod, document, proxy, role, data)
        zavod.emit(proxy)
        zavod.emit(rel)

    for item in ensure_list(m.get("autoren_anzeige")):
        proxy = make_person(zavod, item)
        rel = make_documentation(zavod, document, proxy, "Autor", data)
        zavod.emit(proxy)
        zavod.emit(rel)

    context.emit(data=data)


def parse_drucksache(document):
    base = None
    if document["herausgeber"] == "BT":
        base = "Bundestag"
    elif document["herausgeber"] == "BR":
        base = "Bundesrat"
    else:
        return
    data = {"base": base}
    data["title"] = " - ".join(
        (
            base,
            document["dokumentnummer"],
            document["drucksachetyp"],
            document["titel"],
        )
    )
    data["published_at"] = document["datum"]
    data["foreign_id"] = document["id"]
    if "urheber" in document:
        data["publisher"] = ", ".join([u["titel"] for u in document["urheber"]])
    else:
        data["publisher"] = document["herausgeber"]
    data["url"] = document["fundstelle"]["pdf_url"]
    return data


def make_body(context: Zavod, data: Data) -> CE:
    proxy = context.make("PublicBody")
    proxy.id = context.make_slug(data["titel"])
    proxy.add("name", data["titel"])
    proxy.add("country", "de")
    proxy.add("jurisdiction", "de")
    return proxy


def make_person(context: Zavod, data: Data) -> CE:
    proxy = context.make("Person")
    proxy.id = context.make_slug("author", data["id"])
    proxy.add("name", data["autor_titel"])
    proxy.add("summary", data["titel"])
    proxy.add("country", "de")
    return proxy


def make_documentation(
    context: Zavod, document: CE, entity: CE, role: str, data: Data
) -> CE:
    proxy = context.make("Documentation")
    proxy = context.make("Documentation")
    proxy.id = context.make_id(document.id, entity.id, role)
    proxy.add("role", role)
    proxy.add("date", data["published_at"])
    proxy.add("entity", entity)
    proxy.add("document", document)
    return proxy

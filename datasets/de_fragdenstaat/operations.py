import re

from common.zavod import get_zavod, make_document
from memorious import settings
from memorious.helpers import make_id
from servicelayer import env
from servicelayer.cache import make_key

DEFAULT_URL = "https://fragdenstaat.de/api/v1/document"
MAX_ID = env.to_int("MAX_ID")


def _get(data, *keys):
    if not len(keys):
        return data or None
    return _get(data.get(keys[0], {}) or {}, *keys[1:])


def init(context, data):
    publicbody_store = context.datastore["fragdenstaat_bodies"]  # cache bodies
    url = data.get("url") or context.get("url", DEFAULT_URL)
    res = context.http.get(url)
    seen = 0

    for document in res.json["objects"]:
        # if document.get("foirequest") is not None:  # use only FOI requests documents

        incremental_key = make_key("skip_incremental", document["id"])
        if settings.INCREMENTAL:
            if context.check_tag(incremental_key):
                context.log.debug(f"Skipping: {incremental_key}")
                seen += 1
                continue

        publicbody = {}
        if document["publicbody"] is not None:
            publicbody_key = make_id(document["publicbody"])
            publicbody = publicbody_store.find_one(key=publicbody_key)

            if publicbody is None:
                publicbody_res = context.http.get(document["publicbody"])
                publicbody_data = publicbody_res.json
                publicbody = {
                    "key": publicbody_key,
                    "name": publicbody_data.get("name") or "",
                    "alias": publicbody_data.get("other_names") or "",
                    "description": publicbody_data.get("description") or "",
                    "website": publicbody_data.get("url") or "",
                    "sourceUrl": publicbody_data.get("site_url") or "",
                    "legalForm": _get(publicbody_data, "classification", "name")
                    or "",  # noqa
                    "keywords": ";".join(
                        c.get("name", "") for c in publicbody_data.get("categories", [])
                    )
                    or "",  # noqa
                    "email": publicbody_data.get("email") or "",
                    "address": re.sub(
                        r",\s?$",
                        "",
                        re.sub(r"[\r|\n]+", ", ", publicbody_data.get("address", "")),
                    )
                    or "",  # noqa
                    "jurisdiction": _get(publicbody_data, "jurisdiction", "name")
                    or "",  # noqa
                }
                publicbody_store.insert(publicbody)

        data = {
            "id": document["id"],
            "url": document["file_url"],
            "title": document["title"],
            "description": document["description"],
            "source_url": document["site_url"],
            "incremental_key": incremental_key,
        }
        if data["url"]:
            context.emit(data={**data, **{"publicbody": publicbody.get("key", None)}})

    if res.json["meta"]["next"] is not None:
        context.recurse(data={"url": res.json["meta"]["next"]})

    if seen:
        context.log.info("Already seen: %d" % seen)


def enrich(context, data):
    zavod = get_zavod(context)
    document = make_document(zavod, data, context.crawler.config)

    if data.get("publicbody") is not None:
        publicbody_store = context.datastore["fragdenstaat_bodies"]
        publicbody = publicbody_store.find_one(key=data["publicbody"])
        if publicbody is not None:
            body = zavod.make("PublicBody")
            body.id = zavod.make_slug("body", publicbody["key"])
            body.add("keywords", publicbody["keywords"].split(";"))
            body.add("alias", publicbody["alias"].split(","))
            for key in (
                "name",
                "description",
                "website",
                "sourceUrl",
                "legalForm",
                "email",
                "address",
            ):
                body.add(key, publicbody[key])

            rel = zavod.make("Documentation")
            role = "Publisher"
            rel.id = zavod.make_id(role, document.id, body.id)
            rel.add("entity", body)
            rel.add("document", document)
            rel.add("role", role)

            zavod.emit(body)
            zavod.emit(rel)

    # mark stored document to exclude from next run
    context.set_tag(data["incremental_key"], True)
    context.emit(data=data)

    if MAX_ID and data["id"] > MAX_ID:
        context.log.info("Max id (%d) reached." % data["id"])
        context.crawler.cancel()
        return

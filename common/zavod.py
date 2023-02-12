from pathlib import Path
from typing import Any, Iterable

from dateparser import parse
from memorious.logic.context import Context
from nomenklatura.entity import CE, CompositeEntity
from zavod import Zavod, ZavodDataset
from zavod.sinks.file import JSONFileSink

Data = dict[str, Any]


def get_zavod(context: Context) -> Zavod:
    data_path = Path(context.crawler.source_file).parent / "data"
    out_path = data_path.joinpath("fragments.json")
    out_path.parent.mkdir(exist_ok=True, parents=True)
    sink = JSONFileSink[CompositeEntity](out_path, append=True)
    dataset = ZavodDataset.from_path(context.crawler.source_file)
    return Zavod(dataset, CompositeEntity, data_path=data_path, sink=sink)


def make_document(context: Zavod, data: Data, config: Data) -> CE:
    # data: memorious data
    data["headers"] = {k.lower(): v for k, v in data["headers"].items()}
    proxy = context.make("Document")
    proxy.id = data["content_hash"]
    proxy.add("contentHash", data["content_hash"])
    proxy.add("publisher", config["publisher"]["name"])
    proxy.add("publisherUrl", config["publisher"]["url"])
    proxy.add("fileSize", data["headers"].get("content-length"))
    proxy.add("mimeType", data["headers"]["content-type"])
    proxy.add("sourceUrl", data["url"])
    proxy.add("modifiedAt", data.get("modified_at"))
    proxy.add("retrievedAt", parse(data["headers"]["date"]))
    proxy.add("title", data.get("title"))
    proxy.add("name", data.get("name"))
    proxy.add("summary", data.get("summary"))
    proxy.add("publishedAt", parse(data.get("published_at", "")))
    return proxy


def make_folder(context: Zavod, *path: Iterable[str]) -> CE:
    proxy = None
    parent = None
    ancestors = []
    for name in path:
        proxy = context.make("Folder")
        proxy.id = context.make_slug("folder", name)
        proxy.add("name", name)
        proxy.add("fileName", name)
        if parent is not None:
            proxy.add("parent", parent)
            proxy.add("ancestors", ancestors)
        parent = proxy
        ancestors.append(proxy)
        context.emit(proxy)
    return proxy

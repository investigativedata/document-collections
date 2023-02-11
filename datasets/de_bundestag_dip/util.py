from alephclient import settings
from alephclient.errors import AlephException
from alephclient.util import backoff
from banal import clean_dict
from memorious.core import get_rate_limit
from memorious.operations.aleph import _create_meta_object, get_api, get_collection_id
from servicelayer.cache import make_key


def aleph_folder(context, data):
    api = get_api(context)
    if api is None:
        return
    collection_id = get_collection_id(context, api)
    foreign_id = data.get("foreign_id")
    if foreign_id is None:
        context.log.warning("No folder foreign ID!")
        return

    meta = clean_dict(_create_meta_object(context, data))
    label = meta.get("file_name", meta.get("source_url"))

    document_id = context.get_tag(make_key(collection_id, foreign_id))
    if document_id is not None:
        context.log.info("Use folder: %s", label)
        return document_id

    context.log.info("Make folder: %s", label)
    for try_number in range(api.retries):
        rate = settings.MEMORIOUS_RATE_LIMIT
        rate_limit = get_rate_limit("aleph", limit=rate)
        rate_limit.comply()
        try:
            res = api.ingest_upload(collection_id, metadata=meta, sync=True)
            document_id = res.get("id")
            context.log.info("Aleph folder entity ID: %s", document_id)
            # Save the document id in cache for future use
            context.set_tag(make_key(collection_id, foreign_id), document_id)
            data["aleph_folder_id"] = document_id
            data["aleph_collection_id"] = collection_id
            # context.emit(data=data, optional=True)
            return document_id
        except AlephException as ae:
            if try_number > api.retries or not ae.transient:
                context.emit_warning("Error: %s" % ae)
                return
            backoff(ae, try_number)

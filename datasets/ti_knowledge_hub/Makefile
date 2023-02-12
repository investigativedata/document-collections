all: clean process publish

data/datastore.sqlite3:
	bash ../../sync.sh ti_knowledge_hub

data/store/ti_knowledge_hub:
	mkdir -p data/store/ti_knowledge_hub

data/fragments.json:
	touch data/fragments.json

data/sorted.json: data/fragments.json
	sort -o data/sorted.json data/fragments.json

data/export/entities.ftm.json: data/sorted.json
	mkdir -p data/export
	nk sorted-aggregate -i data/sorted.json -o data/export/entities.ftm.json

publish: data/export/entities.ftm.json data/store/ti_knowledge_hub
	bash ../../upload.sh ti_knowledge_hub

process: data/datastore.sqlite3
	MEMORIOUS_CONFIG_PATH=. memorious run ti_knowledge_hub --threads=1

clean:
	rm -rf data/


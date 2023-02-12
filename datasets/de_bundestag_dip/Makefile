all: clean process publish

data/datastore.sqlite3:
	bash ../../sync.sh de_bundestag_dip

data/store/de_bundestag_dip:
	mkdir -p data/store/de_bundestag_dip

data/fragments.json:
	touch data/fragments.json

data/sorted.json: data/fragments.json
	sort -o data/sorted.json data/fragments.json

data/export/entities.ftm.json: data/sorted.json
	mkdir -p data/export
	nk sorted-aggregate -i data/sorted.json -o data/export/entities.ftm.json

publish: data/export/entities.ftm.json data/store/de_bundestag_dip
	bash ../../upload.sh de_bundestag_dip

process: data/datastore.sqlite3
	MEMORIOUS_CONFIG_PATH=. memorious run de_bundestag_dip --threads=1

clean:
	rm -rf data/

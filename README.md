# 👪 Wiki-Family-Utils: Extracting plain text from Wikimedia Project Dumps

Simple scripts to extract plain text from the dump files of Wikimedia projects.
It processes the HTML data from [Wikimedia Enterprise HTML dumps](https://dumps.wikimedia.org/other/enterprise_html/) and cleans it up to produce plain text.

## Installation

```bash
poetry install
```

## Usage

### Download

To download a dump file to process, run the following command:

```bash
python download.py ja wiktionary
```

You need to specify `language` and `project` as arguments.
The following choices are available for `project`:

- `wiki`: <https://www.wikipedia.org/>
- `wiktionary`: <https://www.wiktionary.org/>
- `wikibooks`: <https://www.wikibooks.org/>
- `wikinews`: <https://www.wikinews.org/>
- `wikiquote`: <https://www.wikiquote.org/>
- `wikisource`: <https://www.wikisource.org/>
- `wikiversity`: <https://www.wikiversity.org/>
- `wikivoyage`: <https://www.wikivoyage.org/>

By default, the file will be saved in the `data` directory.

### Extract

To extract plain text from the downloaded file, run the following command:

```bash
PATH_TO_DOWNLOADED_FILE="data_downloaded/jawiktionary-NS0-20231101-ENTERPRISE-HTML.json.tar.gz"
python extract.py $PATH_TO_DOWNLOADED_FILE data_extracted/jawiktionary-20231101.jsonl
```

## License

Wiki-Family-Utils is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Acknowledgement

This project is inspired by [Wikipedia-Utils](https://github.com/singletongue/wikipedia-utils), serving similar use cases but with customized processing.

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
poetry run python download.py ja wiktionary
```
You need to specify `language` and `project` as arguments.
The following choices are available for `project`:
- `wiki`: https://www.wikipedia.org/
- `wiktionary`: https://www.wiktionary.org/
- `wikibooks`: https://www.wikibooks.org/
- `wikinews`: https://www.wikinews.org/
- `wikiquote`: https://www.wikiquote.org/
- `wikisource`: https://www.wikisource.org/
- `wikiversity`: https://www.wikiversity.org/
- `wikivoyage`: https://www.wikivoyage.org/

By default, the file will be saved in the `data` directory.

### Extract
To extract plain text from the downloaded file, run the following command:
```bash
PATH_TO_DOWNLOADED_FILE="data/jawiktionary-NS0-20231101-ENTERPRISE-HTML.json.tar.gz"
poetry run python extract.py $PATH_TO_DOWNLOADED_FILE plain_text
```
By default, the extracted data are saved as jsonl file and stored under the same directory as the input file.

You can specify the output type from `plain_text` or `passages`.
- `plain_text`: Each page is processed as a plain text which is useful for training a language model.
- `passages`: Each page is processed as a list of passages which is useful for training a passage retrieval model.

⚠️ Note that some parameters in `extract.py` are hard-coded for Japanese text 🇯🇵. 
To get the cleanest text in your language, you may need to tweak the code.

### Example
Here is an example script to download and process all the files of Wikimedia projects.
```bash 
wiki_sites=("wiki" "wiktionary" "wikibooks" "wikinews" "wikiquote" "wikisource" "wikiversity" "wikivoyage")
language="ja"

for site in "${wiki_sites[@]}"; do
    poetry run python download.py $language $site
done

directory="data"
for file in "$directory"/*.tar.gz; do
    poetry run python extract.py $file plain_text
done
```

## License
Wiki-Family-Utils is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Acknowledgement
This project is kind of a child 👦 of [Wikipedia-Utils](https://github.com/singletongue/wikipedia-utils), serving similar use cases but with customized processing. 
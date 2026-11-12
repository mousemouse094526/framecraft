# pythainlp

**Kind:** library

**Version:** 5.4.0

**Docs:** https://pythainlp.org/dev-docs/

## Best practices

- `word_tokenize(text, engine="newmm")` cuts Thai into words with the dictionary inside the package; no download, no network — [tokenize API](https://pythainlp.org/dev-docs/api/tokenize.html)
- Point the data folder away from `~/pythainlp-data` with the env `PYTHAINLP_DATA` before the first call that touches data; `PYTHAINLP_DATA_DIR` still works but is deprecated (a warning), and setting both raises `ValueError` — [tools/path.py `get_pythainlp_data_path` v5.4.0](https://github.com/PyThaiNLP/pythainlp/blob/v5.4.0/pythainlp/tools/path.py)
- `PYTHAINLP_OFFLINE=1` stops automatic background downloads; explicit `corpus.download` still works — [tools/path.py `is_offline_mode` v5.4.0](https://github.com/PyThaiNLP/pythainlp/blob/v5.4.0/pythainlp/tools/path.py)
- Importing `pythainlp.tokenize` takes about 0.1 s; the env must be set before it

## Pattern

```python
def words(project: ProjectPaths, text: str) -> list[str]:
    os.environ["PYTHAINLP_DATA"] = str(project.pythainlp_dir)
    os.environ["PYTHAINLP_OFFLINE"] = "1"
    from pythainlp.tokenize import word_tokenize

    return word_tokenize(text, engine="newmm", keep_whitespace=False)
```

Follows [tokenize API](https://pythainlp.org/dev-docs/api/tokenize.html).

## Traps

- `get_pythainlp_data_path()` creates the folder whenever it is called; without the env that is `~/pythainlp-data`, outside the project (ADR 0003) — [tools/path.py v5.4.0](https://github.com/PyThaiNLP/pythainlp/blob/v5.4.0/pythainlp/tools/path.py)

## Sources

- [PyThaiNLP tokenize API](https://pythainlp.org/dev-docs/api/tokenize.html) — `word_tokenize`, engine `newmm` (accessed 2026-11-02)
- [pythainlp v5.4.0 source](https://github.com/PyThaiNLP/pythainlp/tree/v5.4.0) — `PYTHAINLP_DATA`, `PYTHAINLP_OFFLINE`, data folder; read from the installed package (accessed 2026-11-02)

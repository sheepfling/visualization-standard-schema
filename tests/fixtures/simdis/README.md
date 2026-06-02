# SIMDIS Test Fixtures

This directory is populated from `reference/simdis_corpus_v0_1/simdis_corpus_v0_1.zip`.
The tests use the extracted corpus files directly so each sample can be linked to a
concrete on-disk asset and round-tripped without going through the ZIP container.

Run the SIMDIS-focused checks with:

```bash
python3 -m pytest tests/test_simdis_corpus.py -q
```

For the broader SDJ corpus loop that exercises the supported SIMDIS native path:

```bash
python3 -m pytest -m sdj_roundtrip
```

The `.asi` and `.gog` fixtures are checked into the repo, so these tests are safe to
rerun without SIMDIS installed.

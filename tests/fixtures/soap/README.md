# SOAP Test Fixtures

This directory mirrors the tracked SOAP bundle corpus from
`examples/orb-corpus/soap/orb_format_collection/soap15`.

The corpus is used by `tests/test_soap_corpus.py` to validate:

- fixture hashes against `manifests/corpus-file-manifest.json`
- parse -> emit -> parse round-trips for every tracked SOAP bundle sample
- directory-based bundle loading for the emitted file sets

Run the SOAP-focused checks with:

```bash
python3 -m pytest tests/test_soap_corpus.py -q
```

For the broader SDJ corpus loop that exercises the supported SOAP native path:

```bash
python3 -m pytest -m sdj_roundtrip
```

The bundle fixtures are tracked in the repository, so these tests are repeatable on
any machine without a SOAP install.

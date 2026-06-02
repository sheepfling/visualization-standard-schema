# SIMDIS input corpus v0.1

This package starts a curated SIMDIS input corpus for the SDJ/SIMDIS backend.

It contains:

- confirmed ASI-lite examples generated from the public SDK parser command subset
- confirmed GOG shape examples generated from the public SDK GOG shape model
- one inferred `.discn` candidate file, clearly marked as unvalidated
- empty collection buckets for `.fct` and `.svml`, which need official installed samples
- scripts to crawl a SIMDIS installation/sample repository and copy native examples with checksums

## Immediate use

Use these as seed fixtures for SDJ export tests:

```text
public_seed/asi/*.asi
public_seed/gog/*.gog
```

Treat these as research placeholders until validated in native SIMDIS:

```text
inferred/discn/*.discn
needs_official_samples/fct/
needs_official_samples/svml/
```

## Why `.asi` is not enough

`.asi` is SIMDIS ASCII and is useful for dynamic entities: platforms, platform samples, beams, gates, and projectors. Static authored geometry should usually go to `.gog`. Binary `.fct`, data-initialization `.discn`, and view `.svml` need native examples from SIMDIS installs before we claim full support.

## Suggested next command on a machine with SIMDIS installed

```bash
python3 scripts/collect_simdis_samples.py \
  --root "$SIMDIS_DIR" \
  --root "$SIMDIS_USER_DIR" \
  --out collected
```

The collector is conservative: it copies files by extension, writes SHA-256 hashes, and does not modify originals.

# FCT samples needed

`.fct` is listed by the public SIMDIS SDK as a SIMDIS Binary file pattern, but I did not find a public `.fct` sample in the public SDK repository or open web search results during this pass.

Do not synthesize `.fct` files by hand. Treat `.fct` as native binary and collect samples from an installed SIMDIS distribution or official sample-data repository.

Suggested collection paths:

```text
$SIMDIS_DIR/data
$SIMDIS_DIR/demos
$SIMDIS_DIR/examples
$SIMDIS_USER_DIR
$SIMDIS_SDK_FILE_PATH
```

Use `scripts/collect_simdis_samples.py` from this corpus package to crawl local installations and copy `.fct` files into `collected/fct/` with checksums.

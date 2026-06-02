import inspect

from vss.convert.adapters import EMIT_FORMATS, FORMAT_ADAPTERS, INGEST_FORMATS, TARGET_ADAPTERS, get_format_adapter, get_target_adapter


def test_target_adapter_registry_exposes_canonical_targets() -> None:
    assert set(TARGET_ADAPTERS) == {"czml", "simdis", "soap", "orb"}


def test_target_adapter_contract_shape_is_uniform() -> None:
    for name in ("czml", "simdis", "soap", "orb"):
        adapter = get_target_adapter(name)
        assert adapter.target == name
        ingest_signature = inspect.signature(adapter.ingest)
        emit_signature = inspect.signature(adapter.emit)

        assert list(ingest_signature.parameters) == ["source", "input_format", "source_name"]
        assert ingest_signature.parameters["input_format"].kind is inspect.Parameter.KEYWORD_ONLY
        assert ingest_signature.parameters["source_name"].kind is inspect.Parameter.KEYWORD_ONLY
        assert list(emit_signature.parameters)[0] == "scene"


def test_format_adapter_registry_exposes_cli_modes() -> None:
    assert set(FORMAT_ADAPTERS) == {"czml", "simdis-asi", "simdis-bundle", "soap", "orb"}
    assert INGEST_FORMATS == tuple(FORMAT_ADAPTERS)
    assert EMIT_FORMATS == tuple(name for name, adapter in FORMAT_ADAPTERS.items() if adapter.emit is not None)


def test_format_adapter_contract_shape_is_uniform() -> None:
    for name in ("czml", "simdis-asi", "simdis-bundle", "soap", "orb"):
        adapter = get_format_adapter(name)
        assert adapter.format == name
        assert adapter.target in {"czml", "simdis", "soap", "orb"}
        ingest_signature = inspect.signature(adapter.ingest)
        assert list(ingest_signature.parameters) == ["source", "input_format", "source_name"]
        assert ingest_signature.parameters["input_format"].kind is inspect.Parameter.KEYWORD_ONLY
        assert ingest_signature.parameters["source_name"].kind is inspect.Parameter.KEYWORD_ONLY
        if adapter.emit is not None:
            emit_signature = inspect.signature(adapter.emit)
            assert list(emit_signature.parameters)[0] == "scene"


def test_simdis_bundle_is_ingest_only() -> None:
    assert get_format_adapter("simdis-bundle").emit is None

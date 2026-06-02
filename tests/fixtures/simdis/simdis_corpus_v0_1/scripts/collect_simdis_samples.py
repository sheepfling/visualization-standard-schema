from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


TARGET_EXTENSIONS: dict[str, set[str]] = {
    "asi": {".asi"},
    "fct": {".fct"},
    "discn": {".discn"},
    "gog": {".gog", ".ll", ".lla", ".xy", ".xyz", ".rxy", ".rxyz"},
    "svml": {".svml", ".view"},
    "bookmarks": {".bml"},
    "prefs": {".prefs", ".rul"},
}


@dataclass(frozen=True)
class CollectedSample:
    source: str
    copiedTo: str
    category: str
    extension: str
    sizeBytes: int
    sha256: str


@dataclass(frozen=True)
class CollectionReport:
    roots: list[str]
    outputRoot: str
    samples: list[CollectedSample]
    skipped: list[str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        ####
    ####
    return digest.hexdigest()
####


def _iter_candidate_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        ####
        if root.is_file():
            yield root
            continue
        ####
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in {".git", "node_modules", "__pycache__"}]
            base = Path(dirpath)
            for filename in filenames:
                yield base / filename
            ####
        ####
    ####
####


def _category_for(path: Path) -> str | None:
    suffix = path.suffix.lower()
    for category, extensions in TARGET_EXTENSIONS.items():
        if suffix in extensions:
            return category
        ####
    ####
    return None
####


def _safe_copy_name(path: Path, digest: str) -> str:
    stem = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in path.stem)
    return f"{stem}.{digest[:12]}{path.suffix.lower()}"
####


def collect_samples(roots: list[Path], output_root: Path) -> CollectionReport:
    output_root.mkdir(parents=True, exist_ok=True)
    samples: list[CollectedSample] = []
    skipped: list[str] = []

    for path in _iter_candidate_files(roots):
        category = _category_for(path)
        if category is None:
            continue
        ####
        try:
            digest = _sha256(path)
            destination_dir = output_root / category
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / _safe_copy_name(path, digest)
            if not destination.exists():
                shutil.copy2(path, destination)
            ####
            samples.append(
                CollectedSample(
                    source=str(path),
                    copiedTo=str(destination),
                    category=category,
                    extension=path.suffix.lower(),
                    sizeBytes=path.stat().st_size,
                    sha256=digest,
                )
            )
        except OSError as exc:
            skipped.append(f"{path}: {exc}")
        ####
    ####

    report = CollectionReport(
        roots=[str(root) for root in roots],
        outputRoot=str(output_root),
        samples=samples,
        skipped=skipped,
    )
    report_path = output_root / "collection-manifest.json"
    report_path.write_text(
        json.dumps(
            {
                "roots": report.roots,
                "outputRoot": report.outputRoot,
                "samples": [asdict(sample) for sample in report.samples],
                "skipped": report.skipped,
                "counts": _count_by_category(report.samples),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return report
####


def _count_by_category(samples: list[CollectedSample]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sample in samples:
        counts[sample.category] = counts.get(sample.category, 0) + 1
    ####
    return counts
####


def _env_roots() -> list[Path]:
    roots: list[Path] = []
    for key in ["SIMDIS_DIR", "SIMDIS_USER_DIR", "SIMDIS_SDK_FILE_PATH"]:
        value = os.environ.get(key)
        if value:
            roots.append(Path(value).expanduser())
        ####
    ####
    return roots
####


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect SIMDIS sample files into a fixture corpus.")
    parser.add_argument("--root", action="append", default=[], help="Root directory or file to scan. May be repeated.")
    parser.add_argument("--out", default="collected", help="Output directory for copied files and manifest.")
    parser.add_argument("--include-env", action="store_true", help="Also scan SIMDIS_DIR, SIMDIS_USER_DIR, and SIMDIS_SDK_FILE_PATH.")
    return parser.parse_args()
####


def main() -> int:
    args = parse_args()
    roots = [Path(root).expanduser() for root in args.root]
    if args.include_env:
        roots.extend(_env_roots())
    ####
    if not roots:
        raise SystemExit("Provide at least one --root or use --include-env.")
    ####
    report = collect_samples(roots, Path(args.out).expanduser())
    print(json.dumps({"samples": len(report.samples), "skipped": len(report.skipped)}, indent=2))
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####

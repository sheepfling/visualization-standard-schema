from __future__ import annotations

import argparse

from vss.orb.corpus import build_orb_fixture_set


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SDJ, Cesium, and SOAP fixtures from an ORB archive.")
    parser.add_argument("--archive", default="reference/orb_format_collection/orb_format_collection.tar")
    parser.add_argument("--output", default="examples/orb-corpus")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()

    manifest = build_orb_fixture_set(
        args.archive,
        args.output,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        f"wrote {manifest.totals.get('parsed', 0)} parsed and "
        f"{manifest.totals.get('failed', 0)} failed ORB fixtures to {args.output}"
    )


if __name__ == "__main__":
    main()

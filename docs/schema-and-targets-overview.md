# Schema and Compile Targets Overview

## Purpose

This repository has one core schema surface and several target-specific compile surfaces. The intent is to keep the transport-agnostic model small, then adapt it into target-owned artifacts without hiding the differences between those targets.

## Core Schema

The canonical Python model layer lives in `src/vss/` and starts with:

- `EntityUpsertMessage` for transport-agnostic entity updates
- `VssScene` for scene-level payloads
- Pydantic validation, JSON loading, JSON file loading, and JSON schema export
- Canonical schema docs in `docs/sdj-schema.md`.

Core schema goals:

- keep the message envelope stable
- keep the scene model explicit
- make target mappings testable instead of implicit

## Compile Targets

### Cesium

Implementation:

- `src/vss/cesium/`
- compatibility facade in `src/vss/targets/`

Current outputs:

- CZML document compilation
- Cesium scene compilation
- Cesium viewer HTML generation

Use when the source is a VSS message or scene and the goal is browser-friendly Cesium output.

### SIMDIS

Implementation:

- `src/vss/simdis/`
- compatibility facade in `src/vss/targets/`

Current outputs:

- SIMDIS ASI text
- SIMDIS line-oriented text
- SIMDIS bundle JSON/file-set output

The current extraction covers the bundle split and the scene families already modeled in the repo, with explicit gaps called out in `docs/simdis-corpus-plan.md`.

### SOAP

Implementation:

- `src/vss/soap/`
- compatibility facade in `src/vss/targets/`

Current outputs:

- SOAP envelope XML
- SOAP bundle JSON/file-set output

The current scope and known gaps are documented in `docs/soap-extraction-plan.md`.

### ORB

Implementation:

- `src/vss/orb/`

Current outputs:

- lossless parse and dump of SOAP `.orb` scenario files
- typed scenario extraction for common SOAP blocks
- editor and authoring helpers for round-trip safe package generation

ORB is treated as a source format and authoring workflow rather than a downstream visualization target.

## Target Boundary Rules

- `vss.cesium`, `vss.simdis`, `vss.soap`, and `vss.orb` own their target logic.
- `vss.targets` is a compatibility facade only.
- `targets/capabilities/target-capabilities.json` defines the advertised target surface.
- `vss.capabilities` reports what a target claims and what a scene uses.

## Round-Trip Contracts

What the repo currently treats as round-trip safe:

- `EntityUpsertMessage` -> target output -> target-specific load/parse path where implemented
- `VssScene` -> Cesium/SIMDIS/SOAP output -> corresponding bundle or JSON file-set loaders
- SOAP `.orb` text -> lossless parser -> exact text dump
- SOAP `.orb` text -> typed ORB scenario -> exact text dump

## Known Gaps

The target-specific docs should remain the source of truth for gaps and lossiness:

- `docs/simdis-corpus-plan.md`
- `docs/soap-extraction-plan.md`

The intent is that gaps are explicit, named, and testable.

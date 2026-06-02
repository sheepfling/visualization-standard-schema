# SDJ Schema Documentation

This repo has two SDJ schema surfaces:

- Transport envelope: entity messages (`schemaVersion: 1.0.0`).
- Scene envelope: multi-object scene graphs (`schemaVersion: 1.0.0-scene`).

Both schemas are backed by `pydantic` models in `src/vss/models.py`, and the generated JSON Schema artifacts are stored under `schemas/`.

## Transport Message Schema (`1.0.0`)

Top-level required fields:

- `schemaVersion`: must be `"1.0.0"`
- `messageType`: must be `"entity.upsert"`
- `messageId`: non-empty string
- `timestamp`: ISO-8601 date-time string
- `source`: non-empty string
- `payload`: object

`payload` required fields:

- `entityId`: non-empty string
- `name`: non-empty string
- `position`: object with `longitudeDeg`, `latitudeDeg`, `altitudeM`

Optional payload fields:

- `category`: one of `air`, `ground`, `surface`, `subsurface`, `space`, `sensor`, `overlay`, `other`
- `orientation`: `headingDeg`, `pitchDeg`, `rollDeg`
- `style`: optional display hints (`label`, `iconUri`, `modelUri`, `colorRgba`)
- `attributes`: free-form object

Tracked schema:

- `schemas/vss-message.schema.json` (checked-in hand-authored schema)
- `schemas/vss-message.pydantic.schema.json` (generated from `EntityUpsertMessage`)

## Scene Schema (`1.0.0-scene`)

Top-level required fields:

- `schemaVersion`: must be `"1.0.0-scene"`
- `document`: scene metadata object
- `objects`: array of scene objects

`document` fields:

- `id`: non-empty string
- `name`: non-empty string
- `description`: optional string
- `created`: optional date-time
- `generator`: optional string
- `source`: optional string

`objects` is a discriminated union. Current supported `objectType` values are:

- `entity`
- `overlay`
- `path`
- `track`

Common base fields across all objects:

- `id`, `name` (both required)
- `style`: same style object used by message payload
- `attributes`: free-form object
- `source`: optional string
- `timestamp`: optional date-time

### `SceneEntity`

Required:

- `objectType`: `"entity"`
- `position`: WGS-84 point

Optional:

- `category`: same enum as payload
- `orientation`

### `SceneOverlay`

Required:

- `objectType`: `"overlay"`
- `position`: WGS-84 point
- `geometryType`: one of
  - `polyline`
  - `polygon`
  - `rectangle`
  - `corridor`
  - `ellipse`
  - `circle`
  - `wall`
  - `box`
  - `cylinder`
  - `ellipsoid`
  - `sphere`

At most one geometry object is used with the matching geometry field (`polyline`, `polygon`, etc.).

### `ScenePath` and `SceneTrack`

Both are sampled objects with:

- `samples`: list of `{timestamp, position}` samples (minimum length 2)
- `widthPx`: line width (default `2.0`, must be > 0)
- `clampToGround`: bool (default `false`)
- `orientation` (path-specific on `SceneTrack`)

## Geometry and Value Types

- `Wgs84Position`: object with `longitudeDeg`, `latitudeDeg`, `altitudeM`.
  - Longitude constrained to `[-180, 180]`.
  - Latitude constrained to `[-90, 90]`.
- `Style`: optional scene labels, URIs, and RGBA color array (`length 4`, 0-255 ints).
- `Orientation`: `headingDeg`, `pitchDeg`, `rollDeg` (`float`, optional).

## Canonical Generation

Use this command to regenerate generated schema artifacts after model changes:

```bash
python3 scripts/export_schema.py
```

This writes:

- `schemas/vss-message.pydantic.schema.json`
- `schemas/vss-scene.pydantic.schema.json`

## Notes

- The current tracked scene model is intentionally narrower than the legacy SDJ workbench schema, and target adapters document their own gaps and lossy boundaries in:
  - `docs/simdis-corpus-plan.md`
  - `docs/soap-extraction-plan.md`
  - `docs/cesium-sdj-gap-map.md`

from __future__ import annotations

import math
from typing import Any

from ..models import (
    SceneCircle,
    SceneCone,
    SceneBox,
    SceneCorridor,
    SceneCylinder,
    SceneConicSensor,
    SceneBearingFan,
    SceneCustomPatternSensor,
    SceneEllipse,
    SceneEllipsoid,
    SceneCovarianceEllipse,
    SceneFrustum,
    SceneOverlay,
    SceneKeyhole,
    SceneFan,
    ScenePlane,
    ScenePolyline,
    ScenePolylineVolume,
    SceneRangeRing,
    SceneRectangle,
    SceneSector2D,
    SceneSectorVolume,
    SceneHemisphere,
    SceneSphericalCap,
    SceneSphere,
    SceneUncertaintyEllipsoid,
    SceneTileset,
    SceneInterceptLine,
    SceneParticleSystem,
    SceneVoxel,
    SceneWall,
    Wgs84Position,
)
from ..util import safe_get, to_float, to_bool
from .czml_helpers import _extract_czml_packet_position, _packet_orientation, _packet_style, _packet_timestamp
from .czml_polylines import _packet_to_scene_polyline_overlay


def _packet_to_scene_overlay(packet: dict[str, Any], packet_id: str) -> SceneOverlay | None:
    polyline = safe_get(packet, "polyline")
    rectangle = safe_get(packet, "rectangle")
    corridor = safe_get(packet, "corridor")
    ellipse = safe_get(packet, "ellipse")
    wall = safe_get(packet, "wall")
    box = safe_get(packet, "box")
    cylinder = safe_get(packet, "cylinder")
    cone = safe_get(packet, "agi_conicSensor") or safe_get(packet, "cone")
    polyline_volume = safe_get(packet, "polylineVolume")
    plane = safe_get(packet, "plane")
    tileset = safe_get(packet, "tileset")
    ellipsoid = safe_get(packet, "ellipsoid")
    props = safe_get(packet, "properties")
    if isinstance(props, dict) and safe_get(props, "shapeType") == "voxel":
        voxel = safe_get(props, "voxel")
        if isinstance(voxel, dict):
            center = _extract_czml_packet_position(packet)
            if center is None:
                return None
            grid = safe_get(voxel, "grid")
            extensions = safe_get(voxel, "extensions")
            voxel_dimensions = safe_get(voxel, "dimensionsMeters")
            if isinstance(voxel_dimensions, (list, tuple)) and len(voxel_dimensions) == 3:
                dimensions = tuple(to_float(value) or 0.0 for value in voxel_dimensions)
            else:
                dimensions = None
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=center[0], latitudeDeg=center[1], altitudeM=center[2]),
                orientation=_packet_orientation(packet),
                geometryType="voxel",
                voxel=SceneVoxel(
                    semanticKind=safe_get(voxel, "semanticKind"),
                    grid=grid if isinstance(grid, dict) else {},
                    dimensionsMeters=dimensions,
                    note=safe_get(voxel, "note"),
                    extensions=extensions if isinstance(extensions, dict) else {},
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=_packet_timestamp(packet),
            )
    if isinstance(box, dict) and isinstance(props, dict) and safe_get(props, "shapeType") == "voxel":
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        dimensions = safe_get(box, "dimensions")
        if isinstance(dimensions, dict):
            cartesian = safe_get(dimensions, "cartesian")
        else:
            cartesian = dimensions
        parsed_dimensions = None
        if isinstance(cartesian, list) and len(cartesian) == 3:
            parsed_dimensions = tuple(to_float(value) or 0.0 for value in cartesian)
        voxel = safe_get(props, "voxel")
        if isinstance(voxel, dict):
            grid = safe_get(voxel, "grid")
            extensions = safe_get(voxel, "extensions")
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=center[0], latitudeDeg=center[1], altitudeM=center[2]),
                orientation=_packet_orientation(packet),
                geometryType="voxel",
                voxel=SceneVoxel(
                    semanticKind=safe_get(voxel, "semanticKind"),
                    grid=grid if isinstance(grid, dict) else {},
                    dimensionsMeters=parsed_dimensions,
                    note=safe_get(voxel, "note"),
                    extensions=extensions if isinstance(extensions, dict) else {},
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=_packet_timestamp(packet),
            )
    if isinstance(props, dict) and safe_get(props, "shapeType") in {"sector2d", "bearingFan", "customPatternSensor", "fan", "sectorVolume", "keyhole"}:
        shape_type = safe_get(props, "shapeType")
        sector = safe_get(props, "sector2d") or safe_get(props, "bearingFan") or safe_get(props, "customPatternSensor") or safe_get(props, "fan") or safe_get(props, "sectorVolume") or safe_get(props, "keyhole")
        polygon = safe_get(packet, "polygon")
        if isinstance(sector, dict) and isinstance(polygon, dict):
            positions = safe_get(polygon, "positions")
            if isinstance(positions, dict):
                positions = safe_get(positions, "cartographicDegrees")
            if isinstance(positions, list) and len(positions) >= 9:
                center = _extract_czml_packet_position(packet)
                if center is None:
                    return None
                outer_radius = to_float(safe_get(sector, "outerRadiusMeters"))
                azimuth_start = to_float(safe_get(sector, "azimuthStartDegrees"))
                azimuth_stop = to_float(safe_get(sector, "azimuthStopDegrees"))
                if outer_radius is None or azimuth_start is None or azimuth_stop is None:
                    return None
                segments = safe_get(sector, "segments")
                sector2d_value = SceneSector2D(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")),
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    heightMeters=to_float(safe_get(sector, "heightMeters")),
                    segments=segments if isinstance(segments, int) else 32,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "sector2d" else None
                bearing_fan_value = SceneBearingFan(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")),
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    heightMeters=to_float(safe_get(sector, "heightMeters")),
                    segments=segments if isinstance(segments, int) else 24,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "bearingFan" else None
                fan_value = SceneFan(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")),
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    heightMeters=to_float(safe_get(sector, "heightMeters")),
                    segments=segments if isinstance(segments, int) else 24,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "fan" else None
                pattern_pairs = safe_get(sector, "patternAzimuthElevationDegrees")
                if not isinstance(pattern_pairs, list):
                    pattern_pairs = []
                custom_pattern_value = SceneCustomPatternSensor(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")),
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    patternAzimuthElevationDegrees=[
                        tuple(map(float, pair))
                        for pair in pattern_pairs
                        if isinstance(pair, (list, tuple)) and len(pair) == 2
                    ],
                    heightMeters=to_float(safe_get(sector, "heightMeters")),
                    segments=segments if isinstance(segments, int) else 24,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "customPatternSensor" else None
                sector_volume_value = SceneSectorVolume(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")),
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    heightMeters=to_float(safe_get(sector, "heightMeters")),
                    segments=segments if isinstance(segments, int) else 32,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "sectorVolume" else None
                keyhole_value = SceneKeyhole(
                    innerRadiusMeters=to_float(safe_get(sector, "innerRadiusMeters")) or 0.0,
                    outerRadiusMeters=outer_radius,
                    azimuthStartDegrees=azimuth_start,
                    azimuthStopDegrees=azimuth_stop,
                    elevationStartDegrees=to_float(safe_get(sector, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(sector, "elevationStopDegrees")),
                    segments=segments if isinstance(segments, int) else 32,
                    mode=safe_get(sector, "mode"),
                    windingOrder=safe_get(sector, "windingOrder"),
                    closed=to_bool(safe_get(sector, "closed")) if safe_get(sector, "closed") is not None else None,
                ) if shape_type == "keyhole" else None
                return SceneOverlay(
                    objectType="overlay",
                    id=packet_id,
                    name=safe_get(packet, "name") or packet_id,
                    position=Wgs84Position(longitudeDeg=center[0], latitudeDeg=center[1], altitudeM=center[2]),
                    orientation=_packet_orientation(packet),
                    geometryType=shape_type,  # type: ignore[arg-type]
                    sector2d=sector2d_value,
                    bearingFan=bearing_fan_value,
                    customPatternSensor=custom_pattern_value,
                    fan=fan_value,
                    sectorVolume=sector_volume_value,
                    keyhole=keyhole_value,
                    style=_packet_style(packet, for_overlay=True),
                    attributes={"source": safe_get(packet, "source") or "czml"},
                    source=safe_get(packet, "source"),
                    timestamp=_packet_timestamp(packet),
                )
    polyline_overlay = _packet_to_scene_polyline_overlay(packet, packet_id)
    if polyline_overlay is not None:
        return polyline_overlay

    if isinstance(corridor, dict):
        corridor_positions = safe_get(corridor, "positions")
        if isinstance(corridor_positions, dict):
            corridor_positions = safe_get(corridor_positions, "cartographicDegrees")
        if not isinstance(corridor_positions, list) or len(corridor_positions) < 6:
            return None

        points: list[Wgs84Position] = []
        for i in range(0, len(corridor_positions) - 2, 3):
            lon = to_float(corridor_positions[i])
            lat = to_float(corridor_positions[i + 1])
            alt = to_float(corridor_positions[i + 2])
            if lon is None or lat is None or alt is None:
                return None
            points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
        if not points:
            return None

        corner_type = safe_get(corridor, "cornerType")
        if isinstance(corner_type, str):
            normalized_corner_type = corner_type.lower()
        else:
            normalized_corner_type = None
        width = to_float(safe_get(corridor, "width"))
        if width is None:
            return None

        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=points[0],
            geometryType="corridor",
            corridor=SceneCorridor(
                positions=points,
                widthMeters=width,
                heightMeters=to_float(safe_get(corridor, "height")),
                extrudedHeightMeters=to_float(safe_get(corridor, "extrudedHeight")),
                cornerType=normalized_corner_type,  # type: ignore[arg-type]
                clampToGround=bool(safe_get(corridor, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(rectangle, dict):
        coordinates = safe_get(rectangle, "coordinates")
        if isinstance(coordinates, dict):
            bounds = safe_get(coordinates, "wsenDegrees")
        else:
            bounds = safe_get(rectangle, "wsenDegrees")
        if not isinstance(bounds, list) or len(bounds) != 4:
            return None
        west = to_float(bounds[0])
        south = to_float(bounds[1])
        east = to_float(bounds[2])
        north = to_float(bounds[3])
        if west is None or south is None or east is None or north is None:
            return None
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(
                longitudeDeg=(west + east) / 2.0,
                latitudeDeg=(south + north) / 2.0,
                altitudeM=to_float(safe_get(rectangle, "height")) or 0.0,
            ),
            geometryType="rectangle",
            rectangle=SceneRectangle(
                westSouthEastNorthDegrees=(west, south, east, north),
                heightMeters=to_float(safe_get(rectangle, "height")),
                extrudedHeightMeters=to_float(safe_get(rectangle, "extrudedHeight")),
                rotationDegrees=to_float(safe_get(rectangle, "rotation")),
                stRotationDegrees=to_float(safe_get(rectangle, "stRotation")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(ellipse, dict):
        major = to_float(safe_get(ellipse, "semiMajorAxis"))
        minor = to_float(safe_get(ellipse, "semiMinorAxis"))
        if major is None or minor is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        if isinstance(props, dict) and safe_get(props, "shapeType") == "rangeRing":
            if abs(major - minor) > 1e-9:
                return None
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="rangeRing",
                rangeRing=SceneRangeRing(
                    radiusMeters=major,
                    heightMeters=to_float(safe_get(ellipse, "height")),
                    extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                    rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                    stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                    clampToGround=bool(safe_get(ellipse, "clampToGround")),
                    outlineWidthPx=to_float(safe_get(ellipse, "outlineWidth")) or 1.0,
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        if isinstance(props, dict) and safe_get(props, "shapeType") == "covarianceEllipse":
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="covarianceEllipse",
                covarianceEllipse=SceneCovarianceEllipse(
                    semiMajorAxisMeters=major,
                    semiMinorAxisMeters=minor,
                    heightMeters=to_float(safe_get(ellipse, "height")),
                    extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                    rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                    stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                    clampToGround=bool(safe_get(ellipse, "clampToGround")),
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        is_circle = abs(major - minor) <= 1e-9
        if is_circle:
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="circle",
                circle=SceneCircle(
                    radiusMeters=major,
                    heightMeters=to_float(safe_get(ellipse, "height")),
                    extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                    rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                    stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                    clampToGround=bool(safe_get(ellipse, "clampToGround")),
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="ellipse",
            ellipse=SceneEllipse(
                semiMajorAxisMeters=major,
                semiMinorAxisMeters=minor,
                heightMeters=to_float(safe_get(ellipse, "height")),
                extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                clampToGround=bool(safe_get(ellipse, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(wall, dict):
        wall_positions = safe_get(wall, "positions")
        if isinstance(wall_positions, dict):
            wall_positions = safe_get(wall_positions, "cartographicDegrees")
        if not isinstance(wall_positions, list) or len(wall_positions) < 6:
            return None

        points: list[Wgs84Position] = []
        for i in range(0, len(wall_positions) - 2, 3):
            lon = to_float(wall_positions[i])
            lat = to_float(wall_positions[i + 1])
            alt = to_float(wall_positions[i + 2])
            if lon is None or lat is None or alt is None:
                return None
            points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
        if not points:
            return None

        min_heights = safe_get(wall, "minimumHeights")
        max_heights = safe_get(wall, "maximumHeights")
        min_values = [to_float(value) for value in min_heights] if isinstance(min_heights, list) else None
        max_values = [to_float(value) for value in max_heights] if isinstance(max_heights, list) else None
        if min_values is not None and any(value is None for value in min_values):
            return None
        if max_values is not None and any(value is None for value in max_values):
            return None

        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=points[0],
            geometryType="wall",
            wall=SceneWall(
                positions=points,
                minimumHeightsMeters=[float(value) for value in min_values] if min_values is not None else None,
                maximumHeightsMeters=[float(value) for value in max_values] if max_values is not None else None,
                clampToGround=bool(safe_get(wall, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(box, dict):
        props = safe_get(packet, "properties")
        if isinstance(props, dict) and safe_get(props, "shapeType") == "frustum":
            dimensions = safe_get(box, "dimensions")
            if isinstance(dimensions, dict):
                dimensions = safe_get(dimensions, "cartesian")
            if not isinstance(dimensions, list) or len(dimensions) != 3:
                return None
            frustum_meta = safe_get(props, "frustum")
            if not isinstance(frustum_meta, dict):
                return None
            center = _extract_czml_packet_position(packet)
            if center is None:
                return None
            near = to_float(safe_get(frustum_meta, "nearMeters"))
            far = to_float(safe_get(frustum_meta, "farMeters"))
            if near is None or far is None:
                return None
            h_fov = to_float(safe_get(frustum_meta, "horizontalFovDegrees"))
            v_fov = to_float(safe_get(frustum_meta, "verticalFovDegrees"))
            inner_half = to_float(safe_get(frustum_meta, "innerHalfAngleDegrees"))
            outer_half = to_float(safe_get(frustum_meta, "outerHalfAngleDegrees"))
            aspect = to_float(safe_get(frustum_meta, "aspectRatio"))
            winding_order = safe_get(frustum_meta, "windingOrder")
            closed = safe_get(frustum_meta, "closed")
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=center[0], latitudeDeg=center[1], altitudeM=center[2]),
                orientation=_packet_orientation(packet),
                geometryType="frustum",
                frustum=SceneFrustum(
                    nearMeters=near,
                    farMeters=far,
                    horizontalFovDegrees=h_fov,
                    verticalFovDegrees=v_fov,
                    innerHalfAngleDegrees=inner_half,
                    outerHalfAngleDegrees=outer_half,
                    aspectRatio=aspect,
                    windingOrder=winding_order if isinstance(winding_order, str) else None,
                    closed=to_bool(closed) if closed is not None else None,
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        dimensions = safe_get(box, "dimensions")
        if isinstance(dimensions, dict):
            dimensions = safe_get(dimensions, "cartesian")
        if not isinstance(dimensions, list) or len(dimensions) != 3:
            return None
        x = to_float(dimensions[0])
        y = to_float(dimensions[1])
        z = to_float(dimensions[2])
        if x is None or y is None or z is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="box",
            box=SceneBox(dimensionsMeters=(x, y, z)),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(cylinder, dict):
        length = to_float(safe_get(cylinder, "length"))
        top_radius = to_float(safe_get(cylinder, "topRadius"))
        bottom_radius = to_float(safe_get(cylinder, "bottomRadius"))
        if length is None or top_radius is None or bottom_radius is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        number_of_sides = to_float(safe_get(cylinder, "numberOfVerticalLines"))
        slope = to_float(safe_get(cylinder, "slope"))
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="cylinder",
            cylinder=SceneCylinder(
                lengthMeters=length,
                topRadiusMeters=top_radius,
                bottomRadiusMeters=bottom_radius,
                numberOfSides=int(number_of_sides) if number_of_sides is not None else None,
                slope=slope,
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(cone, dict):
        radius = to_float(safe_get(cone, "radius"))
        inner_half_angle = to_float(safe_get(cone, "innerHalfAngle"))
        outer_half_angle = to_float(safe_get(cone, "outerHalfAngle"))
        if radius is None or inner_half_angle is None or outer_half_angle is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        min_clock_angle = to_float(safe_get(cone, "minimumClockAngle"))
        max_clock_angle = to_float(safe_get(cone, "maximumClockAngle"))
        show_intersection = safe_get(cone, "showIntersection")
        shape_type = safe_get(props, "shapeType") if isinstance(props, dict) else None
        min_clock_degrees = math.degrees(min_clock_angle) if min_clock_angle is not None else None
        max_clock_degrees = math.degrees(max_clock_angle) if max_clock_angle is not None else None
        inner_half_angle_degrees = math.degrees(inner_half_angle)
        outer_half_angle_degrees = math.degrees(outer_half_angle)
        if shape_type == "conicSensor":
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                orientation=_packet_orientation(packet),
                geometryType="conicSensor",
                conicSensor=SceneConicSensor(
                    radiusMeters=radius,
                    innerHalfAngleDegrees=inner_half_angle_degrees,
                    outerHalfAngleDegrees=outer_half_angle_degrees,
                    minimumClockAngleDegrees=min_clock_degrees,
                    maximumClockAngleDegrees=max_clock_degrees,
                    showIntersection=to_bool(show_intersection) if show_intersection is not None else None,
                    intersectionWidthPx=to_float(safe_get(cone, "intersectionWidth")),
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            orientation=_packet_orientation(packet),
            geometryType="cone",
            cone=SceneCone(
                radiusMeters=radius,
                innerHalfAngleDegrees=inner_half_angle_degrees,
                outerHalfAngleDegrees=outer_half_angle_degrees,
                minimumClockAngleDegrees=min_clock_degrees,
                maximumClockAngleDegrees=max_clock_degrees,
                showIntersection=to_bool(show_intersection) if show_intersection is not None else None,
                intersectionWidthPx=to_float(safe_get(cone, "intersectionWidth")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(polyline_volume, dict):
        polyline_positions = safe_get(polyline_volume, "positions")
        if isinstance(polyline_positions, dict):
            polyline_positions = safe_get(polyline_positions, "cartographicDegrees")
        if not isinstance(polyline_positions, list) or len(polyline_positions) < 6:
            return None

        points: list[Wgs84Position] = []
        for i in range(0, len(polyline_positions) - 2, 3):
            lon = to_float(polyline_positions[i])
            lat = to_float(polyline_positions[i + 1])
            alt = to_float(polyline_positions[i + 2])
            if lon is None or lat is None or alt is None:
                return None
            points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
        if not points:
            return None

        shape = safe_get(polyline_volume, "shape")
        if isinstance(shape, dict):
            shape = safe_get(shape, "cartesian")
        if not isinstance(shape, list) or len(shape) < 6 or len(shape) % 2 != 0:
            return None
        shape_points: list[tuple[float, float]] = []
        for i in range(0, len(shape), 2):
            x = to_float(shape[i])
            y = to_float(shape[i + 1])
            if x is None or y is None:
                return None
            shape_points.append((x, y))
        corner_type = safe_get(polyline_volume, "cornerType")
        if isinstance(corner_type, str):
            corner_type = corner_type.lower()
        else:
            corner_type = None

        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=points[0],
            geometryType="polylineVolume",
            polylineVolume=ScenePolylineVolume(
                positions=points,
                shapePositions=shape_points,
                cornerType=corner_type,  # type: ignore[arg-type]
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(plane, dict):
        plane_data = safe_get(plane, "plane")
        dimensions = safe_get(plane, "dimensions")
        if isinstance(plane_data, dict):
            normal = safe_get(plane_data, "normal")
            if isinstance(normal, dict):
                normal = safe_get(normal, "cartesian")
            distance = to_float(safe_get(plane_data, "distance"))
        else:
            normal = None
            distance = None
        if isinstance(dimensions, dict):
            dimensions = safe_get(dimensions, "cartesian")
        if (
            not isinstance(normal, list)
            or len(normal) != 3
            or distance is None
            or not isinstance(dimensions, list)
            or len(dimensions) != 2
        ):
            return None
        nx = to_float(normal[0])
        ny = to_float(normal[1])
        nz = to_float(normal[2])
        width = to_float(dimensions[0])
        height = to_float(dimensions[1])
        center = _extract_czml_packet_position(packet)
        if None in (nx, ny, nz, width, height) or center is None:
            return None
        lon, lat, alt = center
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="plane",
            plane=ScenePlane(
                normal=(nx, ny, nz),
                distanceMeters=distance,
                widthMeters=width,
                heightMeters=height,
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(tileset, dict):
        uri = safe_get(tileset, "uri")
        if not isinstance(uri, str) or not uri.strip():
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="tileset",
            tileset=SceneTileset(uri=uri.strip()),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(ellipsoid, dict):
        radii = safe_get(ellipsoid, "radii")
        if isinstance(radii, dict):
            radii = safe_get(radii, "cartesian")
        if not isinstance(radii, list) or len(radii) != 3:
            return None
        rx = to_float(radii[0])
        ry = to_float(radii[1])
        rz = to_float(radii[2])
        if rx is None or ry is None or rz is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        if isinstance(props, dict) and safe_get(props, "shapeType") == "hemisphere":
            if abs(rx - ry) > 1e-9 or abs(ry - rz) > 1e-9:
                return None
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="hemisphere",
                hemisphere=SceneHemisphere(radiusMeters=rx),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        if isinstance(props, dict) and safe_get(props, "shapeType") == "sphericalCap":
            spherical_cap = safe_get(props, "sphericalCap")
            if not isinstance(spherical_cap, dict):
                return None
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="sphericalCap",
                sphericalCap=SceneSphericalCap(
                    radiusMeters=to_float(safe_get(spherical_cap, "radiusMeters")) or rx,
                    innerRadiusMeters=to_float(safe_get(spherical_cap, "innerRadiusMeters")),
                    portion=safe_get(spherical_cap, "portion"),
                    azimuthStartDegrees=to_float(safe_get(spherical_cap, "azimuthStartDegrees")),
                    azimuthStopDegrees=to_float(safe_get(spherical_cap, "azimuthStopDegrees")),
                    segments=safe_get(spherical_cap, "segments") if isinstance(safe_get(spherical_cap, "segments"), int) else None,
                    windingOrder=safe_get(spherical_cap, "windingOrder"),
                    closed=to_bool(safe_get(spherical_cap, "closed")) if safe_get(spherical_cap, "closed") is not None else None,
                    azimuthSegments=safe_get(spherical_cap, "azimuthSegments") if isinstance(safe_get(spherical_cap, "azimuthSegments"), int) else None,
                    elevationSegments=safe_get(spherical_cap, "elevationSegments") if isinstance(safe_get(spherical_cap, "elevationSegments"), int) else None,
                    elevationStartDegrees=to_float(safe_get(spherical_cap, "elevationStartDegrees")),
                    elevationStopDegrees=to_float(safe_get(spherical_cap, "elevationStopDegrees")),
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        if isinstance(props, dict) and safe_get(props, "shapeType") == "uncertaintyEllipsoid":
            uncertainty_ellipsoid = safe_get(props, "uncertaintyEllipsoid")
            if not isinstance(uncertainty_ellipsoid, dict):
                return None
            radii_values = safe_get(uncertainty_ellipsoid, "radiiMeters")
            if not isinstance(radii_values, list) or len(radii_values) != 3:
                return None
            rx_u = to_float(radii_values[0])
            ry_u = to_float(radii_values[1])
            rz_u = to_float(radii_values[2])
            if rx_u is None or ry_u is None or rz_u is None:
                return None
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="uncertaintyEllipsoid",
                uncertaintyEllipsoid=SceneUncertaintyEllipsoid(
                    radiiMeters=(rx_u, ry_u, rz_u),
                    slicePartitions=safe_get(uncertainty_ellipsoid, "slicePartitions") if isinstance(safe_get(uncertainty_ellipsoid, "slicePartitions"), int) else None,
                    stackPartitions=safe_get(uncertainty_ellipsoid, "stackPartitions") if isinstance(safe_get(uncertainty_ellipsoid, "stackPartitions"), int) else None,
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        if isinstance(props, dict) and safe_get(props, "shapeType") == "particleSystem":
            particle_system = safe_get(props, "particleSystem")
            if not isinstance(particle_system, dict):
                return None
            image_size = safe_get(particle_system, "imageSize")
            image_size_tuple = None
            if isinstance(image_size, list) and len(image_size) == 2:
                width = to_float(image_size[0])
                height = to_float(image_size[1])
                if width is not None and height is not None:
                    image_size_tuple = (width, height)
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="particleSystem",
                particleSystem=SceneParticleSystem(
                    asset=safe_get(particle_system, "asset"),
                    image=safe_get(particle_system, "image"),
                    emitter=safe_get(particle_system, "emitter"),
                    emissionRate=to_float(safe_get(particle_system, "emissionRate")),
                    lifetimeSeconds=to_float(safe_get(particle_system, "lifetimeSeconds") or safe_get(particle_system, "lifetime")),
                    particleLifeSeconds=to_float(safe_get(particle_system, "particleLifeSeconds") or safe_get(particle_system, "particleLife")),
                    minimumParticleLifeSeconds=to_float(safe_get(particle_system, "minimumParticleLifeSeconds") or safe_get(particle_system, "minimumParticleLife")),
                    maximumParticleLifeSeconds=to_float(safe_get(particle_system, "maximumParticleLifeSeconds") or safe_get(particle_system, "maximumParticleLife")),
                    speedMetersPerSecond=to_float(safe_get(particle_system, "speedMetersPerSecond") or safe_get(particle_system, "speed")),
                    minimumSpeedMetersPerSecond=to_float(safe_get(particle_system, "minimumSpeedMetersPerSecond") or safe_get(particle_system, "minimumSpeed")),
                    maximumSpeedMetersPerSecond=to_float(safe_get(particle_system, "maximumSpeedMetersPerSecond") or safe_get(particle_system, "maximumSpeed")),
                    scale=to_float(safe_get(particle_system, "scale")),
                    startScale=to_float(safe_get(particle_system, "startScale")),
                    endScale=to_float(safe_get(particle_system, "endScale")),
                    imageSize=image_size_tuple,
                    startColor=_rgba_to_float_color(safe_get(particle_system, "startColor")),
                    endColor=_rgba_to_float_color(safe_get(particle_system, "endColor")),
                ),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        if abs(rx - ry) <= 1e-9 and abs(ry - rz) <= 1e-9:
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="sphere",
                sphere=SceneSphere(radiusMeters=rx),
                style=_packet_style(packet, for_overlay=True),
                attributes={"source": safe_get(packet, "source") or "czml"},
                source=safe_get(packet, "source"),
                timestamp=None,
            )
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="ellipsoid",
            ellipsoid=SceneEllipsoid(radiiMeters=(rx, ry, rz)),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    return None


def _rgba_to_float_color(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, dict):
        return None
    rgba = safe_get(value, "rgba")
    if not isinstance(rgba, list) or len(rgba) != 4:
        return None
    channels: list[float] = []
    for component in rgba:
        number = to_float(component)
        if number is None:
            return None
        channels.append(number / 255.0 if number > 1.0 else number)
    return (channels[0], channels[1], channels[2], channels[3])


__all__ = [
    "_packet_to_scene_overlay",
]

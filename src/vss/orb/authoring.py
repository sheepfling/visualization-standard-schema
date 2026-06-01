from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..util import write_text_file
from .editor import OrbScenarioEditor
from .io import parse_orb_text
from .typed import OrbPrimitive, OrbScenario


@dataclass(slots=True)
class FixedSiteSpec:
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0
    parent: str = "Earth"
    shape: str = "STATION"
    color: str | None = None
    icon: bool = True
    label: bool = True
    subpoint: bool = False
    orbit_thickness: float = 1.0
    above_terrain: bool = False


@dataclass(slots=True)
class WorldViewSpec:
    name: str
    observer: str
    coordinate_system: str
    icon_list: list[str] = field(default_factory=list)
    label_list: list[str] = field(default_factory=list)
    viewangles: tuple[OrbPrimitive, ...] | None = None


@dataclass(slots=True)
class ContourGridSpec:
    name: str
    dimension: tuple[int, int, int]
    altitude: float
    domain: tuple[OrbPrimitive, ...]
    domdlt: float
    analysis: str = ".None."
    plane: str = "XY"
    output_format: str | None = None
    contour_enabled: bool | None = None


@dataclass(slots=True)
class CoordinateSystemSpec:
    name: str
    cs_type: str = "CSBASIS"
    axes: bool = False
    track: tuple[OrbPrimitive, ...] | None = None
    align: tuple[OrbPrimitive, ...] | None = None
    sweep: tuple[OrbPrimitive, ...] | None = None
    origin: tuple[OrbPrimitive, ...] | None = None


@dataclass(slots=True)
class ObserverPlatformSpec:
    name: str
    state: tuple[OrbPrimitive, ...]
    parent: str = "Earth"
    platform_type: str = "ECR_FIXED"
    coordinate_system: str | None = None
    color: str | None = "Magenta"
    orbit_thickness: float = 1.0


@dataclass(slots=True)
class SiteBundleSpec:
    site: FixedSiteSpec
    observer: ObserverPlatformSpec
    coordinate_system: CoordinateSystemSpec
    view: WorldViewSpec
    grid: ContourGridSpec | None = None


@dataclass(slots=True)
class DisplayDefaultsSpec:
    map_color: str | None = None
    world_pcolor: str | None = None
    xyp_plot_color: str | None = None
    data_pcolor: str | None = None
    text_pcolor: str | None = None
    world_scolor: str | None = None
    xyp_scolor: str | None = None
    data_scolor: str | None = None
    icon_scale: float | None = None
    line_thickness: float | None = None
    map_line_thickness: float | None = None
    limb: bool | None = None
    worldmap: bool | None = None
    lighting: bool | None = None
    atmosphere_shader: bool | None = None


@dataclass(slots=True)
class AnalysisSpec:
    name: str
    variable: tuple[OrbPrimitive, ...]
    variable_details: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = field(default_factory=dict)
    bounds: tuple[OrbPrimitive, OrbPrimitive] | None = None
    color: str = "Red"
    marker: str = "*"
    link: bool = False
    cue: bool = False


@dataclass(slots=True)
class DerivedVariableSpec:
    value: tuple[OrbPrimitive, ...]
    distanceu: tuple[OrbPrimitive, ...] | None = None
    timeu: tuple[OrbPrimitive, ...] | None = None
    angleu: tuple[OrbPrimitive, ...] | None = None
    comment: str | None = None
    extra_details: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisTemplateSpec:
    name: str
    derived_variable: DerivedVariableSpec
    bounds: tuple[OrbPrimitive, OrbPrimitive] | None = None
    color: str = "Red"
    marker: str = "*"
    link: bool = False
    cue: bool = False


@dataclass(slots=True)
class OrbPackageSpec:
    site_bundle: SiteBundleSpec | None = None
    display_defaults: DisplayDefaultsSpec | None = None
    analyses: list[AnalysisSpec] = field(default_factory=list)
    analysis_templates: list[AnalysisTemplateSpec] = field(default_factory=list)
    stabilizations: list[str] = field(default_factory=list)
    extra_fixed_sites: list[FixedSiteSpec] = field(default_factory=list)
    extra_coordinate_systems: list[CoordinateSystemSpec] = field(default_factory=list)
    extra_observer_platforms: list[ObserverPlatformSpec] = field(default_factory=list)
    extra_world_views: list[WorldViewSpec] = field(default_factory=list)
    extra_contour_grids: list[ContourGridSpec] = field(default_factory=list)
    revision: int = 56
    file_type: str = "SOAP_SCENARIO_FILE"


def add_fixed_site(editor: OrbScenarioEditor, spec: FixedSiteSpec) -> None:
    properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
        "STATE": (spec.latitude_deg, spec.longitude_deg, spec.altitude_m),
        "PLAT": spec.parent,
        "SHAPE": spec.shape,
        "ICON": spec.icon,
        "LABEL": spec.label,
        "SUBPOINT": spec.subpoint,
        "ORBIT_THICKNESS": spec.orbit_thickness,
        "ABOVE_TERR": spec.above_terrain,
    }
    if spec.color is not None:
        properties["COLOR"] = spec.color
    editor.create_platform("ECR_FIXED", spec.name, properties=properties)


def add_world_view_from_spec(editor: OrbScenarioEditor, spec: WorldViewSpec) -> None:
    editor.add_world_view(
        spec.name,
        observer=spec.observer,
        coordinate_system=spec.coordinate_system,
        icon_list=spec.icon_list or None,
        label_list=spec.label_list or None,
        viewangles=spec.viewangles,
    )


def add_contour_grid(editor: OrbScenarioEditor, spec: ContourGridSpec) -> None:
    editor.create_grid(
        "CONTOUR",
        spec.name,
        properties={
            "DIMENSION": spec.dimension,
            "ALTITUDE": spec.altitude,
            "DOMAIN": spec.domain,
            "DOMDLT": spec.domdlt,
            "ANALYSIS": spec.analysis,
            "PLANE": spec.plane,
            **({"OUTPUT_FORMAT": spec.output_format} if spec.output_format is not None else {}),
            **({"CONTOUR_ENABLED": spec.contour_enabled} if spec.contour_enabled is not None else {}),
        },
    )


def add_coordinate_system(editor: OrbScenarioEditor, spec: CoordinateSystemSpec) -> None:
    properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
        "AXES": spec.axes,
    }
    if spec.track is not None:
        properties["TRACK"] = spec.track
    if spec.align is not None:
        properties["ALIGN"] = spec.align
    if spec.sweep is not None:
        properties["SWEEP"] = spec.sweep
    if spec.origin is not None:
        properties["ORIGIN"] = spec.origin
    editor.create_coordinate_system(spec.cs_type, spec.name, properties=properties)


def add_observer_platform(editor: OrbScenarioEditor, spec: ObserverPlatformSpec) -> None:
    properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
        "STATE": spec.state,
        "PLAT": spec.parent,
        "SHAPE": "VIEW_ONLY",
        "ICON": True,
        "LABEL": True,
        "SUBPOINT": False,
        "ORBIT_THICKNESS": spec.orbit_thickness,
    }
    if spec.coordinate_system is not None:
        properties["CS"] = spec.coordinate_system
    if spec.color is not None:
        properties["COLOR"] = spec.color
    editor.create_platform(spec.platform_type, spec.name, properties=properties)


def add_site_bundle(editor: OrbScenarioEditor, spec: SiteBundleSpec) -> None:
    add_fixed_site(editor, spec.site)
    add_coordinate_system(editor, spec.coordinate_system)
    add_observer_platform(editor, spec.observer)
    add_world_view_from_spec(editor, spec.view)
    if spec.grid is not None:
        add_contour_grid(editor, spec.grid)


def add_display_defaults(editor: OrbScenarioEditor, spec: DisplayDefaultsSpec) -> None:
    properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {}
    if spec.map_color is not None:
        properties["MAP_COLOR"] = spec.map_color
    if spec.world_pcolor is not None:
        properties["WORLD_PCOLOR"] = spec.world_pcolor
    if spec.xyp_plot_color is not None:
        properties["XYPLOT_PCOLOR"] = spec.xyp_plot_color
    if spec.data_pcolor is not None:
        properties["DATA_PCOLOR"] = spec.data_pcolor
    if spec.text_pcolor is not None:
        properties["TEXT_PCOLOR"] = spec.text_pcolor
    if spec.world_scolor is not None:
        properties["WORLD_SCOLOR"] = spec.world_scolor
    if spec.xyp_scolor is not None:
        properties["XYPLOT_SCOLOR"] = spec.xyp_scolor
    if spec.data_scolor is not None:
        properties["DATA_SCOLOR"] = spec.data_scolor
    if spec.icon_scale is not None:
        properties["ICON_SCALE"] = spec.icon_scale
    if spec.line_thickness is not None:
        properties["LINE_THICKNESS"] = spec.line_thickness
    if spec.map_line_thickness is not None:
        properties["MAP_LINE_THICKNESS"] = spec.map_line_thickness
    if spec.limb is not None:
        properties["LIMB"] = spec.limb
    if spec.worldmap is not None:
        properties["WORLDMAP"] = spec.worldmap
    if spec.lighting is not None:
        properties["LIGHTING"] = spec.lighting
    if spec.atmosphere_shader is not None:
        properties["ATMOSPHERE_SHADER"] = spec.atmosphere_shader
    if not properties:
        return

    if any(block.block_kind == "CONFIG" for block in editor.document.define_blocks):
        for key, value in properties.items():
            editor.set_config_property(key, value)
    else:
        editor.create_config(properties=properties)


def add_analysis(editor: OrbScenarioEditor, spec: AnalysisSpec) -> None:
    properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
        "VARIABLE": spec.variable,
        "COLOR": spec.color,
        "MARKER": spec.marker,
        "LINK": spec.link,
        "CUE": spec.cue,
    }
    if spec.bounds is not None:
        properties["BOUNDS"] = spec.bounds
    editor.create_analysis(spec.name, properties=properties, variable_details=spec.variable_details)


def normalize_analysis_template(spec: AnalysisTemplateSpec) -> AnalysisSpec:
    derived = spec.derived_variable
    variable_details: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {}
    if derived.distanceu is not None:
        variable_details["DISTANCEU"] = derived.distanceu
    if derived.timeu is not None:
        variable_details["TIMEU"] = derived.timeu
    if derived.angleu is not None:
        variable_details["ANGLEU"] = derived.angleu
    if derived.comment is not None:
        variable_details["COMMENT"] = derived.comment
    variable_details.update(derived.extra_details)
    return AnalysisSpec(
        name=spec.name,
        variable=derived.value,
        variable_details=variable_details,
        bounds=spec.bounds,
        color=spec.color,
        marker=spec.marker,
        link=spec.link,
        cue=spec.cue,
    )


def add_analysis_template(editor: OrbScenarioEditor, spec: AnalysisTemplateSpec) -> None:
    add_analysis(editor, normalize_analysis_template(spec))


def build_orb_package(spec: OrbPackageSpec) -> OrbScenarioEditor:
    editor = OrbScenarioEditor(document=parse_orb_text(_seed_orb_text(spec.revision, spec.file_type)))
    if spec.display_defaults is not None:
        add_display_defaults(editor, spec.display_defaults)
    if spec.site_bundle is not None:
        add_site_bundle(editor, spec.site_bundle)
    for analysis_spec in spec.analyses:
        add_analysis(editor, analysis_spec)
    for analysis_template_spec in spec.analysis_templates:
        add_analysis_template(editor, analysis_template_spec)
    for stabilization_name in spec.stabilizations:
        editor.create_stabilization(stabilization_name)
    for site_spec in spec.extra_fixed_sites:
        add_fixed_site(editor, site_spec)
    for cs_spec in spec.extra_coordinate_systems:
        add_coordinate_system(editor, cs_spec)
    for observer_spec in spec.extra_observer_platforms:
        add_observer_platform(editor, observer_spec)
    for view_spec in spec.extra_world_views:
        add_world_view_from_spec(editor, view_spec)
    for grid_spec in spec.extra_contour_grids:
        add_contour_grid(editor, grid_spec)
    return editor


def write_orb_package(spec: OrbPackageSpec, path: str | Path) -> Path:
    return write_text_file(path, build_orb_package(spec).to_text(), encoding="utf-8", trailing_newline=False)


def load_orb_package(path: str | Path) -> OrbScenario:
    return OrbScenario.from_document(parse_orb_text(Path(path).read_text(encoding="utf-8")))


def _seed_orb_text(revision: int, file_type: str) -> str:
    return f"{revision} revision\n{file_type}\n"

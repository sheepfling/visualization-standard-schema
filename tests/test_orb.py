from pathlib import Path

import pytest

from vss.orb import (
    AnalysisSpec,
    AnalysisTemplateSpec,
    ContourGridSpec,
    CoordinateSystemSpec,
    DerivedVariableSpec,
    DisplayDefaultsSpec,
    FixedSiteSpec,
    ObserverPlatformSpec,
    OrbDefineBlock,
    OrbPackageSpec,
    OrbStabilization,
    SiteBundleSpec,
    WorldViewSpec,
    add_contour_grid,
    add_coordinate_system,
    add_fixed_site,
    add_observer_platform,
    add_site_bundle,
    add_world_view_from_spec,
    build_orb_package,
    dump_orb_text,
    edit_orb_scenario_text,
    load_orb_package,
    normalize_analysis_template,
    parse_orb_scenario_text,
    parse_orb_text,
    write_orb_package,
)

ORB_SAMPLE_DIR = Path("reference/orb_samples")
ORB_SNIPPET = """56 revision
SOAP_SCENARIO_FILE
DEFINE UNITS
\tDISTANCE KILOMETERS
\tTIME HOURS
DEFINE GROUP PLATFORM_GROUP  "{New}"
\tPLATLIST "ON"
     ".Earth CI Observer"
     "Air"
     "END_OF_INPUT"
DEFINE VIEW WORLD  ".Moon CI Observer View" ".Moon CI Observer" ".Moon Pointing"
  CONES SET
\tCONE_LIST
     "END_OF_INPUT"
  ICONS ON
\tICON_LIST "ON"
     "ABQ"
     "Air(Smooth)"
     "END_OF_INPUT"
"""
ORB_TYPED_SNIPPET = """56 revision
SOAP_SCENARIO_FILE
DEFINE UNITS
\tDISTANCE KILOMETERS
\tTIME SECONDS
\tANGLE DEGREES
\tANGLE_SHIFT OFF
DEFINE CLOCK
\tEPOCH  1994 11 1 0 0 0
\tSIMULATION_TIME 9840
\tPAUSE ON
\tREAL_TIME OFF
\tTIME_STEP 60
DEFINE CONFIG
\tVERSION "Version 15.3.2"
\tCLOCK_FONT_COLOR Gray
\tTRANSCTL -637813.7
\tCLOCK_CONE_GRID
\tCLOCK_COUNT 12
\tCONE_COUNT 6
\tGRID_COLOR Magenta
\tGRID_END
\tDRIVER
\tBORDER OFF
\tDRIVER_END
\tAUTO_LOAD OFF
"""
ORB_EXPANDED_SNIPPET = """54 revision
SOAP_SCENARIO_FILE
DEFINE GROUP PLATFORM_GROUP  "{New}"
\tPLATLIST "ON"
     ".Earth CI Observer"
     "Air"
     "END_OF_INPUT"
DEFINE PLATFORM AIRROUTE  "Air"
\tSTATE  2004 2 1 0 0 0 2004 2 11 0 0 0
  PLAT  "Earth"
  WAYPOINT_TYPE BY_SPEED
  WAYPOINT 33.93 -118.4 1 0 0.205778
  WAYPOINT 38.82 -104.72 1 0 0.205778
  SHAPE AIRCRAFT
  SMOOTH OFF
DEFINE TRAJECTORY  "Air Trajectory"
\tCS  "ECR"
\tPLATFORM  "Air"
\tTRAJECTORY_CHOICE RELATIVE FORWARD 49000
\t\t2001 4 10 0 0 0
\t\t2001 4 10 1 1 1
\tREFRESH_CHOICE GENERATE
DEFINE VIEW WORLD  ".Moon CI Observer View" ".Moon CI Observer" ".Moon Pointing"
  CONES SET
\tCONE_LIST
     "END_OF_INPUT"
  ICONS ON
\tICON_LIST "ON"
     "ABQ"
     "Air(Smooth)"
     "END_OF_INPUT"
  LABELS ON
\tLABEL_LIST "ON"
     "Air(Smooth)"
     "END_OF_INPUT"
  VIEWANGLES -90 90
"""
ORB_REMAINDER_SNIPPET = """54 revision
SOAP_SCENARIO_FILE
DEFINE MAPCENTER
\tMAPFILE wmedium.wld
DEFINE SPICE
\tSPICEFILE leap.tls
\tSPICEFILE constant.tpc
DEFINE CS CSBASIS  "ECR"
  AXES OFF
  TRACK Z LONLAT 0 90
  ALIGN RESULTANT Y LONLAT 0 0
  SWEEP Z NOSWEEP
  ORIGIN  ".Host Platform" ".Host Platform"
DEFINE ANALYSIS  ".GM Earth"
  VARIABLE CONSTANT 398600.5
    DISTANCEU KILOMETERS 3
    TIMEU SECONDS -2
    ANGLEU DEGREES 0
    COMMENT  "Earth GM"
  BOUNDS 0 10
  COLOR Red
DEFINE GRID CONTOUR  ".Earth Lat/Lon Grid"
  DIMENSION 8 8 10
\tALTITUDE 0
  DOMAIN 0 86400
\tDOMDLT 300
  ANALYSIS  ".None."
  PLANE XY
"""

def test_orb_parser_preserves_round_trip_text() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    assert dump_orb_text(document) == ORB_SNIPPET

def test_orb_parser_extracts_define_blocks() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    assert [block.block_kind for block in document.define_blocks] == ["UNITS", "GROUP", "VIEW"]
    assert isinstance(document.define_blocks[0], OrbDefineBlock)
    assert document.entries[0].tokens == ("56", "revision")
    assert document.entries[1].tokens == ("SOAP_SCENARIO_FILE",)

def test_orb_parser_builds_indented_child_lists() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    group_block = document.define_blocks[1]
    assert group_block.define_tokens == ("GROUP", "PLATFORM_GROUP", "{New}")
    platlist = group_block.children[0]
    assert platlist.keyword == "PLATLIST"
    assert [child.tokens[0] for child in platlist.children] == [".Earth CI Observer", "Air", "END_OF_INPUT"]

    view_block = document.define_blocks[2]
    icons = view_block.children[1]
    assert icons.keyword == "ICONS"
    icon_list = icons.children[0]
    assert icon_list.keyword == "ICON_LIST"
    assert [child.tokens[0] for child in icon_list.children] == ["ABQ", "Air(Smooth)", "END_OF_INPUT"]

def test_orb_parser_closes_sentinel_sections() -> None:
    document = parse_orb_text(ORB_TYPED_SNIPPET)
    config_block = document.define_blocks[2]
    assert [child.keyword for child in config_block.children[-2:]] == ["DRIVER", "AUTO_LOAD"]
    driver = config_block.children[-2]
    assert [child.keyword for child in driver.children] == ["BORDER", "DRIVER_END"]

def test_orb_typed_scenario_extracts_units_clock_and_config() -> None:
    scenario = parse_orb_scenario_text(ORB_TYPED_SNIPPET)
    assert scenario.revision == 56
    assert scenario.file_type == "SOAP_SCENARIO_FILE"
    assert scenario.units is not None
    assert scenario.clock is not None
    assert scenario.config is not None

    assert scenario.units.distance == "KILOMETERS"
    assert scenario.units.time == "SECONDS"
    assert scenario.units.angle_shift is False

    assert scenario.clock.epoch == (1994, 11, 1, 0, 0, 0)
    assert scenario.clock.simulation_time == 9840
    assert scenario.clock.pause is True
    assert scenario.clock.real_time is False
    assert scenario.clock.time_step == 60

    assert scenario.config.properties["VERSION"] == "Version 15.3.2"
    assert scenario.config.properties["CLOCK_FONT_COLOR"] == "Gray"
    assert scenario.config.properties["TRANSCTL"] == -637813.7
    assert scenario.config.clock_cone_grid["CLOCK_COUNT"] == 12
    assert scenario.config.clock_cone_grid["GRID_COLOR"] == "Magenta"
    assert scenario.config.driver["BORDER"] is False
    assert scenario.config.properties["AUTO_LOAD"] is False

def test_orb_typed_scenario_extracts_group_platform_trajectory_and_view() -> None:
    scenario = parse_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    assert len(scenario.groups) == 1
    assert len(scenario.platforms) == 1
    assert len(scenario.trajectories) == 1
    assert len(scenario.views) == 1

    group = scenario.groups[0]
    assert group.group_type == "PLATFORM_GROUP"
    assert group.name == "{New}"
    assert group.properties["PLATLIST"] is True
    assert group.lists["PLATLIST"] == [".Earth CI Observer", "Air", "END_OF_INPUT"]

    platform = scenario.platforms[0]
    assert platform.platform_type == "AIRROUTE"
    assert platform.name == "Air"
    assert platform.properties["PLAT"] == "Earth"
    assert platform.properties["WAYPOINT_TYPE"] == "BY_SPEED"
    assert platform.repeated["WAYPOINT"][0] == (33.93, -118.4, 1, 0, 0.205778)
    assert platform.properties["SMOOTH"] is False

    trajectory = scenario.trajectories[0]
    assert trajectory.name == "Air Trajectory"
    assert trajectory.properties["CS"] == "ECR"
    assert trajectory.properties["TRAJECTORY_CHOICE"] == ("RELATIVE", "FORWARD", 49000)
    assert trajectory.trajectory_rows[1] == (2001, 4, 10, 1, 1, 1)

    view = scenario.views[0]
    assert view.view_type == "WORLD"
    assert view.name == ".Moon CI Observer View"
    assert view.observer == ".Moon CI Observer"
    assert view.coordinate_system == ".Moon Pointing"
    assert view.sets["CONES"] is True
    assert view.lists["ICON_LIST"] == ["ABQ", "Air(Smooth)", "END_OF_INPUT"]
    assert view.properties["ICON_LIST"] is True
    assert view.properties["VIEWANGLES"] == (-90, 90)

@pytest.mark.parametrize(
    "sample_path",
    [
        ORB_SAMPLE_DIR / "air_route_simple.orb",
        ORB_SAMPLE_DIR / "demo.orb",
    ],
)
def test_real_orb_files_round_trip_exactly(sample_path: Path) -> None:
    raw = sample_path.read_text(encoding="utf-8")
    assert dump_orb_text(parse_orb_text(raw)) == raw

def test_orb_typed_scenario_extracts_mapcenter_spice_cs_analysis_and_grid() -> None:
    scenario = parse_orb_scenario_text(ORB_REMAINDER_SNIPPET)
    assert len(scenario.map_centers) == 1
    assert len(scenario.spices) == 1
    assert len(scenario.coordinate_systems) == 1
    assert len(scenario.analyses) == 1
    assert len(scenario.grids) == 1

    assert scenario.map_centers[0].properties["MAPFILE"] == "wmedium.wld"
    assert scenario.spices[0].repeated["SPICEFILE"] == ["leap.tls", "constant.tpc"]

    cs = scenario.coordinate_systems[0]
    assert cs.cs_type == "CSBASIS"
    assert cs.name == "ECR"
    assert cs.properties["AXES"] is False
    assert cs.properties["TRACK"] == ("Z", "LONLAT", 0, 90)

    analysis = scenario.analyses[0]
    assert analysis.name == ".GM Earth"
    assert analysis.properties["VARIABLE"] == ("CONSTANT", 398600.5)
    assert analysis.variable_details["DISTANCEU"] == ("KILOMETERS", 3)
    assert analysis.variable_details["COMMENT"] == "Earth GM"

    grid = scenario.grids[0]
    assert grid.grid_type == "CONTOUR"
    assert grid.name == ".Earth Lat/Lon Grid"
    assert grid.properties["DIMENSION"] == (8, 8, 10)
    assert grid.properties["PLANE"] == "XY"

def test_orb_editor_updates_existing_lines_and_round_trips() -> None:
    editor = edit_orb_scenario_text(ORB_TYPED_SNIPPET)
    editor.set_config_property("AUTO_LOAD", True)
    editor.set_units_property("TIME", "HOURS")
    updated = editor.refresh()

    assert updated.config is not None
    assert updated.units is not None
    assert updated.config.properties["AUTO_LOAD"] is True
    assert updated.units.time == "HOURS"

    rendered = editor.to_text()
    assert "\tAUTO_LOAD ON\n" in rendered
    assert "\tTIME HOURS\n" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_updates_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.set_platform_property("Air", "SMOOTH", True)
    editor.set_view_property(".Moon CI Observer View", "VIEWANGLES", (-45, 45))
    updated = editor.refresh()

    assert updated.platforms[0].properties["SMOOTH"] is True
    assert updated.views[0].properties["VIEWANGLES"] == (-45, 45)
    rendered = editor.to_text()
    assert "SMOOTH ON" in rendered
    assert "VIEWANGLES -45 45" in rendered

def test_orb_editor_deletes_singleton_statements() -> None:
    editor = edit_orb_scenario_text(ORB_TYPED_SNIPPET)
    editor.delete_config_property("AUTO_LOAD")
    editor.delete_units_property("ANGLE_SHIFT")
    editor.delete_clock_property("REAL_TIME")
    updated = editor.refresh()

    assert updated.config is not None
    assert updated.units is not None
    assert updated.clock is not None
    assert "AUTO_LOAD" not in updated.config.properties
    assert updated.units.angle_shift is None
    assert updated.clock.real_time is None

    rendered = editor.to_text()
    assert "AUTO_LOAD" not in rendered
    assert "ANGLE_SHIFT" not in rendered
    assert "REAL_TIME" not in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_creates_new_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.create_platform(
        "ECR_FIXED",
        "New Site",
        properties={
            "STATE": (35.0, -97.0, 0),
            "PLAT": "Earth",
            "SHAPE": "STATION",
            "ICON": True,
        },
    )
    editor.create_view(
        "WORLD",
        "New View",
        "New Site",
        "ECR",
        properties={
            "ICONS": True,
            "VIEWANGLES": (-30, 60),
        },
    )
    updated = editor.refresh()

    created_platform = next(platform for platform in updated.platforms if platform.name == "New Site")
    assert created_platform.platform_type == "ECR_FIXED"
    assert created_platform.state == (35.0, -97.0, 0)
    assert created_platform.properties["ICON"] is True

    created_view = next(view for view in updated.views if view.name == "New View")
    assert created_view.view_type == "WORLD"
    assert created_view.observer == "New Site"
    assert created_view.coordinate_system == "ECR"
    assert created_view.properties["VIEWANGLES"] == (-30, 60)

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM ECR_FIXED "New Site"' in rendered
    assert 'DEFINE VIEW WORLD "New View" "New Site" ECR' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_deletes_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.delete_platform("Air")
    editor.delete_view(".Moon CI Observer View")
    updated = editor.refresh()

    assert not updated.platforms
    assert not updated.views

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM AIRROUTE  "Air"' not in rendered
    assert 'DEFINE VIEW WORLD  ".Moon CI Observer View"' not in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_updates_group_and_view_list_items() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.set_group_list_items("{New}", "PLATLIST", ["Alpha", "Bravo", "END_OF_INPUT"])
    editor.set_view_list_items(".Moon CI Observer View", "ICON_LIST", ["One", "Two", "END_OF_INPUT"])
    updated = editor.refresh()

    assert updated.groups[0].lists["PLATLIST"] == ["Alpha", "Bravo", "END_OF_INPUT"]
    assert updated.views[0].lists["ICON_LIST"] == ["One", "Two", "END_OF_INPUT"]

    rendered = editor.to_text()
    assert '"Alpha"' in rendered
    assert '"Bravo"' in rendered
    assert '"One"' in rendered
    assert '"Two"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_updates_spice_files_and_platform_repeated_rows() -> None:
    editor = edit_orb_scenario_text(f"{ORB_REMAINDER_SNIPPET}{ORB_EXPANDED_SNIPPET}")
    editor.set_spice_files(["alpha.tls", "beta.tpc"])
    editor.set_platform_repeated(
        "Air",
        "WAYPOINT",
        [
            (10.0, 20.0, 1, 0, 0.1),
            (30.0, 40.0, 2, 0, 0.2),
        ],
    )
    updated = editor.refresh()

    assert updated.spices[0].repeated["SPICEFILE"] == ["alpha.tls", "beta.tpc"]
    assert updated.platforms[0].repeated["WAYPOINT"] == [
        (10.0, 20.0, 1, 0, 0.1),
        (30.0, 40.0, 2, 0, 0.2),
    ]

    rendered = editor.to_text()
    assert 'SPICEFILE "alpha.tls"' in rendered
    assert 'SPICEFILE "beta.tpc"' in rendered
    assert "WAYPOINT 10.0 20.0 1 0 0.1" in rendered
    assert "WAYPOINT 30.0 40.0 2 0 0.2" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_updates_trajectory_rows() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.set_trajectory_rows(
        "Air Trajectory",
        [
            (2020, 1, 1, 0, 0, 0),
            (2020, 1, 1, 1, 2, 3),
        ],
    )
    updated = editor.refresh()

    assert updated.trajectories[0].trajectory_rows == [
        (2020, 1, 1, 0, 0, 0),
        (2020, 1, 1, 1, 2, 3),
    ]

    rendered = editor.to_text()
    assert "\t\t2020 1 1 0 0 0\n" in rendered
    assert "\t\t2020 1 1 1 2 3\n" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_editor_authors_airroute_platform() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.add_airroute_platform(
        "Route One",
        start_state=(2004, 2, 1, 0, 0, 0, 2004, 2, 2, 0, 0, 0),
        waypoints=[
            (33.9, -118.4, 1, 0, 0.2),
            (35.0, -97.0, 1, 0, 0.3),
        ],
        color="Cyan",
        smooth=True,
    )
    updated = editor.refresh()

    platform = next(item for item in updated.platforms if item.name == "Route One")
    assert platform.platform_type == "AIRROUTE"
    assert platform.properties["PLAT"] == "Earth"
    assert platform.properties["WAYPOINT_TYPE"] == "BY_SPEED"
    assert platform.properties["SMOOTH"] is True
    assert platform.repeated["WAYPOINT"][1] == (35.0, -97.0, 1, 0, 0.3)

def test_orb_editor_authors_trajectory_and_world_view() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.create_trajectory(
        "Route One Trajectory",
        coordinate_system="ECR",
        platform_name="Route One",
        trajectory_choice=("RELATIVE", "FORWARD", 1200),
        rows=[
            (2024, 1, 1, 0, 0, 0),
            (2024, 1, 1, 0, 5, 0),
        ],
        properties={"REFRESH_CHOICE": "GENERATE"},
    )
    editor.add_world_view(
        "Route One View",
        observer="Route One",
        coordinate_system="ECR",
        icon_list=["Route One", "END_OF_INPUT"],
        label_list=["Route One", "END_OF_INPUT"],
        viewangles=(-10, 70),
    )
    updated = editor.refresh()

    trajectory = next(item for item in updated.trajectories if item.name == "Route One Trajectory")
    assert trajectory.properties["CS"] == "ECR"
    assert trajectory.trajectory_rows[0] == (2024, 1, 1, 0, 0, 0)

    view = next(item for item in updated.views if item.name == "Route One View")
    assert view.observer == "Route One"
    assert view.coordinate_system == "ECR"
    assert view.lists["ICON_LIST"] == ["Route One", "END_OF_INPUT"]
    assert view.lists["LABEL_LIST"] == ["Route One", "END_OF_INPUT"]
    assert view.properties["VIEWANGLES"] == (-10, 70)

def test_orb_editor_clones_named_block() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.clone_named_block("PLATFORM", "Air", "Air Copy")
    updated = editor.refresh()

    clone = next(item for item in updated.platforms if item.name == "Air Copy")
    assert clone.platform_type == "AIRROUTE"
    assert clone.repeated["WAYPOINT"] == updated.platforms[0].repeated["WAYPOINT"]

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM AIRROUTE "Air Copy"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_authoring_helpers_add_fixed_site_view_and_grid() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    add_fixed_site(
        editor,
        FixedSiteSpec(
            name="Site Alpha",
            latitude_deg=35.0,
            longitude_deg=-97.0,
            color="Orange",
        ),
    )
    add_world_view_from_spec(
        editor,
        WorldViewSpec(
            name="Site Alpha View",
            observer="Site Alpha",
            coordinate_system="ECR",
            icon_list=["Site Alpha", "END_OF_INPUT"],
            label_list=["Site Alpha", "END_OF_INPUT"],
            viewangles=(-20, 50),
        ),
    )
    add_contour_grid(
        editor,
        ContourGridSpec(
            name="Site Alpha Grid",
            dimension=(8, 8, 10),
            altitude=0.0,
            domain=(0, 3600),
            domdlt=60.0,
            output_format="TEXTUREMAP_FORMAT",
            contour_enabled=True,
        ),
    )
    updated = editor.refresh()

    site = next(item for item in updated.platforms if item.name == "Site Alpha")
    assert site.platform_type == "ECR_FIXED"
    assert site.state == (35.0, -97.0, 0.0)
    assert site.properties["PLAT"] == "Earth"
    assert site.properties["COLOR"] == "Orange"

    view = next(item for item in updated.views if item.name == "Site Alpha View")
    assert view.observer == "Site Alpha"
    assert view.lists["ICON_LIST"] == ["Site Alpha", "END_OF_INPUT"]
    assert view.properties["VIEWANGLES"] == (-20, 50)

    grid = next(item for item in updated.grids if item.name == "Site Alpha Grid")
    assert grid.grid_type == "CONTOUR"
    assert grid.properties["DIMENSION"] == (8, 8, 10)
    assert grid.properties["OUTPUT_FORMAT"] == "TEXTUREMAP_FORMAT"
    assert grid.properties["CONTOUR_ENABLED"] is True

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM ECR_FIXED "Site Alpha"' in rendered
    assert 'DEFINE VIEW WORLD "Site Alpha View" "Site Alpha" ECR' in rendered
    assert 'DEFINE GRID CONTOUR "Site Alpha Grid"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_authoring_helpers_add_coordinate_system_observer_and_site_bundle() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    add_coordinate_system(
        editor,
        CoordinateSystemSpec(
            name="Site Alpha CS",
            track=("Z", "LONLAT", 0, 90),
            align=("RESULTANT", "Y", "LONLAT", 0, 0),
            sweep=("Z", "NOSWEEP"),
            origin=(".Host Platform", ".Host Platform"),
        ),
    )
    add_observer_platform(
        editor,
        ObserverPlatformSpec(
            name="Site Alpha Observer",
            state=(35.0, -97.0, 1000.0),
            coordinate_system="Site Alpha CS",
        ),
    )
    add_site_bundle(
        editor,
        SiteBundleSpec(
            site=FixedSiteSpec(name="Bundle Site", latitude_deg=34.0, longitude_deg=-96.0),
            coordinate_system=CoordinateSystemSpec(
                name="Bundle CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Bundle Observer",
                state=(34.0, -96.0, 500.0),
                coordinate_system="Bundle CS",
            ),
            view=WorldViewSpec(
                name="Bundle View",
                observer="Bundle Observer",
                coordinate_system="Bundle CS",
                icon_list=["Bundle Site", "END_OF_INPUT"],
                viewangles=(-15, 45),
            ),
            grid=ContourGridSpec(
                name="Bundle Grid",
                dimension=(4, 4, 4),
                altitude=0.0,
                domain=(0, 600),
                domdlt=30.0,
            ),
        ),
    )
    updated = editor.refresh()

    assert any(cs.name == "Site Alpha CS" for cs in updated.coordinate_systems)
    observer = next(item for item in updated.platforms if item.name == "Site Alpha Observer")
    assert observer.properties["CS"] == "Site Alpha CS"
    assert observer.properties["SHAPE"] == "VIEW_ONLY"

    assert any(site.name == "Bundle Site" for site in updated.platforms)
    bundle_view = next(item for item in updated.views if item.name == "Bundle View")
    assert bundle_view.observer == "Bundle Observer"
    assert bundle_view.coordinate_system == "Bundle CS"
    bundle_grid = next(item for item in updated.grids if item.name == "Bundle Grid")
    assert bundle_grid.properties["DIMENSION"] == (4, 4, 4)

    rendered = editor.to_text()
    assert 'DEFINE CS CSBASIS "Site Alpha CS"' in rendered
    assert 'DEFINE PLATFORM ECR_FIXED "Site Alpha Observer"' in rendered
    assert 'DEFINE VIEW WORLD "Bundle View" "Bundle Observer" "Bundle CS"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_package_build_write_and_load_round_trip(tmp_path: Path) -> None:
    spec = OrbPackageSpec(
        site_bundle=SiteBundleSpec(
            site=FixedSiteSpec(name="Pkg Site", latitude_deg=36.0, longitude_deg=-98.0, color="Blue"),
            coordinate_system=CoordinateSystemSpec(
                name="Pkg CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Pkg Observer",
                state=(36.0, -98.0, 900.0),
                coordinate_system="Pkg CS",
            ),
            view=WorldViewSpec(
                name="Pkg View",
                observer="Pkg Observer",
                coordinate_system="Pkg CS",
                icon_list=["Pkg Site", "END_OF_INPUT"],
                label_list=["Pkg Site", "END_OF_INPUT"],
                viewangles=(-25, 55),
            ),
            grid=ContourGridSpec(
                name="Pkg Grid",
                dimension=(6, 6, 6),
                altitude=0.0,
                domain=(0, 3600),
                domdlt=120.0,
                contour_enabled=False,
            ),
        ),
        extra_fixed_sites=[
            FixedSiteSpec(name="Pkg Site 2", latitude_deg=37.0, longitude_deg=-99.0),
        ],
    )

    editor = build_orb_package(spec)
    text = editor.to_text()
    assert "SOAP_SCENARIO_FILE" in text
    assert 'DEFINE PLATFORM ECR_FIXED "Pkg Site"' in text
    assert 'DEFINE GRID CONTOUR "Pkg Grid"' in text

    output_path = write_orb_package(spec, tmp_path / "pkg.orb")
    assert output_path.read_text(encoding="utf-8") == text

    scenario = load_orb_package(output_path)
    assert scenario.revision == 56
    assert scenario.file_type == "SOAP_SCENARIO_FILE"
    assert any(platform.name == "Pkg Site" for platform in scenario.platforms)
    assert any(platform.name == "Pkg Site 2" for platform in scenario.platforms)
    assert any(view.name == "Pkg View" for view in scenario.views)
    assert any(grid.name == "Pkg Grid" for grid in scenario.grids)
    assert scenario.document.to_text() == text
    assert dump_orb_text(parse_orb_text(text)) == text

def test_orb_package_supports_analysis_templates_stabilization_and_display_defaults(tmp_path: Path) -> None:
    spec = OrbPackageSpec(
        site_bundle=SiteBundleSpec(
            site=FixedSiteSpec(name="Template Site", latitude_deg=35.0, longitude_deg=-97.0),
            coordinate_system=CoordinateSystemSpec(
                name="Template CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Template Observer",
                state=(35.0, -97.0, 1000.0),
                coordinate_system="Template CS",
            ),
            view=WorldViewSpec(
                name="Template View",
                observer="Template Observer",
                coordinate_system="Template CS",
                icon_list=["Template Site", "END_OF_INPUT"],
            ),
        ),
        display_defaults=DisplayDefaultsSpec(
            map_color="Black",
            world_pcolor="White",
            data_pcolor="White",
            text_pcolor="White",
            world_scolor="Gray",
            icon_scale=1.5,
            line_thickness=2.0,
            map_line_thickness=2.0,
            limb=True,
            worldmap=False,
            lighting=True,
        ),
        analyses=[
            AnalysisSpec(
                name="Template Derived",
                variable=("CONSTANT", 1),
                variable_details={
                    "DISTANCEU": ("KILOMETERS", 1.0),
                    "TIMEU": ("SECONDS", 0.0),
                    "COMMENT": "Template derived variable",
                },
                bounds=(0, 10),
            )
        ],
        stabilizations=["Inertial"],
    )

    editor = build_orb_package(spec)
    output_path = write_orb_package(spec, tmp_path / "template.orb")
    scenario = load_orb_package(output_path)

    assert scenario.config is not None
    assert scenario.config.properties["MAP_COLOR"] == "Black"
    assert scenario.config.properties["ICON_SCALE"] == 1.5
    assert scenario.config.properties["LIMB"] is True
    assert scenario.config.properties["WORLDMAP"] is False
    assert scenario.config.properties["LIGHTING"] is True

    analysis = next(item for item in scenario.analyses if item.name == "Template Derived")
    assert analysis.properties["VARIABLE"] == ("CONSTANT", 1)
    assert analysis.properties["BOUNDS"] == (0, 10)
    assert analysis.variable_details["COMMENT"] == "Template derived variable"

    stabilization = next(item for item in scenario.stabilizations if item.name == "Inertial")
    assert isinstance(stabilization, OrbStabilization)

    rendered = editor.to_text()
    assert 'DEFINE ANALYSIS "Template Derived"' in rendered
    assert 'DEFINE STABILIZATION "Inertial"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered

def test_orb_package_analysis_template_normalization_round_trip(tmp_path: Path) -> None:
    template = AnalysisTemplateSpec(
        name="Normalized Derived",
        derived_variable=DerivedVariableSpec(
            value=("CONSTANT", 1),
            distanceu=("KILOMETERS", 1.0),
            timeu=("SECONDS", 0.0),
            comment="Normalized derived variable",
            extra_details={"SOURCE": "Template"},
        ),
        bounds=(0, 10),
        color="Blue",
        marker="o",
        link=True,
        cue=True,
    )

    analysis = normalize_analysis_template(template)
    assert analysis.name == "Normalized Derived"
    assert analysis.variable == ("CONSTANT", 1)
    assert analysis.variable_details["DISTANCEU"] == ("KILOMETERS", 1.0)
    assert analysis.variable_details["TIMEU"] == ("SECONDS", 0.0)
    assert analysis.variable_details["COMMENT"] == "Normalized derived variable"
    assert analysis.variable_details["SOURCE"] == "Template"

    spec = OrbPackageSpec(analysis_templates=[template])
    editor = build_orb_package(spec)
    output_path = write_orb_package(spec, tmp_path / "normalized.orb")
    scenario = load_orb_package(output_path)

    assert output_path.read_text(encoding="utf-8") == editor.to_text()
    analysis_block = next(item for item in scenario.analyses if item.name == "Normalized Derived")
    assert analysis_block.properties["VARIABLE"] == ("CONSTANT", 1)
    assert analysis_block.properties["BOUNDS"] == (0, 10)
    assert analysis_block.properties["COLOR"] == "Blue"
    assert analysis_block.variable_details["COMMENT"] == "Normalized derived variable"
    assert dump_orb_text(parse_orb_text(editor.to_text())) == editor.to_text()

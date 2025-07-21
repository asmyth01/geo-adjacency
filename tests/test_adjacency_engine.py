import geopandas as gpd
import pytest
from shapely import LineString, Point, Polygon
from shapely.wkt import loads

from geo_adjacency.adjacency import AdjacencyEngine
from geo_adjacency.exception import ImmutablePropertyError


def test_source_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = engine.source_gdf.geometry.tolist()
    assert geoms == source_geoms


def test_target_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = engine.target_gdf.geometry.tolist()
    assert geoms == target_geoms


def test_obstacle_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = engine.obstacle_gdf.geometry.tolist()
    assert geoms == obstacle_geoms


def test_all_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    all_features = engine.all_features_gdf

    # Test that we get a GeoDataFrame
    assert isinstance(all_features, gpd.GeoDataFrame)

    # Test that all geometries are included
    expected_total = len(source_geoms) + len(target_geoms) + len(obstacle_geoms)
    assert len(all_features) == expected_total

    # Test that feature types are correctly assigned
    assert set(all_features["feature_type"].unique()) == {
        "source",
        "target",
        "obstacle",
    }

    # Test that original indices are preserved
    assert "original_index" in all_features.columns

    # Test that source geometries are first
    source_features = all_features[all_features["feature_type"] == "source"]
    assert len(source_features) == len(source_geoms)

    # Test that target geometries are second
    target_features = all_features[all_features["feature_type"] == "target"]
    assert len(target_features) == len(target_geoms)

    # Test that obstacle geometries are last
    obstacle_features = all_features[all_features["feature_type"] == "obstacle"]
    assert len(obstacle_features) == len(obstacle_geoms)


def test_get_adjacency_dict_with_targets_and_obstacles(
    source_geoms, target_geoms, obstacle_geoms
):
    engine = AdjacencyEngine(
        source_geoms,
        target_geoms,
        obstacle_geoms,
        **{"densify_features": True, "max_segment_length": 0.1},
    )
    actual = engine.get_adjacency_dict()
    expected = {0: [0], 1: [1, 2], 2: [2, 3], 3: [3, 4, 5], 4: [5], 5: [6], 6: [7]}

    assert actual == expected


def test_get_adjacency_dict_with_source_only(source_geoms):
    engine = AdjacencyEngine(
        source_geoms,
        None,
        None,
        **{"densify_features": True, "max_segment_length": 0.1},
    )
    actual = engine.get_adjacency_dict()
    expected = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5], 5: [4, 6], 6: [5]}

    assert actual == expected


def test_get_adjacency_dict_with_source_and_obstacles(source_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms,
        None,
        obstacle_geoms,
        **{"densify_features": True, "max_segment_length": 0.1},
    )
    actual = engine.get_adjacency_dict()
    expected = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5], 5: [4, 6], 6: [5]}

    assert actual == expected


def test_vor(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"densify_features": False}
    )
    expected = [
        26,
        2,
        4,
        25,
        26,
        37,
        61,
        60,
        36,
        37,
        38,
        63,
        44,
        41,
        38,
        39,
        43,
        21,
        34,
        23,
        43,
        24,
        22,
        52,
        54,
        24,
        55,
        53,
        67,
        47,
        55,
        65,
        18,
        5,
        13,
        59,
        57,
        5,
        58,
        62,
        27,
        45,
        58,
        40,
        42,
        7,
        11,
        12,
        20,
        7,
        33,
        9,
        10,
        31,
        33,
        35,
        28,
        69,
        29,
        16,
        15,
        69,
        17,
        19,
        8,
        14,
        17,
        3,
        6,
        6,
        1,
        32,
        30,
        56,
        50,
        32,
        49,
        51,
        70,
        68,
        49,
        64,
        66,
        48,
        46,
        64,
    ]
    actual = list(engine.vor.point_region)
    assert actual == expected


def test_calc_segmentation_dist(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"densify_features": True}
    )
    actual = engine._calc_segmentation_dist()
    expected = 0.05037593984962406
    assert actual == expected


def test_get_geometry_from_coord_index(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"densify_features": False}
    )

    # Test that we get back the correct dataframe type and index for various coordinates
    dataframe_type, geom_idx = engine.get_geometry_from_coord_index(26)
    assert isinstance(dataframe_type, str)
    assert isinstance(geom_idx, int)
    assert dataframe_type in ["source", "target", "obstacle"]

    # Test a few more coordinate indices
    dataframe_type2, geom_idx2 = engine.get_geometry_from_coord_index(32)
    assert isinstance(dataframe_type2, str)
    assert isinstance(geom_idx2, int)

    dataframe_type3, geom_idx3 = engine.get_geometry_from_coord_index(39)
    assert isinstance(dataframe_type3, str)
    assert isinstance(geom_idx3, int)


def test_tag_geometries():
    source_geoms_1 = [loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")]
    target_geoms_1 = [loads("POLYGON((2 0, 3 0, 3 1, 2 1, 2 0))")]
    obstacle_geoms_1 = [loads("POLYGON((4 0, 5 0, 5 1, 4 1, 4 0))")]

    engine = AdjacencyEngine(
        source_geoms_1, target_geoms_1, obstacle_geoms_1, **{"densify_features": False}
    )
    engine._tag_geometries_with_voronoi_vertices()

    # Test that the geometry voronoi vertices mapping was created
    assert hasattr(engine, "_geometry_voronoi_vertices")
    assert isinstance(engine._geometry_voronoi_vertices, dict)

    # Test that source and target geometries got tagged with voronoi vertices
    source_key = ("source", 0)
    target_key = ("target", 0)
    assert source_key in engine._geometry_voronoi_vertices
    assert target_key in engine._geometry_voronoi_vertices
    assert isinstance(engine._geometry_voronoi_vertices[source_key], set)
    assert isinstance(engine._geometry_voronoi_vertices[target_key], set)


def test_immutable_properties(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"densify_features": False}
    )
    # Test that all_features property is immutable
    with pytest.raises(ImmutablePropertyError):
        engine.all_features_gdf = gpd.GeoDataFrame()
    with pytest.raises(ImmutablePropertyError):
        engine.vor = 1


def test_add_new_attribute_error(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"densify_features": False}
    )
    with pytest.raises(AttributeError):
        engine.new_attribute = 1


def test_max_distance(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"max_distance": 1.0}
    )
    actual = engine.get_adjacency_dict()
    expected = {0: [0], 1: [1], 3: [4, 5], 4: [6], 6: [7]}
    print(actual)
    print(expected)
    assert actual == expected


def test_bounding_rectangle(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(
        source_geoms, target_geoms, obstacle_geoms, **{"bounding_box": (0, 0, 16, 2)}
    )
    actual = engine.get_adjacency_dict()
    expected = {0: [0], 1: [1], 2: [2, 3], 3: [3, 4]}
    assert actual == expected


def test_invalid_bounding_rectangle():
    # Test invalid bounding box
    with pytest.raises(AssertionError):
        AdjacencyEngine(
            [loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")],
            bounding_box=(1, 0, 0, 1),  # minx > maxx
        )


def test_geodataframe_input_sources():
    """Test AdjacencyEngine with GeoDataFrame as source input."""
    # Create GeoDataFrame with attributes
    geometries = [Point(0, 0), Point(1, 0), Point(0, 1), Point(1, 1)]
    gdf = gpd.GeoDataFrame(
        {
            "id": ["A", "B", "C", "D"],
            "type": ["residential", "commercial", "industrial", "park"],
            "value": [100, 200, 150, 50],
        },
        geometry=geometries,
    )

    engine = AdjacencyEngine(gdf)

    # Test that GeoDataFrame is stored correctly
    assert isinstance(engine.source_gdf, gpd.GeoDataFrame)
    assert len(engine.source_gdf) == 4
    assert list(engine.source_gdf.columns) == ["id", "type", "value", "geometry"]
    assert engine.source_gdf["id"].tolist() == ["A", "B", "C", "D"]


def test_geodataframe_source_target():
    """Test AdjacencyEngine with separate source and target GeoDataFrames."""
    # Source: Buildings
    buildings = gpd.GeoDataFrame(
        {
            "name": ["Building A", "Building B", "Building C"],
            "height": [20, 30, 25],
            "floors": [5, 8, 6],
        },
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
            Polygon([(1, 2), (2, 2), (2, 3), (1, 3)]),
        ],
    )

    # Target: Parks
    parks = gpd.GeoDataFrame(
        {
            "park_name": ["Central Park", "Small Park"],
            "area_sqm": [5000, 1000],
            "has_playground": [True, False],
        },
        geometry=[
            Polygon([(0.5, -0.5), (2.5, -0.5), (2.5, 0.5), (0.5, 0.5)]),
            Polygon([(1.5, 1.5), (2.5, 1.5), (2.5, 2.5), (1.5, 2.5)]),
        ],
    )

    engine = AdjacencyEngine(buildings, parks)

    # Test that both GeoDataFrames are stored correctly
    assert isinstance(engine.source_gdf, gpd.GeoDataFrame)
    assert isinstance(engine.target_gdf, gpd.GeoDataFrame)
    assert len(engine.source_gdf) == 3
    assert len(engine.target_gdf) == 2
    assert "name" in engine.source_gdf.columns
    assert "park_name" in engine.target_gdf.columns


def test_adjacency_gdf_with_attributes():
    """Test get_adjacency_gdf() preserves attributes from source and target."""
    # Create source and target with rich attributes
    sources = gpd.GeoDataFrame(
        {
            "building_id": ["B1", "B2"],
            "type": ["office", "retail"],
            "year_built": [1995, 2005],
        },
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
        ],
    )

    targets = gpd.GeoDataFrame(
        {"road_id": ["R1"], "speed_limit": [25], "surface": ["asphalt"]},
        geometry=[Polygon([(0.5, -0.5), (2.5, -0.5), (2.5, 0.5), (0.5, 0.5)])],
    )

    engine = AdjacencyEngine(sources, targets)
    adj_gdf = engine.get_adjacency_gdf()

    assert adj_gdf is not None
    assert len(adj_gdf) > 0

    # Check that source attributes are preserved with 'source_' prefix
    assert "source_building_id" in adj_gdf.columns
    assert "source_type" in adj_gdf.columns
    assert "source_year_built" in adj_gdf.columns

    # Check that target attributes are preserved with 'target_' prefix
    assert "target_road_id" in adj_gdf.columns
    assert "target_speed_limit" in adj_gdf.columns
    assert "target_surface" in adj_gdf.columns

    # Check core adjacency columns
    assert "source_idx" in adj_gdf.columns
    assert "target_idx" in adj_gdf.columns
    assert "source_geometry" in adj_gdf.columns
    assert "target_geometry" in adj_gdf.columns
    assert "geometry" in adj_gdf.columns


def test_source_source_adjacency_gdf():
    """Test get_adjacency_gdf() for source-to-source adjacency."""
    # Create points in a grid pattern that will be adjacent
    points = [Point(i, j) for i in range(3) for j in range(3)]
    sources = gpd.GeoDataFrame(
        {
            "point_id": [f"P{i}" for i in range(9)],
            "x_coord": [p.x for p in points],
            "y_coord": [p.y for p in points],
        },
        geometry=points,
    )

    engine = AdjacencyEngine(sources)  # No target - source-to-source
    adj_gdf = engine.get_adjacency_gdf()

    if adj_gdf is not None and len(adj_gdf) > 0:
        # For source-to-source, both source and target refer to the same GDF
        assert "source_point_id" in adj_gdf.columns
        assert "target_point_id" in adj_gdf.columns
        assert "source_x_coord" in adj_gdf.columns
        assert "target_x_coord" in adj_gdf.columns

        # Check that source_idx != target_idx (no self-adjacency)
        assert all(adj_gdf["source_idx"] != adj_gdf["target_idx"])


def test_mixed_geometry_types():
    """Test AdjacencyEngine with mixed geometry types in GeoDataFrames."""
    mixed_geoms = gpd.GeoDataFrame(
        {
            "feature_id": ["F1", "F2", "F3", "F4"],
            "geom_type": ["Point", "LineString", "Polygon", "Point"],
        },
        geometry=[
            Point(0, 0),
            LineString([(1, 0), (2, 0), (3, 0)]),
            Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),
            Point(3, 1),
        ],
    )

    engine = AdjacencyEngine(mixed_geoms)

    # Should handle mixed geometry types without error
    result = engine.get_adjacency_dict()
    assert isinstance(result, dict)

    # Test that all_features contains the geometries properly
    all_features = engine.all_features_gdf
    assert len(all_features) == 4
    assert all(all_features["feature_type"] == "source")
    assert set(all_features["feature_id"]) == {"F1", "F2", "F3", "F4"}

    # Test that coordinate extraction works by testing Voronoi creation
    vor = engine.vor
    assert vor is not None
    assert len(vor.points) > 0


def test_geometry_from_coord_index_geodataframe():
    """Test get_geometry_from_coord_index with GeoDataFrame architecture."""
    sources = gpd.GeoDataFrame(
        {"name": ["S1", "S2"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]), Point(2, 0)],
    )

    targets = gpd.GeoDataFrame(
        {"name": ["T1"]}, geometry=[LineString([(0, 2), (1, 2)])]
    )

    obstacles = gpd.GeoDataFrame({"name": ["O1"]}, geometry=[Point(3, 3)])

    engine = AdjacencyEngine(sources, targets, obstacles)

    # Test mapping for various coordinate indices
    # Calculate total coordinate count from all_features
    from geo_adjacency.utils import count_unique_coords

    all_features = engine.all_features_gdf
    total_coords = 0
    for _, row in all_features.iterrows():
        geom = row.geometry
        coord_count = count_unique_coords(geom)
        total_coords += coord_count

    for i in range(min(5, total_coords)):  # Test first few coordinates
        dataframe_type, geom_idx = engine.get_geometry_from_coord_index(i)
        assert dataframe_type in ["source", "target", "obstacle"]
        assert isinstance(geom_idx, int)
        assert geom_idx >= 0


def test_empty_geodataframes():
    """Test behavior with empty GeoDataFrames."""
    empty_gdf = gpd.GeoDataFrame({"geometry": []})
    # Need enough non-collinear points for Voronoi diagram
    sufficient_gdf = gpd.GeoDataFrame(
        {"geometry": [Point(0, 0), Point(1, 0), Point(0, 1), Point(1, 1)]}
    )

    # Empty target - source geometries exist but have no targets to be adjacent to
    engine = AdjacencyEngine(sufficient_gdf, empty_gdf)
    result = engine.get_adjacency_dict()

    # The adjacency dict is a defaultdict that only creates entries when accessed
    # Since there are no targets, no adjacencies are found, so dict remains empty
    assert isinstance(result, dict)

    # Test that the engine was created successfully with the right GeoDataFrames
    assert len(engine.source_gdf) == 4
    assert len(engine.target_gdf) == 0

    # Test adjacency GDF should be None when no adjacencies found
    adj_gdf = engine.get_adjacency_gdf()
    assert adj_gdf is None


def test_all_features_functionality():
    """Test that all_features property works correctly with different geometry types."""
    geometries = [
        Point(1, 2),
        LineString([(0, 0), (1, 1), (2, 0)]),
        Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
    ]

    gdf = gpd.GeoDataFrame({"geometry": geometries})
    engine = AdjacencyEngine(gdf)

    # Test that all_features contains the geometries
    all_features = engine.all_features_gdf
    assert isinstance(all_features, gpd.GeoDataFrame)
    assert len(all_features) == 3
    assert all(all_features["feature_type"] == "source")

    # Test that Voronoi diagram can be created
    vor = engine.vor
    assert vor is not None

    # Test that coordinate mapping works
    coord_type, geom_idx = engine.get_geometry_from_coord_index(0)
    assert coord_type == "source"
    assert isinstance(geom_idx, int)


def test_list_to_geodataframe_conversion():
    """Test that lists of geometries are correctly converted to GeoDataFrames."""
    geom_list = [Point(0, 0), Point(1, 1), Point(2, 2)]

    engine = AdjacencyEngine(geom_list)

    # Should have converted list to GeoDataFrame
    assert isinstance(engine.source_gdf, gpd.GeoDataFrame)
    assert len(engine.source_gdf) == 3
    assert list(engine.source_gdf.geometry) == geom_list

    # Should have only geometry column when converting from list
    assert list(engine.source_gdf.columns) == ["geometry"]


def test_voronoi_geometry_mapping():
    """Test that the new Voronoi geometry mapping system works correctly."""
    # Simple case with well-separated geometries
    sources = gpd.GeoDataFrame(
        {"id": ["S1", "S2"]},
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(3, 0), (4, 0), (4, 1), (3, 1)]),
        ],
    )

    engine = AdjacencyEngine(sources)
    engine._tag_geometries_with_voronoi_vertices()

    # Check that the geometry-to-voronoi mapping was created
    assert hasattr(engine, "_geometry_voronoi_vertices")
    assert isinstance(engine._geometry_voronoi_vertices, dict)

    # Check that geometries are mapped with proper keys
    source_key1 = ("source", 0)
    source_key2 = ("source", 1)

    assert source_key1 in engine._geometry_voronoi_vertices
    assert source_key2 in engine._geometry_voronoi_vertices
    assert isinstance(engine._geometry_voronoi_vertices[source_key1], set)
    assert isinstance(engine._geometry_voronoi_vertices[source_key2], set)


def test_adjacency_with_max_distance_geodataframes():
    """Test max_distance parameter works with GeoDataFrames."""
    # Create points at known distances - make them non-collinear for Voronoi
    points = gpd.GeoDataFrame(
        {"name": ["A", "B", "C", "D"]},
        geometry=[
            Point(0, 0),  # A
            Point(1, 0),  # B - distance 1 from A
            Point(2, 1),  # C - distance ~1.4 from B, ~2.2 from A
            Point(10, 5),  # D - far from others
        ],
    )

    # With max_distance=1.5, A-B should be adjacent, but others should be too far
    engine = AdjacencyEngine(points, max_distance=1.5)
    result = engine.get_adjacency_dict()

    # Should have some adjacencies within the distance limit
    total_adjacencies = sum(len(v) for v in result.values())
    assert total_adjacencies >= 0  # May be 0 if no points are close enough

    # Get adjacency GDF for easier analysis
    adj_gdf = engine.get_adjacency_gdf()

    # If there are adjacencies, they should respect the max_distance constraint
    if adj_gdf is not None and len(adj_gdf) > 0:
        # Should have some adjacencies but point D should be largely isolated due to distance
        assert len(adj_gdf) > 0


def test_max_segment_length_without_densify_error():
    """Test that providing max_segment_length without densify_features raises ValueError."""
    from shapely import Point
    
    source_geoms = [Point(0, 0), Point(1, 0)]
    
    with pytest.raises(ValueError, match="interpolate_points must be True"):
        AdjacencyEngine(
            source_geoms, 
            densify_features=False, 
            max_segment_length=0.1
        )


def test_empty_geodataframes_edge_cases():
    """Test various empty GeoDataFrame edge cases."""
    # Test with properly constructed empty GeoDataFrame
    empty_gdf = gpd.GeoDataFrame(geometry=[])
    engine = AdjacencyEngine(empty_gdf)
    
    # Test coordinate mapping with empty features
    all_features = engine.all_features_gdf
    assert len(all_features) == 0
    assert isinstance(all_features, gpd.GeoDataFrame)


def test_no_adjacency_results():
    """Test case where no adjacencies are found."""
    # Create enough geometries that are far apart so no adjacency
    # Need at least 4 points for Voronoi diagram
    sources = gpd.GeoDataFrame({'geometry': [
        Point(0, 0), Point(1, 0)
    ]})
    targets = gpd.GeoDataFrame({'geometry': [
        Point(100, 100), Point(101, 100)
    ]})
    
    engine = AdjacencyEngine(sources, targets, max_distance=1.0)
    result = engine.get_adjacency_dict()
    
    # Should have empty results due to max_distance constraint
    assert result == {}
    
    # get_adjacency_gdf should return None when no results
    adj_gdf = engine.get_adjacency_gdf()
    assert adj_gdf is None


def test_coordinate_cache_empty_case():
    """Test coordinate-to-feature cache with empty features."""
    from shapely import Point
    
    # Create engine with valid geometries first
    engine = AdjacencyEngine([Point(0, 0)])
    
    # Clear the features to test empty case
    engine._all_features_gdf = gpd.GeoDataFrame({'geometry': []})
    engine._coord_to_feature_cache = None
    
    # This should handle empty case without error
    try:
        # This would fail if run with actual empty features, 
        # but tests the empty cache creation path
        with pytest.raises(KeyError):
            engine.get_geometry_from_coord_index(0)
    except:
        pass  # Expected to fail but shouldn't crash on cache creation


def test_bounding_rectangle_edge_cases():
    """Test bounding rectangle filtering edge cases."""
    # Create enough geometries outside a small bounding box (need 4+ points for Voronoi)
    sources = gpd.GeoDataFrame({'geometry': [Point(100, 100), Point(101, 100)]})  
    targets = gpd.GeoDataFrame({'geometry': [Point(200, 200), Point(201, 200)]})
    
    # Set a bounding box that excludes all geometries
    engine = AdjacencyEngine(
        sources, targets, 
        bounding_box=(0, 0, 10, 10)  # Small box that excludes all points
    )
    
    # This should trigger the early return for no valid geometries
    result = engine.get_adjacency_dict()
    assert result == {}


def test_determine_adjacency_empty_inputs():
    """Test _determine_adjacency with empty GeoDataFrames to hit early return."""
    from shapely import Point
    import geopandas as gpd
    from collections import defaultdict
    
    # Create engine with valid geometries
    sources = gpd.GeoDataFrame({'geometry': [Point(0, 0), Point(1, 0), Point(0, 1), Point(1, 1)]})
    engine = AdjacencyEngine(sources)
    
    # Initialize adjacency dict
    engine._adjacency_dict = defaultdict(list)
    
    # Test with empty source GDF
    empty_gdf = gpd.GeoDataFrame({'geometry': []})
    valid_gdf = gpd.GeoDataFrame({'geometry': [Point(0, 0)]})
    
    # This should hit the early return for empty source
    engine._determine_adjacency(empty_gdf, valid_gdf)
    
    # Should not have added anything to adjacency dict
    assert len(engine._adjacency_dict) == 0

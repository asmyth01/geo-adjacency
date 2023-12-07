import pytest
from shapely.wkt import dumps, loads

import geo_adjacency.adjacency
from geo_adjacency.adjacency import AdjacencyEngine, _Feature
import geo_adjacency.utils
from geo_adjacency.exception import ImmutablePropertyError


def test_source_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.source_features]
    assert geoms == source_geoms


def test_target_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.target_features]
    assert geoms == target_geoms


def test_obstacle_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.obstacle_features]
    assert geoms == obstacle_geoms


def test_all_features(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    expected = []
    for geom in source_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))
    for geom in target_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))
    for geom in obstacle_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))

    for feat_expected, feat_actual in zip(expected, engine.all_features):
        assert feat_expected.geometry == feat_actual.geometry, "{} != {}".format(feat_expected, feat_actual)


def test_all_coordinates(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    actual = engine.all_coordinates
    for coord in actual:
        try:
            assert isinstance(coord, tuple)
            assert len(coord) == 2
        except AssertionError:
            print(f"Problem with coordinate pair: '{coord}'")
            raise

    expected = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (3.0, 0.0), (3.0, 1.0), (5.0, 1.0),
                (5.0, 0.0), (6.0, 0.0), (6.0, 1.0), (7.0, 1.0), (7.0, 0.0), (10.0, 1.0),
                (15.0, 0.0), (15.0, 1.0), (18.0, 1.0), (18.0, 0.0), (20.0, 0.0), (20.0, 1.0),
                (22.0, 1.0), (22.0, 0.0), (24.0, 0.0), (24.0, 1.0), (26.0, 1.0), (26.0, 0.0),
                (27.0, 1.0), (30.0, 1.0),(0.0, 2.0), (0.0, 3.0), (5.0, 3.0), (5.0, 2.0), (6.0, 2.0),
                (6.0, 3.0), (8.0, 3.0), (8.0, 2.0), (9.0, 2.0), (12.0, 2.0), (15.0, 2.0), (15.0, 3.0),
                (17.0, 3.0), (17.0, 2.0), (18.0, 2.0), (18.0, 3.0),(20.0, 3.0), (20.0, 2.0),
                (21.0, 2.0), (26.0, 2.0), (27.0, 2.0), (27.0, 3.0), (29.0, 3.0), (29.0, 2.0),
                (30.0, 2.0),(30.0, 3.0),(32.0, 3.0), (32.0, 2.0), (0.0, 1.5),(1.0, 1.5), (1.0, 1.5),
                (1.5, 1.5), (20.0, 1.25), (20.0, 1.75), (22.0, 1.75),(22.0, 1.25), (23.0, 1.25),
                (23.0, 1.75), (25.0, 1.75), (25.0, 1.25), (26.0, 1.25), (26.0, 1.75), (28.0, 1.75),
                (28.0, 1.25))
    assert actual == expected


def test_get_adjacency_dict_with_targets_and_obstacles(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [0],
             1: [1, 2],
             2: [2, 3],
             3: [3, 4, 5],
             4: [5],
             5: [6],
             6: [7]}

    assert actual == expected


def test_get_adjacency_dict_with_source_only(source_geoms):
    engine = AdjacencyEngine(source_geoms, None, None, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [1],
             1: [0, 2],
             2: [1, 3],
             3: [2, 4],
             4: [3, 5],
             5: [4, 6],
             6: [5]}

    assert actual == expected


def test_get_adjacency_dict_with_source_and_obstacles(source_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, None, obstacle_geoms, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [1],
             1: [0, 2],
             2: [1, 3],
             3: [2, 4],
             4: [3, 5],
             5: [4, 6],
             6: [5]}

    assert actual == expected


def test_vor(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    expected = [26, 2, 4, 25, 37, 61, 60, 36, 38, 63, 44, 41, 39, 43, 21, 34, 23, 24, 22, 52, 54, 55,
                53, 67, 47, 65, 18, 5, 13, 59, 57, 58, 62, 27, 45, 40, 42, 7, 11, 12, 20, 33, 9, 10,
                31, 35, 28, 69, 29, 16, 15, 17, 19, 8, 14, 3, 6, 6, 1, 32, 30, 56, 50, 49, 51, 70,
                68, 64, 66, 48, 46]
    actual = list(engine.vor.point_region)
    assert actual == expected


def test_calc_segmentation_dist(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True)
    actual = engine._calc_segmentation_dist()
    expected = 1.147746358922793
    assert actual == expected


def test_get_feature_from_coord_index(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    actual = dumps(engine.get_feature_from_coord_index(26).geometry)
    expected = "LINESTRING (27.0000000000000000 1.0000000000000000, 30.0000000000000000 1.0000000000000000)"
    assert actual == expected

    actual = dumps(engine.get_feature_from_coord_index(32).geometry)
    expected = "POLYGON ((6.0000000000000000 2.0000000000000000, 6.0000000000000000 3.0000000000000000, 8.0000000000000000 3.0000000000000000, 8.0000000000000000 2.0000000000000000, 6.0000000000000000 2.0000000000000000))"
    assert actual == expected

    actual = dumps(engine.get_feature_from_coord_index(39).geometry)
    expected = 'POLYGON ((15.0000000000000000 2.0000000000000000, 15.0000000000000000 3.0000000000000000, 17.0000000000000000 3.0000000000000000, 17.0000000000000000 2.0000000000000000, 15.0000000000000000 2.0000000000000000))'
    assert actual == expected

    actual = dumps(engine.get_feature_from_coord_index(46).geometry)
    expected = 'LINESTRING (21.0000000000000000 2.0000000000000000, 26.0000000000000000 2.0000000000000000)'
    assert actual == expected

    actual = dumps(engine.get_feature_from_coord_index(55).geometry)
    expected = 'LINESTRING (0.0000000000000000 1.5000000000000000, 1.0000000000000000 1.5000000000000000, 1.0000000000000000 1.5000000000000000, 1.5000000000000000 1.5000000000000000)'
    assert actual == expected


def test_tag_features():
    source_geoms_1 = [loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")]
    target_geoms_1 = [loads("POLYGON((2 0, 3 0, 3 1, 2 1, 2 0))")]
    obstacle_geoms_1 = [loads("POLYGON((4 0, 5 0, 5 1, 4 1, 4 0))")]

    engine = AdjacencyEngine(source_geoms_1, target_geoms_1, obstacle_geoms_1, False)
    engine._tag_feature_with_voronoi_vertices()

    assert engine.source_features[0].voronoi_points == {1, 2}
    assert engine.target_features[0].voronoi_points == {2, 3, 4}


def test_immutable_properties(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    with pytest.raises(ImmutablePropertyError):
        engine.source_features = [_Feature(loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"))]
    with pytest.raises(ImmutablePropertyError):
        engine.target_features = [_Feature(loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"))]
    with pytest.raises(ImmutablePropertyError):
        engine.obstacle_features = [_Feature(loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"))]
    with pytest.raises(ImmutablePropertyError):
        engine.vor = 1
    with pytest.raises(ImmutablePropertyError):
        engine.all_features = 1
    with pytest.raises(ImmutablePropertyError):
        engine.all_coordinates = 1


def test_add_new_attribute_error(source_geoms, target_geoms, obstacle_geoms):
    engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    with pytest.raises(AttributeError):
        engine.new_attribute = 1


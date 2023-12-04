from shapely.wkt import dumps, loads

import geo_adjacency.adjacency
import geo_adjacency.feature
import geo_adjacency.utils
from geo_adjacency import adjacency
from geo_adjacency.utils import flatten_list

from tests.sample_data.wkts import source_geoms, target_geoms, obstacle_geoms


def test_flatten_list():
    test_data = [[(1, 2), (3, 4)], [(5, 6), (7, 8)], [(9, 10), [(11, 12), [(13, 14), [(15, 16)]]]]]
    assert list(flatten_list(test_data)) == [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)]


def test_source_features():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.source_features]
    assert geoms == source_geoms


def test_target_features():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.target_features]
    assert geoms == target_geoms


def test_obstacle_features():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    geoms = [feat.geometry for feat in engine.obstacle_features]
    assert geoms == obstacle_geoms


def test_all_features():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    expected = []
    for geom in source_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))
    for geom in target_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))
    for geom in obstacle_geoms:
        expected.append(geo_adjacency.adjacency._Feature(geom))

    for feat_expected, feat_actual in zip(expected, engine.all_features):
        assert feat_expected == feat_actual, "{} != {}".format(feat_expected, feat_actual)


def test_coords_from_point():
    point = loads("POINT (30 10)")
    actual = geo_adjacency.utils.coords_from_point(point)
    expected = [(30.0, 10.0)]
    assert actual == expected


def test_coords_from_ring():
    ring = loads("LINESTRING (30 10, 10 30, 40 40)")
    actual = geo_adjacency.utils.coords_from_ring(ring)
    expected = [(30.0, 10.0), (10.0, 30.0), (40.0, 40.0)]
    assert actual == expected


def test_coords_from_polygon():
    polygon = loads("POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))")
    actual = geo_adjacency.utils.coords_from_polygon(polygon)
    expected = [(30.0, 10.0), (40.0, 40.0), (20.0, 40.0), (10.0, 20.0)]
    assert actual == expected

    poylgon_w_interior = loads("POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, "
                               "30 20, 20 30))")
    actual = geo_adjacency.utils.coords_from_polygon(poylgon_w_interior)
    expected = [(35.0, 10.0), (45.0, 45.0), (15.0, 40.0), (10.0, 20.0), (20.0, 30.0),
                (35.0, 35.0), (30.0, 20.0)]
    assert actual == expected


def test_coords_from_multipolygon():
    multipolygon = loads("MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, "
                         "5 10, 15 5)))")
    actual = geo_adjacency.utils.coords_from_multipolygon(multipolygon)
    expected = [(30.0, 20.0), (45.0, 40.0), (10.0, 40.0), (15.0, 5.0), (40.0, 10.0), (10.0, 20.0),
                (5.0, 10.0)]

    assert actual == expected

    multipolygon_w_interior = loads("MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, "
                                    "10 30, 10 10, 30 5, 45 20, 20 35),(30 20, 20 15, 20 25, "
                                    "30 20)))")
    actual = geo_adjacency.utils.coords_from_multipolygon(multipolygon_w_interior)
    expected = [(40.0, 40.0), (20.0, 45.0), (45.0, 30.0), (20.0, 35.0), (10.0, 30.0),
                (10.0, 10.0),
                (30.0, 5.0), (45.0, 20.0), (30.0, 20.0), (20.0, 15.0), (20.0, 25.0)]
    assert actual == expected


def test_all_coordinates():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
    actual = engine.all_coordinates
    for coord in actual:
        try:
            assert isinstance(coord, tuple)
            assert len(coord) == 2
        except AssertionError:
            print(f"Problem with coordinate pair: '{coord}'")
            raise

    expected = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (3.0, 0.0), (3.0, 1.0), (5.0, 1.0), (5.0, 0.0), (6.0, 0.0), (6.0, 1.0), (7.0, 1.0), (7.0, 0.0), (10.0, 1.0), (15.0, 0.0), (15.0, 1.0), (18.0, 1.0), (18.0, 0.0), (20.0, 0.0), (20.0, 1.0),(22.0, 1.0), (22.0, 0.0), (24.0, 0.0), (24.0, 1.0), (26.0, 1.0), (26.0, 0.0), (27.0, 1.0), (30.0, 1.0),(0.0, 2.0), (0.0, 3.0), (5.0, 3.0), (5.0, 2.0), (6.0, 2.0), (6.0, 3.0), (8.0, 3.0), (8.0, 2.0), (9.0, 2.0), (12.0, 2.0), (15.0, 2.0), (15.0, 3.0), (17.0, 3.0), (17.0, 2.0), (18.0, 2.0), (18.0, 3.0),(20.0, 3.0), (20.0, 2.0), (21.0, 2.0), (26.0, 2.0), (27.0, 2.0), (27.0, 3.0), (29.0, 3.0), (29.0, 2.0), (30.0, 2.0),(30.0, 3.0),(32.0, 3.0), (32.0, 2.0), (0.0, 1.5),(1.0, 1.5), (1.0, 1.5), (1.5, 1.5), (20.0, 1.25), (20.0, 1.75), (22.0, 1.75),(22.0, 1.25), (23.0, 1.25), (23.0, 1.75), (25.0, 1.75), (25.0, 1.25), (26.0, 1.25), (26.0, 1.75), (28.0, 1.75), (28.0, 1.25))
    assert actual == expected

def test_get_adjacency_dict_with_targets_and_obstacles():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [0],
             1: [1, 2],
             2: [2, 3],
             3: [3, 4, 5],
             4: [5],
             5: [6],
             6: [7]}

    assert actual == expected


def test_get_adjacency_dict_with_source_only():
    engine = adjacency.AdjacencyEngine(source_geoms, None, None, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [1],
             1: [0, 2],
             2: [1, 3],
             3: [2, 4],
             4: [3, 5],
             5: [4, 6],
             6: [5]}

    assert actual == expected

def test_get_adjacency_dict_with_source_and_obstacles():
    engine = adjacency.AdjacencyEngine(source_geoms, None, obstacle_geoms, True, 0.1)
    actual = engine.get_adjacency_dict()
    expected = {0: [1],
             1: [0, 2],
             2: [1, 3],
             3: [2, 4],
             4: [3, 5],
             5: [4, 6],
             6: [5]}

    assert actual == expected


def test_vor():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    expected = [26, 2, 4, 25, 37, 61, 60, 36, 38, 63, 44, 41, 39, 43, 21, 34, 23, 24, 22, 52, 54, 55,
                53, 67, 47, 65, 18, 5, 13, 59, 57, 58, 62, 27, 45, 40, 42, 7, 11, 12, 20, 33, 9, 10,
                31, 35, 28, 69, 29, 16, 15, 17, 19, 8, 14, 3, 6, 6, 1, 32, 30, 56, 50, 49, 51, 70,
                68, 64, 66, 48, 46]
    actual = list(engine.vor.point_region)
    assert actual == expected


def test_calc_segmentation_dist():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True)
    actual = engine.calc_segmentation_dist()
    expected = 1.147746358922793
    assert actual == expected


def test_get_feature_from_coord_index():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
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

    engine = adjacency.AdjacencyEngine(source_geoms_1, target_geoms_1, obstacle_geoms_1, False)
    engine._tag_feature_with_voronoi_vertices()

    assert engine.source_features[0].voronoi_points == {1, 2}
    assert engine.target_features[0].voronoi_points == {2, 3, 4}

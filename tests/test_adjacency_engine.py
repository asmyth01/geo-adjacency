from shapely.wkt import dumps

from geo_adjacency import adjacency
from geo_adjacency.utils import flatten_list

from tests.sample_data.wkts import source_geoms, target_geoms, obstacle_geoms


def test_flatten_list():
    assert list(flatten_list([[1, 2], [3, 4]])) == [1, 2, 3, 4]


def test_get_adjacency_matrix():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True, 0.001)
    actual = engine.get_adjacency_dict()
    expected = {
        0: [2, 3],
        1: [0],
        2: [0, 1, 2],
        3: [3, 4, 5],
        4: [5],
        5: [6],
        6: [7]
    }
    assert actual == expected


def test_vor():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    expected = [28,
 2,
 7,
 6,
 14,
 2,
 13,
 30,
 31,
 29,
 13,
 11,
 10,
 24,
 1,
 11,
 33,
 37,
 36,
 32,
 33,
 18,
 22,
 23,
 15,
 18,
 16,
 8,
 4,
 50,
 42,
 52,
 4,
 44,
 41,
 43,
 51,
 44,
 26,
 27,
 25,
 48,
 46,
 40,
 25,
 38,
 45,
 57,
 39,
 38,
 56,
 21,
 17,
 47,
 49,
 9,
 17,
 5,
 3,
 3,
 12,
 35,
 34,
 53,
 54,
 35,
 58,
 55,
 19,
 20,
 58]
    actual = list(engine.vor.point_region)
    assert actual == expected


def test_calc_segmentation_dist():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True)
    actual = engine.calc_segmentation_dist()
    expected = 1.068225655023215
    assert actual == expected


def test_get_feature_from_coord_index():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    actual = dumps(engine.get_feature_from_coord_index(50).geometry)
    expected = "LINESTRING (21.0000000000000000 2.0000000000000000, 26.0000000000000000 2.0000000000000000)"
    assert actual == expected

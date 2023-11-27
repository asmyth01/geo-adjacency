from shapely.wkt import dumps

from geo_adjacency import adjacency
from geo_adjacency.utils import flatten_list
from tests.utils import load_test_geoms

source_geoms, target_geoms, obstacle_geoms = load_test_geoms("sample_data")


def test_flatten_list():
    assert list(flatten_list([[1, 2], [3, 4]])) == [1, 2, 3, 4]


def test_get_adjacency_matrix():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True, 0.001)
    actual = engine.get_adjacency_dict()
    expected = {0: [4, 7], 1: [4], 3: [2, 3], 4: [3], 5: [3], 8: [4], 9: [0], 13: [2], 15: [3], 16: [0], 17: [0, 7]}
    assert actual == expected

def test_vor():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    expected = [23, 10, 21, 6, 9, 8, 5, 1, 2, 4, 45, 71, 14, 52, 0, 7, 3, 62, 60, 57, 63, 62, 26,
                64, 47, 27, 26, 92, 95, 94, 91, 92, 13, 76, 96, 97, 77, 73, 13, 93, 98, 70, 66, 93,
                48, 67, 51, 53, 48, 55, 54, 15, 16, 55, 30, 19, 58, 31, 30, 17, 22, 20, 24, 25, 18,
                17, 56, 46, 41, 29, 56, 44, 75, 79, 74, 44, 90, 69, 86, 68, 90, 72, 87, 50, 49, 72,
                11, 33, 37, 32, 11, 80, 82, 81, 78, 80, 85, 89, 88, 84, 85, 28, 12, 43, 40, 28, 61,
                99, 59, 100, 65, 39, 35, 83, 42, 36, 38]
    actual = list(engine.vor.point_region)
    assert actual == expected


def test_calc_segmentation_dist():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True)
    actual = engine.calc_segmentation_dist()
    expected = 0.0009346349219844988
    assert actual == expected

def test_get_feature_from_coord_index():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, False)
    actual = dumps(engine.get_feature_from_coord_index(50).geometry)
    expected = "POLYGON ((-122.4759872510099967 47.7276072458459026, -122.4759507224080011 47.7262312413106997, -122.4729188484759987 47.7262066694707983, -122.4730649628820061 47.7274598185273007, -122.4759872510099967 47.7276072458459026))"
    assert actual == expected

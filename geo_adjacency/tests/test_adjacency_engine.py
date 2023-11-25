from geo_adjacency import adjacency
from geo_adjacency.utils import flatten_list
from geo_adjacency.tests.utils import load_test_geoms

source_geoms, target_geoms, obstacle_geoms = load_test_geoms("sample_data")


def test_flatten_list():
    assert list(flatten_list([[1, 2], [3, 4]])) == [1, 2, 3, 4]


def test_get_adjacency_matrix():
    engine = adjacency.AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, True, 0.001)
    actual = engine.get_adjacency_dict()
    expected = {0: [4, 7], 1: [4], 3: [2, 3], 4: [3], 5: [3], 8: [4], 9: [0], 13: [2], 15: [3], 16: [0], 17: [0, 7]}
    assert actual == expected


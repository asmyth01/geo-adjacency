from collections import defaultdict

from geo_adjacency import adjacency
from geo_adjacency.utils import flatten_list
from tests.testUtils import load_test_geoms

source_geoms, target_geoms, sample_obstacles = load_test_geoms("sample_data")


ENGINE = adjacency.AdjacencyEngine(source_geoms, target_geoms, sample_obstacles)


def test_flatten_list():
    assert list(flatten_list([[1, 2], [3, 4]])) == [1, 2, 3, 4]


def test_get_adjacency_matrix():
    actual = ENGINE.get_adjacency_matrix()
    expected = {0: [1, 2], 1: [1], 2: [1], 3: [2], 4: [0], 5: [0], 6: [1], 7: [1], 8: [0], 9: [1]}
    assert actual == expected


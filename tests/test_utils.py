from shapely.wkt import loads

import geo_adjacency.utils
from geo_adjacency.utils import flatten_list


def test_flatten_list():
    test_data = [[(1, 2), (3, 4)], [(5, 6), (7, 8)], [(9, 10), [(11, 12), [(13, 14), [(15, 16)]]]]]
    assert list(flatten_list(test_data)) == [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)]


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

import pytest
from shapely.wkt import loads

import geo_adjacency.adjacency
from geo_adjacency.exception import ImmutablePropertyError
from geo_adjacency.adjacency import _Feature


def test_point_feature(point_feature_a):
    expected = [(30.0, 10.0)]
    assert point_feature_a.coords == expected


def test_line_feature():
    line = loads("LINESTRING (30 10, 10 30, 40 40)")
    expected = [(30.0, 10.0), (10.0, 30.0), (40.0, 40.0)]
    line_feature = geo_adjacency.adjacency._Feature(line)
    assert line_feature.coords == expected


def test_polygon_feature():
    polygon = loads("POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))")
    expected = [(30.0, 10.0), (40.0, 40.0), (20.0, 40.0), (10.0, 20.0)]
    polygon_feature = geo_adjacency.adjacency._Feature(polygon)
    assert polygon_feature.coords == expected


def test_polygon_w_interior():
    poylgon_w_interior = loads("POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, "
                               "30 20, 20 30))")
    polygon_feature = geo_adjacency.adjacency._Feature(poylgon_w_interior)
    expected = [(35.0, 10.0), (45.0, 45.0), (15.0, 40.0), (10.0, 20.0), (20.0, 30.0),
                (35.0, 35.0), (30.0, 20.0)]
    assert polygon_feature.coords == expected


def test_multipolygon_feature():
    multipolygon = loads("MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, "
                         "5 10, 15 5)))")
    expected = [(30.0, 20.0), (45.0, 40.0), (10.0, 40.0), (15.0, 5.0), (40.0, 10.0), (10.0, 20.0),
                (5.0, 10.0)]
    multipolygon_feature = geo_adjacency.adjacency._Feature(multipolygon)
    assert multipolygon_feature.coords == expected


def test_multipolygon_w_interior():
    multipolygon_w_interior = loads("MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, "
                                    "10 30, 10 10, 30 5, 45 20, 20 35),(30 20, 20 15, 20 25, "
                                    "30 20)))")
    multipolygon_feature = geo_adjacency.adjacency._Feature(multipolygon_w_interior)
    expected = [(40.0, 40.0), (20.0, 45.0), (45.0, 30.0), (20.0, 35.0), (10.0, 30.0),
                (10.0, 10.0), (30.0, 5.0), (45.0, 20.0), (30.0, 20.0), (20.0, 15.0),
                (20.0, 25.0)]
    assert multipolygon_feature.coords == expected


def test_feature_equality(point_geom_a):
    # We don't want to compare the geometry; rather whether the objects are the same instance.
    feature1 = geo_adjacency.adjacency._Feature(point_geom_a)
    feature2 = geo_adjacency.adjacency._Feature(point_geom_a)
    assert feature1 != feature2


def test_immutable_exception(point_feature_a):
    with pytest.raises(ImmutablePropertyError):
        point_feature_a.coords = (10, 10)


def test_change_feature_geometry(point_feature_a, point_feature_b):

    assert point_feature_a.coords == [(30.0, 10.0)]
    assert point_feature_b.coords == [(10.0, 10.0)]


def test_features_are_adjacent(point_feature_a, point_feature_b):
    point_feature_a.voronoi_points.update({1, 2, 3, 4, 5})
    point_feature_b.voronoi_points.update({4, 5, 6, 7})
    assert point_feature_a.is_adjacent(point_feature_b)


def test_features_are_not_adjacent(point_feature_a, point_feature_b):
    point_feature_a.voronoi_points.update({1, 2, 3})
    point_feature_b.voronoi_points.update({4, 5, 6})
    assert not point_feature_a.is_adjacent(point_feature_b)


def test_not_adjacent_only_one_shared_voronoi_vertex(point_feature_a, point_feature_b):
    point_feature_a.voronoi_points.update({1, 2, 3, 4})
    point_feature_b.voronoi_points.update({4, 5, 6})
    assert not point_feature_a.is_adjacent(point_feature_b)


def test_features_not_adjacent_empty_voronoi(point_feature_a, point_feature_b):
    assert not point_feature_a.is_adjacent(point_feature_b)


def test_invalid_geometry_type():
    geom = loads("GEOMETRYCOLLECTION (POINT (40 10), LINESTRING (10 10, 20 20, 10 40), POLYGON ((40 40, 20 45, 45 30, 40 40)))")
    with pytest.raises(TypeError):
        _Feature(geom)
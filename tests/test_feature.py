from shapely.wkt import loads

import geo_adjacency.adjacency


def test_point_feature():
    point = loads("POINT (30 10)")
    expected = [(30.0, 10.0)]
    point_feature = geo_adjacency.adjacency._Feature(point)
    assert point_feature.coords == expected


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

def test_feature_equality():
    feature1 = geo_adjacency.adjacency._Feature(loads("POINT (30 10)"))
    feature2 = geo_adjacency.adjacency._Feature(loads("POINT (30 10)"))
    assert feature1 == feature2

def test_feature_inequality():
    feature1 = geo_adjacency.adjacency._Feature(loads("POINT (30 10)"))
    feature2 = geo_adjacency.adjacency._Feature(loads("POINT (30 11)"))
    assert feature1 != feature2
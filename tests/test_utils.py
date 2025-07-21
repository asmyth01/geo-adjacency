"""
Test utility functions.
"""

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon
from shapely.wkt import loads

from geo_adjacency.utils import count_unique_coords

import pytest


def test_count_unique_coords_additional_types():
    """Test count_unique_coords with additional geometry types for better coverage."""
    # Test MultiLineString
    multiline = MultiLineString([
        LineString([(0, 0), (1, 1)]),
        LineString([(2, 2), (3, 3)])
    ])
    assert count_unique_coords(multiline) == 4
    
    # Test Polygon with holes
    exterior = [(0, 0), (0, 4), (4, 4), (4, 0), (0, 0)]
    hole = [(1, 1), (1, 3), (3, 3), (3, 1), (1, 1)]
    polygon_with_hole = Polygon(exterior, [hole])
    # Based on actual implementation: exterior + hole coords minus interior count minus 1
    assert count_unique_coords(polygon_with_hole) == 8
    
    # Test unknown geometry type error
    class UnknownGeometry:
        pass
    
    with pytest.raises(ValueError, match="Unknown geometry type"):
        count_unique_coords(UnknownGeometry())


def test_add_geometry_to_plot():
    """Test the add_geometry_to_plot function with different geometry types."""
    from geo_adjacency.utils import add_geometry_to_plot
    import matplotlib.pyplot as plt
    
    # Test with Point
    point = Point(1, 2)
    add_geometry_to_plot([point], "red")
    
    # Test with LineString
    line = LineString([(0, 0), (1, 1)])
    add_geometry_to_plot([line], "blue")
    
    # Test with Polygon
    polygon = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    add_geometry_to_plot([polygon], "green")
    
    # Test with MultiPolygon
    multi_poly = MultiPolygon([
        Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    ])
    add_geometry_to_plot([multi_poly], "yellow")
    
    # Test with unknown geometry type
    class UnknownGeom:
        pass
    
    with pytest.raises(TypeError, match="Unknown geometry type"):
        add_geometry_to_plot([UnknownGeom()], "black")
    
    plt.close()  # Clean up the plot 

def test_count_unique_coords():
    point = loads("POINT(10 1)")
    assert count_unique_coords(point) == 1
    line = loads("LINESTRING(0 0, 1 1)")
    assert count_unique_coords(line) == 2
    multilinestring = loads("MULTILINESTRING((0 0, 1 1), (2 2, 3 3))")
    assert count_unique_coords(multilinestring) == 4
    polygon = loads("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")
    assert count_unique_coords(polygon) == 4
    multipolygon = loads(
        "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)), ((3 0, 3 1, 5 1, 5 0, 3 0)))"
    )
    assert count_unique_coords(multipolygon) == 8

    with pytest.raises(ValueError):
        count_unique_coords(None)

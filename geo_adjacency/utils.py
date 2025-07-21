"""
Utility functions for geometric analysis and plotting.

This module provides utility functions for coordinate counting, geometry plotting,
and other spatial operations used internally by the AdjacencyEngine. These functions 
are designed for internal use and should not be called directly by end users.
"""

from matplotlib import pyplot as plt
from shapely import (
    LinearRing,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry


def add_geometry_to_plot(geoms, color="black"):
    """
    Add Shapely geometries to the current matplotlib plot.
    
    Useful for visualizing geometric data and test results. Each geometry type 
    is rendered appropriately (points as markers, lines as paths, polygons as outlines).

    Args:
        geoms (List[BaseGeometry]): A list of Shapely geometries to plot.
        color (str, optional): The color for rendering the geometries. Defaults to "black".

    Returns:
        None

    Raises:
        TypeError: If an unsupported geometry type is encountered.
    """
    for geom in geoms:
        if isinstance(geom, Point):
            plt.plot(
                geom.x,
                geom.y,
                marker="o",
                markersize=5,
                markeredgecolor="black",
                markerfacecolor=color,
            )
        elif isinstance(geom, LineString):
            plt.plot(*geom.coords.xy, color=color)
        elif isinstance(geom, Polygon):
            plt.plot(*geom.exterior.xy, color=color, linestyle="-")
        elif isinstance(geom, MultiPolygon):
            for sub_poly in geom.geoms:
                plt.plot(*sub_poly.exterior.xy, color=color, linewidth=3)
        else:
            raise TypeError("Unknown geometry type")


def count_unique_coords(geom: BaseGeometry) -> int:
    """
    Count the number of coordinate points in a Shapely geometry.
    
    This function counts all coordinate points that define a geometry's shape,
    with special handling for different geometry types:
    - Points: Always returns 1
    - LineStrings: Returns number of coordinate points
    - Polygons: Returns exterior coords + interior ring coords, minus duplicates
    - Multi-geometries: Sums coordinates from all component geometries
    
    Args:
        geom (BaseGeometry): The Shapely geometry to analyze.
    
    Returns:
        int: The total number of coordinate points in the geometry.
        
    Raises:
        ValueError: If the geometry type is not supported.
    """
    if isinstance(geom, Point):
        return 1
    elif isinstance(geom, LineString):
        return len(geom.coords)
    elif isinstance(geom, MultiLineString):
        return sum(len(line.coords) for line in geom.geoms)
    elif isinstance(geom, Polygon):
        return (
            len(geom.exterior.coords)
            + sum(len(ring.coords) for ring in geom.interiors)
            - len(geom.interiors)
            - 1
        )
    elif isinstance(geom, MultiPolygon):
        return sum(count_unique_coords(poly) for poly in geom.geoms)
    else:
        raise ValueError(f"Unknown geometry type: {type(geom)}")

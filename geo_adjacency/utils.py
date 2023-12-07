"""
Utility functions. These are designed for use in the AdjacencyEngine only, and should not be called
by end users.
"""

from typing import List, Tuple

from matplotlib import pyplot as plt
from shapely import Point, LineString, Polygon, MultiPolygon


def coords_from_point(point: Point) -> List[Tuple[float, float]]:
    """
    Convert a Point into a tuple of (x, y). We put this inside a list for consistency with other
    coordinate methods to allow us to seamlessly merge them later.

    Args:
        point (Point): A Shapely Point.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples.

    """
    assert isinstance(point, Point), "Geometry must be a Point, not '%s'." % type(point)
    return [(float(point.x), float(point.y))]


def coords_from_ring(ring: LineString) -> List[Tuple[float, float]]:
    """
    Convert a LinearRing into a list of (x, y) tuples.

    Args:
        ring (LineString): A Shapely LinearString.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples.
    """
    assert isinstance(
        ring, LineString
    ), "Geometry must be a LinearRing, not '%s'." % type(ring)
    return [(float(coord[0]), float(coord[1])) for coord in ring.coords]


def coords_from_polygon(polygon: Polygon) -> List[Tuple[float, float]]:
    """
    Convert a Polygon into a list of (x, y) tuples. Does not repeat the first coordinate to close
    the ring.

    Args:
        polygon (Polygon): A Shapely Polygon.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples.
    """
    assert isinstance(polygon, Polygon), "Geometry must be a Polygon, not '%s'." % type(
        polygon
    )
    coords = []
    coords.extend(coords_from_ring(polygon.exterior)[:-1])
    for ring in polygon.interiors:
        coords.extend(coords_from_ring(ring)[:-1])
    return coords


def coords_from_multipolygon(multipolygon: MultiPolygon) -> List[Tuple[float, float]]:
    """
    Convert a MultiPolygon into a list of (x, y) tuples. Does not repeat the first coordinate to
    close the ring.

    Args:
        multipolygon (MultiPolygon): A Shapely MultiPolygon.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples.
    """
    assert isinstance(
        multipolygon, MultiPolygon
    ), "Geometry must be a MultiPolygon, not '%s'." % type(multipolygon)
    coords = []
    for polygon in multipolygon.geoms:
        coords.extend(coords_from_polygon(polygon))
    return coords


def flatten_list(nested_list) -> List:
    """
    Flatten a list of lists.
    Args:
        nested_list (List): A list of lists.

    Returns:

    """
    # check if list is empty
    if not bool(nested_list):
        return nested_list

    # to check instance of list is empty or not
    if isinstance(nested_list[0], list):
        # call function with sublist as argument
        return flatten_list(*nested_list[:1]) + flatten_list(nested_list[1:])

    # Call function with sublist as argument
    return nested_list[:1] + flatten_list(nested_list[1:])


def add_geometry_to_plot(geoms, color="black"):
    """
    When updating the test data, it may be useful to visualize it. Add a geometry to the global
    maplotlib plt object. The next time we call plt.show(), this geometry will be plotted.

    Args:
        geoms (List[BaseGeometry]): A list of Shapely geometries.
        color (str): The color we want the geometry to be in the plot.

    Returns:
        None
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

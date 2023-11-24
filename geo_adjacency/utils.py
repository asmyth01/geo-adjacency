"""
Convenience functions.
"""

from matplotlib import pyplot as plt
from shapely import Point, LineString, Polygon, MultiPolygon


def flatten_list(list_of_lists):
    """
    Flattens a list of lists.
    :param list_of_lists: The list of lists.
    :return: A flattened list.
    """
    flattened_list = []

    for sublist in list_of_lists:
        for item in sublist:
            flattened_list.append(item)

    return flattened_list


def add_geometry_to_plot(geoms, color="black"):
    """
    When updating the test data, it may be useful to visualize it.
    :param geoms:
    :param color:
    :return:
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

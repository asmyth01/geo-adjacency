from shapely import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry

from geo_adjacency.exception import ImmutablePropertyError
from geo_adjacency.utils import (
    coords_from_multipolygon,
    coords_from_point,
    coords_from_polygon,
    coords_from_ring,
)

try:
    from typing_extensions import Self  # Python < 3.11
except ImportError:
    from typing import Self  # Python >= 3.11

import logging
from typing import List, Tuple, Union

from geo_adjacency.logging_config import setup_logger

# Create a custom logger using the centralized logging configuration
log: logging.Logger = setup_logger(__name__)


class Feature:
    """
    A Feature is a wrapper around a Shapely geometry that allows us to easily determine if two
    geometries are adjacent.
    """

    __slots__ = ("_geometry", "_coords", "voronoi_points", "_bounds", "_coord_count")

    def __init__(self, geometry: BaseGeometry):
        """
        Create a Feature from a Shapely geometry.

        Args:
            geometry (BaseGeometry): A valid Shapely Geometry, either a Point, LineString, Polygon, or
        MultiPolygon.
        """

        if not isinstance(geometry, (Point, Polygon, MultiPolygon, LineString)):
            raise TypeError(
                "Cannot create Feature for geometry type '%s'." % type(geometry)
            )

        assert geometry.is_valid, (
            "Could not process invalid geometry: %s" % geometry.wkt
        )

        self._geometry: BaseGeometry = geometry
        self._coords: Union[List[Tuple[float, float]], None] = None
        self.voronoi_points: set = set()
        self._bounds: Union[Tuple[float, float, float, float], None] = None
        self._coord_count: Union[int, None] = None

    def __str__(self):
        return str(self.geometry)

    def __repr__(self):
        return f"<Feature: {str(self.geometry)}>"

    def _is_adjacent(
        self, other: Self, min_overlapping_voronoi_vertices: int = 2
    ) -> bool:
        """
        Determine if two features are adjacent based on how many Voronoi vertices they share. Note:
        the Voronoi analysis must have been run, or this will always return False.
        Args:
            other (Feature): Another Feature to compare to.
            min_overlapping_voronoi_vertices (int): The minimum number of Voronoi vertices that
                must be shared to be considered adjacent.

        Returns:
            bool: True if the two features are adjacent.

        """
        assert isinstance(other, type(self)), "Cannot compare '%s' with '%s'." % (
            type(self),
            type(other),
        )
        if len(self.voronoi_points) == 0 and len(other.voronoi_points) == 0:
            log.warning(
                "No Voronoi vertices found for either feature. Did you run the analysis yet?"
            )
            return False
        return (
            len(self.voronoi_points & other.voronoi_points)
            >= min_overlapping_voronoi_vertices
        )

    @property
    def geometry(self):
        """
        Access the Shapely geometry of the feature.

        Returns:
            BaseGeometry: The Shapely geometry of the feature.

        """
        return self._geometry

    @geometry.setter
    def geometry(self, geometry):
        self._geometry = geometry
        self._coords = None
        self._bounds = None
        self._coord_count = None

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Cached bounds of the geometry.
        """
        if self._bounds is None:
            self._bounds = self.geometry.bounds
        return self._bounds

    @property
    def coord_count(self) -> int:
        """
        Cached count of coordinates in this feature.
        """
        if self._coord_count is None:
            self._coord_count = len(self.coords)
        return self._coord_count

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """
        Convenience property for accessing the coordinates of the geometry as a list of 2-tuples.

        Returns:
            List[Tuple[float, float]]: A list of coordinate tuples.

        """

        if not self._coords:
            if isinstance(self.geometry, Point):
                self._coords = coords_from_point(self.geometry)
            elif isinstance(self.geometry, LineString):
                self._coords = coords_from_ring(self.geometry)
            elif isinstance(self.geometry, Polygon):
                self._coords = coords_from_polygon(self.geometry)
            elif isinstance(self.geometry, MultiPolygon):
                self._coords = coords_from_multipolygon(self.geometry)
            else:
                raise TypeError(f"Unknown geometry type '{type(self.geometry)}'")
        return self._coords

    @coords.setter
    def coords(self, coords):
        raise ImmutablePropertyError("Property coords is immutable.")

"""
The `adjacency` module implements the AdjacencyEngine class,
which allows us to determine adjacency relationships. Adjacency relationships are between a set of source geometries,
 or between source geometries and a second set of target geometries. Obstacle geometries can be passed in to
 stand between sources or sources and targets, but they are not included in the output.

 For example, if we wanted to know what trees in a forest are adjacent to the shore of a lake, we could
 pass in a set of Point geometries to the trees, a Polygon to represent the lake, and a LineString to represent
 a road passing between some of the trees and the shore.

 `AdjacencyEngine` utilizes a Voronoi of all the vertices in all the geometries combined to determine
 which geomtries are adjacent to each other. See
"""

import math
from collections import defaultdict
from typing import List, Union, Dict, Tuple
try:
    from typing_extensions import Self  # Python < 3.11
except ImportError:
    from typing import Self  # Python >= 3.11
import logging

import matplotlib.pyplot as plt
import numpy as np
import shapely.ops
from scipy.spatial import distance
from scipy.spatial import Voronoi
from shapely import LineString, Point, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry

from geo_adjacency.exception import ImmutablePropertyError
from geo_adjacency.utils import (
    add_geometry_to_plot,
    coords_from_point,
    coords_from_ring,
    coords_from_polygon,
    coords_from_multipolygon,
)

# ToDo: Support geometries with Z-coordinates

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.WARNING)

# Create formatters and add it to handlers
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)

# Add handlers to the logger
logger.addHandler(c_handler)


class _Feature:
    __slots__ = ("_geometry", "_coords", "voronoi_points")

    def __init__(self, geometry: BaseGeometry):
        if not isinstance(geometry, (Point, Polygon, MultiPolygon, LineString)):
            raise TypeError(
                "Cannot create _Feature for geometry type '%s'." % type(self.geometry)
            )

        self._geometry: BaseGeometry = geometry
        self._coords = None
        self.voronoi_points: set = set()

    def __str__(self):
        return str(self.geometry)

    def __repr__(self):
        return f"<_Feature: {str(self.geometry)}>"

    def __eq__(self, other: Self):
        if not isinstance(other, type(self)):
            return False
        return self.geometry.equals_exact(other.geometry, 1e-8)

    def __ne__(self, other: Self):
        return not self.__eq__(other)

    def is_adjacent(
        self, other: Self, min_overlapping_voronoi_vertices: int = 2
    ) -> bool:
        """
        Determine if two features are adjacent based on how many Voronoi vertices they share. Note:
        the Voronoi analysis must have been run, or this will always return False.
        :param min_overlapping_voronoi_vertices:
        :param other:
        :return:
        """
        assert isinstance(other, type(self)), "Cannot compare '%s' with '%s'." % (
            type(self),
            type(other),
        )
        if len(self.voronoi_points) == 0 and len(other.voronoi_points) == 0:
            logger.warning(
                "No Voronoi vertices found for either feature. Did you run the analysis yet?"
            )
        return (
            len(self.voronoi_points & other.voronoi_points)
            >= min_overlapping_voronoi_vertices
        )

    @property
    def geometry(self):
        """
        Access the Shapely geometry of the feature.
        :return: BaseGeometry
        """
        return self._geometry

    @geometry.setter
    def geometry(self, geometry):
        self._geometry = geometry
        self._coords = None

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """
        Convenience property for accessing the coordinates of the geometry as a list of 2-tuples.

        :return: List[Tuple[float, float]]: A list of coordinate tuples.
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


class AdjacencyEngine:
    """
    A class for calculating the adjacency of a set of geometries to another geometry or set
    of geometries, given a set of obstacles, within a given radius.

    First, the Voronoi diagram is generated for each geometry and obstacle. Then, we check which
    voronoi shapes intersect one another. If they do, then the two underlying geometries are
    adjacent.

    :ivar all_features: List of all features in order of source, target, and obstacle.
    :ivar all_coordinates: List of all coordinates in the same order as all_features.
    """

    __slots__ = (
        "_source_features",
        "_target_features",
        "_obstacle_features",
        "_adjacency_dict",
        "_feature_indices",
        "_vor",
        "all_features",
        "_all_coordinates",
    )

    def __init__(
        self,
        source_geoms: List[BaseGeometry],
        target_geoms: Union[List[BaseGeometry], None] = None,
        obstacle_geoms: Union[List[BaseGeometry], None] = None,
        densify_features: bool = False,
        max_segment_length: Union[float, None] = None,
    ):
        """
        Note: only Multipolygons, Polygons, LineStrings and Points are supported. It is assumed all
        features are in the same projection.

        :param source_geoms: List of Shapely geometries. We will which ones are adjacent to
        which others.
        :param target_geoms: Optional list of Shapley geometries. if not None, We will
        test if these features are adjacent to the source features.
        :param obstacle_geoms: List
        of Shapely geometries. These features will not be tested for adjacency, but they can
        prevent a source and target feature from being adjacent.
        :param densify_features: If
        True, we will add additional points to the features to improve accuracy of the voronoi
        diagram.
        :param max_segment_length: The maximum distance between vertices that we want.
        In projection units. densify_features must be True, or an error will be thrown. If
        densify_features is True and max_segment_length is false, then the max_segment_length
        will be calculated based on the average segment length of all features, divided by 5.
        This often works well.
        """

        if max_segment_length and not densify_features:
            raise ValueError(
                "interpolate_points must be True if interpolation_distance is not None"
            )

        self._source_features: Tuple[_Feature] = tuple(
            [_Feature(geom) for geom in source_geoms]
        )
        self._target_features: Tuple[_Feature] = (
            tuple([_Feature(geom) for geom in target_geoms])
            if target_geoms
            else tuple()
        )
        self._obstacle_features: Union[Tuple[_Feature], None] = (
            tuple([_Feature(geom) for geom in obstacle_geoms])
            if obstacle_geoms
            else tuple()
        )
        self._adjacency_dict = None
        self._feature_indices = None
        self._vor = None
        self._all_coordinates = None

        """All source, target, and obstacle features in a single list. The order of this list must
        not be changed."""
        self.all_features: Tuple[_Feature, ...] = tuple(
            [*self.source_features, *self.target_features, *self.obstacle_features]
        )

        if densify_features:
            if max_segment_length is None:
                max_segment_length = self.calc_segmentation_dist()
                logger.info("Calculated max_segment_length of %s" % max_segment_length)

            for feature in self.all_features:
                if not isinstance(feature.geometry, Point):
                    feature.geometry = feature.geometry.segmentize(max_segment_length)
            # Reset all coordinates
            self._all_coordinates = None

    @property
    def all_coordinates(self):
        if not self._all_coordinates:
            self._all_coordinates = []
            for feature in self.all_features:
                self._all_coordinates.extend(feature.coords)

            self._all_coordinates = tuple(self._all_coordinates)
        return self._all_coordinates

    @all_coordinates.setter
    def all_coordinates(self, value):
        raise ImmutablePropertyError("Property all_coordinates is immutable.")

    def calc_segmentation_dist(self, divisor=5):
        """
        Try to create a well-fitting maximum length for all line segments in all features. Take
        the average distance between all coordinate pairs and divide by 5. This means that the
        average segment will be divided into five segments.

        This won't work as well if the different geometry sets have significantly different
        average segment lengths. In that case, it is advisable to prepare the data appropriately
        beforehand.

        :param divisor: Divide the average segment length by this number to get the new desired
        segment length.

        :return: Average segment length divided by divisor
        """

        return float(
            (
                sum(distance.pdist(self.all_coordinates, "euclidean"))
                / math.pow(len(self.all_coordinates), 2)
            )
            / divisor
        )

    @property
    def source_features(self) -> Tuple[_Feature]:
        """
        Features which will be the keys in the adjacency_dict.
        :return: List of source features.
        """
        return self._source_features

    @source_features.setter
    def source_features(self, features: Tuple[BaseGeometry]):
        raise ImmutablePropertyError("Property source_features is immutable.")

    @property
    def target_features(self) -> Tuple[_Feature]:
        """
        Features which will be the values in the adjacency_dict.
        :return: List of target features.
        """
        return self._target_features

    @target_features.setter
    def target_features(self, _):
        raise ImmutablePropertyError("Property target_features is immutable.")

    @property
    def obstacle_features(self) -> Tuple[_Feature]:
        """
        Features which can prevent source and target features from being adjacent. They
        Do not participate in the adjacency_dict.
        :return: List of obstacle features.
        """
        return self._obstacle_features

    @obstacle_features.setter
    def obstacle_features(self, _):
        raise ImmutablePropertyError("Property obstacle_features is immutable.")

    def get_feature_from_coord_index(self, coord_index: int) -> _Feature:
        """
        A list which is the length of self._all_coordinates. For each coordinate, we add the
        index of the corresponding feature from the list self.all_features. This is used to
        determine which coordinate belongs to which feature after we calculate the voronoi
        diagram.

        :return: A _Feature.

        """
        if not self._feature_indices:
            self._feature_indices = {}
            c = -1
            for f, feature in enumerate(self.all_features):
                for _ in range(len(feature.coords)):
                    c += 1
                    self._feature_indices[c] = f

        return self.all_features[self._feature_indices[coord_index]]

    @property
    def vor(self):
        """
        The Voronoi diagram object returned by Scipy. Useful primarily for debugging an
        adjacency analysis.

        :return: Voronoi object.
        """

        if not self._vor:
            self._vor = Voronoi(np.array(self.all_coordinates))
        return self._vor

    @vor.setter
    def vor(self, _):
        raise ImmutablePropertyError("Property vor is immutable.")

    def _tag_feature_with_voronoi_vertices(self):
        """
        Tag each feature with the vertices of the voronoi region it belongs to. Runs the
        voronoi analysis if it has not been done already. This is broken out mostly for testing.
        Do not call this function directly.
        :return:
        """
        # We don't need to tag obstacles with their voronoi vertices
        obstacle_coord_len = sum(len(feat.coords) for feat in self.obstacle_features)

        # Tag each feature with the vertices of the voronoi region it
        # belongs to
        for feature_coord_index in range(
            len(self.all_coordinates) - obstacle_coord_len
        ):
            feature = self.get_feature_from_coord_index(feature_coord_index)
            for voronoi_vertex_index in self.vor.regions[
                self.vor.point_region[feature_coord_index]
            ]:
                # "-1" indices indicate the vertex goes to infinity. These don't provide us
                # with adjacency information, so we ignore them.
                if voronoi_vertex_index != -1:
                    feature.voronoi_points.add(voronoi_vertex_index)

    def _determine_adjacency(
        self, source_set: Tuple[_Feature], target_set: Tuple[_Feature]
    ):
        """
        Determines the adjacency relationship between two sets of features.
        Parameters:
            source_set (Tuple[_Feature]): The set of source features.
            target_set (Tuple[_Feature]): The set of target features.
        Returns:
            None
        """
        min_overlapping_voronoi_vertices = 2
        for source_index, source_feature in enumerate(source_set):
            for target_index, target_feature in enumerate(target_set):
                if source_feature != target_feature and source_feature.is_adjacent(
                    target_feature, min_overlapping_voronoi_vertices
                ):
                    self._adjacency_dict[source_index].append(target_index)

    def get_adjacency_dict(self) -> Dict[int, List[int]]:
        """
        Returns a dictionary of indices. They keys are the indices of feature_geoms. The values
        are the indices of any target geometries which are adjacent to the feature_geoms.

        If no targets were specified, then calculate adjacency between source features and other
        source features.

        :return: dict A dictionary of indices. The keys are the indices of feature_geoms. The
        values are the indices of any adjacent features
        """

        # We want adjacent features to have at least two overlapping vertices, otherwise we might
        # call the features adjacent when their voronoi regions don't share any edges.

        if self._adjacency_dict is None:
            self._tag_feature_with_voronoi_vertices()

            # If any two features have any voronoi indices in common, then their voronoi regions
            # must intersect, therefore the input features are adjacent.
            self._adjacency_dict = defaultdict(list)

            # Get adjacency between source and target features
            if len(self.target_features) > 0:
                self._determine_adjacency(self.source_features, self.target_features)
            # If no target specified, get adjacency between source and other source features.
            else:
                self._determine_adjacency(self.source_features, self.source_features)

        return self._adjacency_dict

    def plot_adjacency_dict(self) -> None:
        """
        Plot the adjacency linkages between the source and target with pyplot. Runs the analysis if
        it has not already been run.
        :return: None
        """
        # Plot the adjacency linkages between the source and target
        if len(self.target_features) > 0:
            for source_i, target_is in self.get_adjacency_dict().items():
                source_poly = self.source_features[source_i].geometry
                target_polys = [
                    self.target_features[target_i].geometry for target_i in target_is
                ]

                # Plot the linestrings between the source and target polygons
                links = []
                for target_poly in target_polys:
                    if target_poly:
                        try:
                            links.append(
                                LineString(
                                    shapely.ops.nearest_points(target_poly, source_poly)
                                )
                            )
                        except ValueError:
                            logger.error(
                                f"Error creating link between '{target_poly}' and '{source_poly}'"
                            )
                add_geometry_to_plot(links, "green")

        else:
            for source_i, source_2_is in self.get_adjacency_dict().items():
                source_poly = self.source_features[source_i].geometry
                target_polys = [
                    self.source_features[source_2_i].geometry
                    for source_2_i in source_2_is
                    if source_2_i > source_i
                ]

                # Plot the linestrings between the source and target polygons
                links = [
                    LineString([target_poly.centroid, source_poly.centroid])
                    for target_poly in target_polys
                    if target_poly is not None
                ]
                add_geometry_to_plot(links, "green")

        add_geometry_to_plot([t.geometry for t in self.target_features], "blue")
        add_geometry_to_plot([t.geometry for t in self.source_features], "grey")
        add_geometry_to_plot([t.geometry for t in self.obstacle_features], "red")

        plt.title("Adjacency linkages between source and target")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()

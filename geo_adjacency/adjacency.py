"""
Calculate adjacency relationships between features, based on the intersection of their Voronoi
diagram regions.
"""

import math
import os
import time
from collections import defaultdict
from typing import List, Union, Dict, Tuple
import logging

from scipy.spatial import distance, voronoi_plot_2d
from scipy.spatial import Voronoi
from shapely import Polygon, MultiPolygon, LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points
from shapely.wkt import loads
from shapely.geometry import mapping
import numpy as np
import matplotlib.pyplot as plt

from geo_adjacency.exception import ImmutablePropertyError
from geo_adjacency.utils import flatten_list, add_geometry_to_plot

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler("file.log")
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


class _Feature:
    __slots__ = ("_geometry", "_coords", "voronoi_points")

    def __init__(self, geometry: BaseGeometry):
        self._geometry: BaseGeometry = geometry
        self._coords = None
        self.voronoi_points: set = set()

    def __str__(self):
        return str(self.geometry)

    @property
    def geometry(self):
        """
        Acess the Shapely geometry of the feature.
        :return:
        """
        return self._geometry

    @geometry.setter
    def geometry(self, geometry):
        self._geometry = geometry
        self._coords = None

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """
        Convenience property for accessing the coordinates of the geometry.

        :return: List[Tuple[float, float]]: A list of coordinate tuples.
        """
        if not self._coords:
            if isinstance(self.geometry, Point):
                self._coords = [(self.geometry.x, self.geometry.y)]
            elif isinstance(self.geometry, Polygon):
                self._coords = mapping(self.geometry)["coordinates"][0]
            elif isinstance(self.geometry, MultiPolygon):
                self._coords = flatten_list(
                    mapping(self.geometry)["coordinates"][0])
            elif isinstance(self.geometry, LineString):
                self._coords = list((x, y) for x, y in self.geometry.coords)
            else:
                raise TypeError(
                    f"Unknown geometry type '{type(self.geometry)}'")
        return self._coords


class AdjacencyEngine:
    """
    A class for calculating the adjacency of a set of geometries to another geometry or set
    of geometries, given a set of obstacles, within a given radius.

    First, the Voronoi diagram is generated for each geometry and obstacle. Then, we check which
    voronoi shapes intersect one another. If they do, then the two underlying geometries are
    adjacent.
    """

    __slots__ = ("_source_features", "_target_features", "_obstacle_features", "_adjacency_dict",
                 "_feature_indices", "_vor", "all_features", "all_coordinates")

    def __init__(
            self,
            source_geoms: List[BaseGeometry],
            target_geoms: List[BaseGeometry],
            obstacle_geoms: Union[List[BaseGeometry], None] = None,
            densify_features: bool = False,
            max_segment_length: Union[float, None] = None,
    ):
        """
        Note: only Multipolygons, Polygons, and LineStrings are supported. It is assumed all
        features are in the same projection.

        :param source_geoms: List of Shapely geometries. We will test if these features are
        adjacent to the target features. :param target_geoms: List of Shapley geometries. We will
        test if these features are adjacent to the source features. :param obstacle_geoms: List
        of Shapely geometries. These features will not be tested for adjacency, but they can
        prevent a source and target feature from being adjacent. :param densify_features: If
        True, we will add additional points to the features to improve accuracy of the voronoi
        diagram. :param max_segment_length: The maximum distance between vertices that we want.
        In projection units. densify_features must be True, or an error will be thrown. If
        densify_features is True and max_segment_length is false, then the max_segment_length
        will be calculated based on the average segment length of all features, divided by 5.
        This often works well.
        """

        if max_segment_length and not densify_features:
            raise ValueError(
                "interpolate_points must be True if interpolation_distance is not None"
            )

        self._source_features: List[_Feature] = [
            _Feature(geom) for geom in source_geoms
        ]
        self._target_features: List[_Feature] = [
            _Feature(geom) for geom in target_geoms
        ]
        self._obstacle_features: Union[List[_Feature], None] = [
            _Feature(geom) for geom in obstacle_geoms
        ]
        self._adjacency_dict = None
        self._feature_indices = None
        self._vor = None

        self.all_features: List[_Feature] = [
            *self.source_features,
            *self.target_features,
            *self.obstacle_features,
        ]

        if densify_features:
            if max_segment_length is None:
                max_segment_length = self.calc_segmentation_dist()
                logger.info("Calculated max_segment_length of %s" % max_segment_length)

            for feature in self.all_features:
                feature.geometry = feature.geometry.segmentize(
                    max_segment_length)

        self.all_coordinates = flatten_list(
            [feature.coords for feature in self.all_features]
        )

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

        :return:
        """

        all_coordinates = flatten_list(
            [feature.coords for feature in self.all_features]
        )
        return float(
            (
                    sum(distance.pdist(all_coordinates, "euclidean"))
                    / math.pow(len(all_coordinates), 2)
            )
            / divisor
        )

    @property
    def source_features(self) -> List[_Feature]:
        """
        Features which will be the keys in the adjacency_dict.
        :return: List of source features.
        """
        return self._source_features

    @source_features.setter
    def source_features(self, features: List[BaseGeometry]):
        raise ImmutablePropertyError("Property source_features is immutable.")

    @property
    def target_features(self) -> List[_Feature]:
        """
        Features which will be the values in the adjacency_dict.
        :return: List of target features.
        """
        return self._target_features

    @target_features.setter
    def target_features(self, _):
        raise ImmutablePropertyError("Property target_features is immutable.")

    @property
    def obstacle_features(self) -> List[_Feature]:
        """
        Features which can prevent source and target features from being adjacent. They
        Do not participate in the adjacency_dict.
        :return: List of obstacle features.
        """
        return self._obstacle_features

    @obstacle_features.setter
    def obstacle_features(self, _):
        raise ImmutablePropertyError(
            "Property obstacle_features is immutable.")

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

    def get_adjacency_dict(self) -> Dict[int, List[int]]:
        """
        Returns a dictionary of indices. They keys are the indices of feature_geoms. The values
        are the indices of any target geometries which are adjacent to the feature_geoms.

        :return: dict A dictionary of indices. The keys are the indices of feature_geoms. The
        values are the indices of any
        """

        if self._adjacency_dict is None:
            # We don't need to tag obstacles with their voronoi vertices
            obstacle_coord_len = sum(
                len(feat.coords) for feat in self.obstacle_features
            )

            # Tag each feature with the vertices of the voronoi region it
            # belongs to
            for coord_index in range(
                    len(self.all_coordinates) - obstacle_coord_len):
                feature = self.get_feature_from_coord_index(coord_index)
                for vor_vertex_index in self.vor.regions[
                    self.vor.point_region[coord_index]
                ]:
                    # "-1" indices indicate the vertex goes to infinity. These don't provide us
                    # with adjacency information, so we ignore them.
                    if vor_vertex_index != -1:
                        feature.voronoi_points.add(vor_vertex_index)

            # If any two features have any voronoi indices in common, then their voronoi regions
            # must intersect, therefore the input features are adjacent.
            self._adjacency_dict = defaultdict(list)

            for coord_index, source_feature in enumerate(self.source_features):
                for vor_region_index, target_feature in enumerate(
                        self.target_features):
                    if (
                            len(
                                source_feature.voronoi_points
                                & target_feature.voronoi_points
                            )
                            > 1
                    ):
                        self._adjacency_dict[coord_index].append(
                            vor_region_index)

        return self._adjacency_dict

    def plot_adjacency_dict(self) -> None:
        """
        Plot the adjacency linkages between the source and target with pyplot. Runs the analysis if
        it has not already been run.
        :return: None
        """
        # Plot the adjacency linkages between the source and target
        for source_i, target_is in self.get_adjacency_dict().items():
            source_poly = self.source_features[source_i].geometry
            target_polys = [
                self.target_features[target_i].geometry for target_i in
                target_is
            ]

            # Plot the linestrings between the source and target polygons
            links = [
                LineString(
                    [nearest_points(source_poly, target_poly)
                     [1], source_poly.centroid]
                )
                for target_poly in target_polys
            ]
            add_geometry_to_plot(links, "green")

        add_geometry_to_plot(
            [t.geometry for t in self.target_features], "blue")
        add_geometry_to_plot(
            [t.geometry for t in self.source_features], "grey")
        add_geometry_to_plot(
            [t.geometry for t in self.obstacle_features], "red")

        plt.title("Adjacency linkages between source and target")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()


def load_test_geoms(
        test_data_dir,
) -> Tuple[List[BaseGeometry], List[BaseGeometry], List[BaseGeometry]]:
    """
    Load some test data
    """

    with open(os.path.join(test_data_dir, "source.csv"),
              encoding="utf-8") as f:
        source_geoms = [loads(line) for line in f.readlines()]

    with open(os.path.join(test_data_dir, "target.csv"),
              encoding="utf-8") as f:
        target_geoms = [loads(line) for line in f.readlines()]

    with open(os.path.join(test_data_dir, "obstacle.csv"),
              encoding="utf-8") as f:
        obstacle_geoms = [loads(line) for line in f.readlines()]

    return source_geoms, target_geoms, obstacle_geoms


if __name__ == "__main__":
    s, t, o = load_test_geoms("../tests/sample_data")
    engine = AdjacencyEngine(s, t, o, True, 0.001)
    fig = voronoi_plot_2d(engine.vor)
    plt.show()
    start = time.time()
    print(engine.get_adjacency_dict())
    print("elapsed time: ", time.time() - start)

    engine.plot_adjacency_dict()

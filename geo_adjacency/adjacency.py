import math
import os
import time
from collections import defaultdict
from typing import List, Union, Dict, Tuple

from scipy.spatial import distance
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely import Polygon, MultiPolygon, LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points
from shapely.wkt import loads
from shapely.geometry import mapping
import numpy as np
import matplotlib.pyplot as plt
import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

# ToDo: More tests
# ToDo: build wheel
# ToDo: Publish to Pipy


def flatten_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


class Feature:
    __slots__ = ("_geometry", "_coords", "voronoi_points")

    def __init__(self, geometry: BaseGeometry):
        self._geometry: BaseGeometry = geometry
        self._coords = None
        self.voronoi_points: set = set()

    def __str__(self):
        return str(self.geometry)

    @property
    def geometry(self):
        return self._geometry

    @geometry.setter
    def geometry(self, geometry):
        self._geometry = geometry
        self._coords = None

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """
        Convenience property for accessing the coordinates of the geometry.
        Returns:
            List[Tuple[float, float]]: A list of coordinate tuples.
        """
        if not self._coords:
            if isinstance(self.geometry, Polygon) or isinstance(self.geometry, MultiPolygon):
                self._coords = mapping(self.geometry)['coordinates'][0]
            elif isinstance(self.geometry, LineString):
                self._coords = [(x, y) for x, y in self.geometry.coords]

        return self._coords


class AdjacencyEngine:
    """
    A class for calculating the adjacency of a set of geometries to another geometry or set
    of geometries, given a set of obstacles, within a given radius.

    First, the Voronoi diagram is generated for each geometry and obstacle. Then, we check which
    voronoi shapes intersect one another. If they do, then the two underlying geometries are adjacent.
    """

    def __init__(self, source_geoms: List[BaseGeometry], target_geoms: List[BaseGeometry],
                 obstacle_geoms: Union[List[BaseGeometry], None] = None, densify_features: bool = False,
                 max_segment_length: Union[float, None] = None):
        if max_segment_length and not densify_features:
            raise ValueError("interpolate_points must be True if interpolation_distance is not None")

        self._source_features: List[Feature] = []
        self._target_features: List[Feature] = []
        self._obstacle_features: Union[List[Feature], None] = []
        self._adjacency_matrix = None
        self._feature_indices = None

        self.source_features: List[Feature] = source_geoms
        self.target_features: List[Feature] = target_geoms
        self.obstacle_features: Union[List[Feature], None] = obstacle_geoms

        self.all_features = [*self.source_features, *self.target_features,
                             *self.obstacle_features]  # ToDo: Update this if any features are added

        if densify_features:
            if max_segment_length is None:
                max_segment_length = self.calc_segmentation_dist()
                logger.info(f"Calculated max_segment_length of {max_segment_length}")

            for feature in self.all_features:
                feature.geometry = feature.geometry.segmentize(max_segment_length)

        self.all_coordinates = flatten_list([feature.coords for feature in self.all_features])

    def calc_segmentation_dist(self, divisor=5):
        """
        Try to create a well-fitting maximum length for all line segments in all features. Take the average distance
        between all coordinate pairs and divide by 5. This means that the average segment will be divided into five
        segments.

        This won't work as well if the different geometry sets have significantly different average segment lengths.
        In that case, it is advisable to prepare the data appropriately beforehand.
        Returns:

        """
        all_coordinates = flatten_list([feature.coords for feature in self.all_features])
        return float((sum(distance.pdist(all_coordinates, 'euclidean')) / math.pow(len(all_coordinates), 2)) / divisor)

    @property
    def source_features(self) -> List[Feature]:
        return self._source_features

    @source_features.setter
    def source_features(self, features: List[BaseGeometry]):
        assert isinstance(features, list), "'source_features' must be a list"
        assert len(features) > 0, "'source_features' must contain at least one geometry"
        self._adjacency_matrix = None
        self._source_features = [Feature(geom) for geom in features]

    @property
    def target_features(self) -> List[Feature]:
        return self._target_features

    @target_features.setter
    def target_features(self, features: List[BaseGeometry]):
        assert isinstance(features, list), "'target_features' must be a list"
        assert len(features) > 0, "'target_features' must contain at least one geometry"
        self._adjacency_matrix = None
        self._target_features = [Feature(geom) for geom in features]

    @property
    def obstacle_features(self) -> List[Feature]:
        self._adjacency_matrix = None
        return self._obstacle_features

    @obstacle_features.setter
    def obstacle_features(self, features: List[BaseGeometry]):
        self._adjacency_matrix = None
        self._obstacle_features = [Feature(geom) for geom in features]

    @property
    def feature_indices(self):
        if not self._feature_indices:
            self._feature_indices = [i for i in range(len(self.all_features)) for _ in
                                     range(len(self.all_features[i].coords))]

        return self._feature_indices

    def get_feature_from_coord_index(self, coord_index: int) -> Feature:
        """
        Given an index in the self.all_coordinates list, determine which feature from self.all_features the coordinate is from.
        Args:
            coord_index:

        Returns:

        """

        return self.all_features[self.feature_indices[coord_index]]

    def get_adjacency_matrix(self, return_voronoi=False) -> Dict[int, List[int]]:
        """
        Returns a dictionary of indices. They keys are the indices of feature_geoms. The values are the indices of any
        target geometries which are adjacent to the feature_geoms.

        Params:
            return_voronoi: If True, return the adjacency_dict followed by the Voronoi diagram object from scipy. Useful
            for plotting out the diagram to better understand why two features are or aren't considered adjacent.

        Returns:
            dict A dictionary of indices. The keys are the indices of feature_geoms. The values are the indices of any
        """

        if self._adjacency_matrix is None:

            # Get the voronoi diagram of all vertices of all features
            vor = Voronoi(np.array(self.all_coordinates))

            if return_voronoi:
                fig = voronoi_plot_2d(vor, show_vertices=False, line_colors='orange',
                                      line_width=2, line_alpha=0.6, point_size=2)
                plt.title("Voronoi diagram of all input feature vertices.")
                plt.xlabel("Longitude")
                plt.ylabel("Latitude")
                plt.show()

            # We don't need to tag obstacles with their voronoi vertices
            obstacle_coord_len = sum(len(feat.coords) for feat in self.obstacle_features)

            # Tag each feature with the vertices of the voronoi region it belongs to
            for coord_index in range(len(self.all_coordinates) - obstacle_coord_len):
                feature = self.get_feature_from_coord_index(coord_index)
                for vor_vertex_index in vor.regions[vor.point_region[coord_index]]:
                    if vor_vertex_index != -1:
                        feature.voronoi_points.add(vor_vertex_index)

            # If any two features have any voronoi indices in common, then their voronoi regions must intersect,
            # therefore the input features are adjacent.
            self._adjacency_matrix = defaultdict(list)

            for coord_index, source_feature in enumerate(self.source_features):
                for vor_region_index, target_feature in enumerate(self.target_features):
                    if len(source_feature.voronoi_points & target_feature.voronoi_points) > 1:
                        self._adjacency_matrix[coord_index].append(vor_region_index)

        return self._adjacency_matrix

    def plot_adjacency_matrix(self):
        for source_i, target_is in self.get_adjacency_matrix().items():
            source_poly = self.source_features[source_i].geometry
            target_polys = [self.target_features[target_i].geometry for target_i in target_is]

            plt.plot(*source_poly.exterior.xy, color="grey")

            # Plot the linestrings between the source and target polygons
            for target_poly in target_polys:
                linestring = LineString([nearest_points(source_poly, target_poly)[1], source_poly.centroid])
                plt.plot(*linestring.xy, color="green")

        for target_poly in self.target_features:
            plt.plot(*target_poly.geometry.exterior.xy, color="blue")

        # Plot the rest of the source features
        for i, source_poly in enumerate(self.source_features):
            if i not in self.get_adjacency_matrix().keys():
                plt.plot(*source_poly.geometry.exterior.xy, color="grey")

        for obstacle_poly in self.obstacle_features:
            if isinstance(obstacle_poly.geometry, LineString):
                plt.plot(*obstacle_poly.geometry.coords.xy, color="red")

        plt.title("Adjacency linkages between source and target")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()

    # ToDo: Support geodataframes


def load_test_geoms(test_data_dir) -> Tuple[List[BaseGeometry], List[BaseGeometry], List[BaseGeometry]]:
    """
    Load some test data
    """

    with open(os.path.join(test_data_dir, "source.csv")) as f:
        source_geoms = [loads(line) for line in f.readlines()]

    with open(os.path.join(test_data_dir, "target.csv")) as f:
        target_geoms = [loads(line) for line in f.readlines()]

    with open(os.path.join(test_data_dir, "obstacle.csv")) as f:
        obstacle_geoms = [loads(line) for line in f.readlines()]

    return source_geoms, target_geoms, obstacle_geoms


if __name__ == "__main__":
    s, t, o = load_test_geoms("../tests/sample_data")
    engine = AdjacencyEngine(s , t, o, True)
    start = time.time()
    print(engine.get_adjacency_matrix())
    print("elapsed time: ", time.time() - start)


    engine.plot_adjacency_matrix()



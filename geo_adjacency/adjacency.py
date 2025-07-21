"""
The `adjacency` module implements the AdjacencyEngine class,
which allows us to calculate adjacency relationships. Adjacency relationships are between a set of source geometries,
or between source geometries and a second set of target geometries. Obstacle geometries can be passed in to
stand between sources or sources and targets, but they are not included in the output.

For example, if we wanted to know what trees in a forest are adjacent to the shore of a lake, we could
pass in a set of Point geometries to the trees, a Polygon to represent the lake, and a LineString to represent
a road passing between some of the trees and the shore.

`AdjacencyEngine` utilizes a Voronoi diagram of all the vertices in all the geometries combined to determine
which geometries are adjacent to each other. The methodology is described in detail in the project documentation.
"""

import logging
from typing import Dict, Generator, List, Tuple, Union
from collections import defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.spatial import Voronoi
from shapely import LineString, MultiPoint, Point, Polygon, box
from shapely import ops as shapely_ops
from shapely.geometry.base import BaseGeometry

from geo_adjacency.exception import ImmutablePropertyError
from geo_adjacency.logging_config import setup_logger
from geo_adjacency.utils import count_unique_coords, add_geometry_to_plot

# Create a custom logger using the centralized logging configuration
log: logging.Logger = setup_logger(__name__)


class AdjacencyEngine:
    """
    A class for calculating the adjacency of a set of geometries to another geometry or set
    of geometries, given a set of obstacles. Optionally supports distance constraints and 
    bounding box filtering.

    First, the Voronoi diagram is generated for all geometry vertices including obstacles. 
    Then, we check which Voronoi regions share vertices. If they share enough vertices 
    (configurable threshold), then the underlying geometries are considered adjacent.
    """

    __slots__ = (
        "_source_gdf",
        "_target_gdf",
        "_obstacle_gdf",
        "_adjacency_dict",
        "_vor",
        "_all_features_gdf",
        "_max_distance",
        "_bounding_rectangle",
        "_min_overlapping_voronoi_vertices",
        "_coord_to_feature_cache",
        "_geometry_voronoi_vertices",
    )

    def __init__(
        self,
        source_geoms: Union[List[BaseGeometry], gpd.GeoDataFrame],
        target_geoms: Union[List[BaseGeometry], gpd.GeoDataFrame, None] = None,
        obstacle_geoms: Union[List[BaseGeometry], gpd.GeoDataFrame, None] = None,
        **kwargs,
    ):
        """
        Note: only Multipolygons, Polygons, LineStrings and Points are supported. It is assumed all
        features are in the same projection.

        Args:
            source_geoms (Union[List[BaseGeometry], gpd.GeoDataFrame]): List of Shapely geometries
                or a GeoPandas GeoDataFrame. We will determine which ones are adjacent to which others,
                unless target_geoms is specified. If a list is provided, it will be converted to a
                GeoDataFrame internally for vectorized operations.
            target_geoms (Union[List[BaseGeometry], gpd.GeoDataFrame, None], optional): List of
                Shapely geometries or a GeoPandas GeoDataFrame. If not None, we will test if these
                features are adjacent to the source features. If a list is provided, it will be
                converted to a GeoDataFrame internally.
            obstacle_geoms (Union[List[BaseGeometry], gpd.GeoDataFrame, None], optional): List
                of Shapely geometries or a GeoPandas GeoDataFrame. These features will not be tested
                for adjacency, but they can prevent a source and target feature from being adjacent.
                If a list is provided, it will be converted to a GeoDataFrame internally.

        Keyword Args:
            densify_features (bool, optional):  If True, we will add additional points to the
              features to improve accuracy of the voronoi diagram. If densify_features is True and
              max_segment_length is false, then the max_segment_length will be calculated based on
              the average segment length of all features, divided by 5.
            max_segment_length (Union[float, None], optional): The maximum distance between vertices
              that we want in projection units. densify_features must be True, or an error will be thrown.
            max_distance (Union[float, None], optional): The maximum distance between two features
              for them to be candidates for adjacency. Units are same as geometry coordinate system.
            bounding_box (Union[float, float, float, float, None], optional): Set a bounding box
              for the analysis. Only include features that intersect the box in the output.
              This is useful for removing data from the edges from the final analysis, as these
              are often not accurate. This is particularly helpful when analyzing a large data set
              in a windowed fashion. Expected format is (minx, miny, maxx, maxy).
            min_overlapping_voronoi_vertices (int, optional): Minimum number of Voronoi vertices
              that must be shared between features to be considered adjacent. Default 2.

        """

        densify_features = kwargs.get("densify_features", False)
        max_segment_length = kwargs.get("max_segment_length", None)
        self._max_distance = kwargs.get("max_distance", None)
        self._min_overlapping_voronoi_vertices = kwargs.get(
            "min_overlapping_voronoi_vertices", 2
        )
        if kwargs.get("bounding_box", None):
            minx, miny, maxx, maxy = kwargs.get("bounding_box")
            assert (
                minx < maxx and miny < maxy
            ), "Bounding box must have minx < maxx and miny < maxy"
            self._bounding_rectangle: Polygon = box(minx, miny, maxx, maxy)
        else:
            self._bounding_rectangle = None

        if max_segment_length and not densify_features:
            raise ValueError(
                "densify_features must be True if max_segment_length is not None"
            )

        # Convert inputs to GeoDataFrames for vectorized operations
        self._source_gdf = self._to_geodataframe(source_geoms)
        self._target_gdf = (
            self._to_geodataframe(target_geoms) if target_geoms is not None else None
        )
        self._obstacle_gdf = (
            self._to_geodataframe(obstacle_geoms)
            if obstacle_geoms is not None
            else None
        )

        self._adjacency_dict: Union[Dict[int, List[int]], None] = None
        self._vor = None
        self._all_features_gdf = None
        self._geometry_voronoi_vertices = None
        self._coord_to_feature_cache: Union[Dict[int, Tuple[str, int]], None] = None

        if densify_features:
            if max_segment_length is None:
                max_segment_length = self._calc_segmentation_dist()
                log.info("Calculated max_segment_length of %s" % max_segment_length)

            # Apply segmentation to all GeoDataFrames
            for gdf in [self.source_gdf, self.target_gdf, self.obstacle_gdf]:
                if gdf is not None:
                    # Apply segmentation to non-point geometries
                    mask = ~gdf.geometry.apply(
                        lambda geom: isinstance(geom, (Point, MultiPoint))
                    )
                    if mask.any():
                        gdf.loc[mask, "geometry"] = gdf.loc[mask, "geometry"].apply(
                            lambda geom: geom.segmentize(max_segment_length)
                        )
            # Reset all features cache
            self._all_features_gdf = None

    def _to_geodataframe(
        self, geoms_input: Union[List[BaseGeometry], gpd.GeoDataFrame]
    ) -> gpd.GeoDataFrame:
        """
        Convert input geometries to a GeoDataFrame for vectorized operations.

        Args:
            geoms_input: Either a list of geometries or an existing GeoDataFrame

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame with geometries and optional attributes
        """
        return (
            geoms_input
            if isinstance(geoms_input, gpd.GeoDataFrame)
            else gpd.GeoDataFrame(geometry=geoms_input)
        )

    @property
    def source_gdf(self) -> gpd.GeoDataFrame:
        """Access the source geometries as a GeoDataFrame."""
        return self._source_gdf

    @property
    def target_gdf(self) -> Union[gpd.GeoDataFrame, None]:
        """Access the target geometries as a GeoDataFrame."""
        return self._target_gdf

    @property
    def obstacle_gdf(self) -> Union[gpd.GeoDataFrame, None]:
        """Access the obstacle geometries as a GeoDataFrame."""
        return self._obstacle_gdf

    @property
    def all_features_gdf(self) -> gpd.GeoDataFrame:
        """
        All source, target, and obstacle features concatenated into a single GeoDataFrame.
        The order is preserved: source, then target, then obstacles.

        Returns:
            gpd.GeoDataFrame: Combined GeoDataFrame with all geometries and a 'feature_type' column.
        """

        if self._all_features_gdf is None:
            # Concatenate all GeoDataFrames while preserving order
            gdfs_to_concat = []

            if self.source_gdf is not None and len(self.source_gdf) > 0:
                source_copy = self.source_gdf.copy()
                source_copy["feature_type"] = "source"
                source_copy["original_index"] = range(len(source_copy))
                gdfs_to_concat.append(source_copy)

            if self.target_gdf is not None and len(self.target_gdf) > 0:
                target_copy = self.target_gdf.copy()
                target_copy["feature_type"] = "target"
                target_copy["original_index"] = range(len(target_copy))
                gdfs_to_concat.append(target_copy)

            if self.obstacle_gdf is not None and len(self.obstacle_gdf) > 0:
                obstacle_copy = self.obstacle_gdf.copy()
                obstacle_copy["feature_type"] = "obstacle"
                obstacle_copy["original_index"] = range(len(obstacle_copy))
                gdfs_to_concat.append(obstacle_copy)

            if gdfs_to_concat:
                self._all_features_gdf = pd.concat(gdfs_to_concat, ignore_index=True)
            else:
                self._all_features_gdf = gpd.GeoDataFrame()

        return self._all_features_gdf

    @all_features_gdf.setter
    def all_features_gdf(self, value):
        raise ImmutablePropertyError("Property all_features is immutable.")

    def _calc_segmentation_dist(self, divisor=5):
        """
        Try to create a well-fitting maximum length for all line segments in all features. Take
        the average distance between all coordinate pairs and divide by 5. This means that the
        average segment will be divided into five segments.

        This won't work as well if the different geometry sets have significantly different
        average segment lengths. In that case, it is advisable to prepare the data appropriately
        beforehand.

        Args:
            divisor (int, optional): Divide the average segment length by this number to get the new desired
        segment length.

        Returns:
            float: Average segment length divided by divisor.
        """

        return float(
            sum(self.all_features_gdf.geometry.length)
            / self.all_features_gdf.apply(
                lambda row: count_unique_coords(row.geometry), axis=1
            ).sum()
            / divisor
        )

    def get_geometry_from_coord_index(self, coord_index: int) -> Tuple[str, int]:
        """
        Map a coordinate index back to its source geometry.

        Given a coordinate index from the flattened coordinate list used for Voronoi 
        analysis, determine which geometry the coordinate belongs to.

        Args:
            coord_index (int): The index of the coordinate in the flattened coordinate list.

        Returns:
            Tuple[str, int]: A tuple of (feature_type, geometry_index) where:
                - feature_type is 'source', 'target', or 'obstacle'
                - geometry_index is the index within that feature type's GeoDataFrame

        Raises:
            KeyError: If the coordinate index is not found in the cache.
        """
        if self._coord_to_feature_cache is None:
            all_features_gdf = self.all_features_gdf

            if len(all_features_gdf) == 0:
                self._coord_to_feature_cache = {}
            else:
                # Build coordinate counts by actually extracting coordinates (matches Voronoi exactly)
                all_coords = all_features_gdf.geometry.get_coordinates()
                coord_counts = all_coords.groupby(all_coords.index).size().tolist()

                                # Build the cache using fully vectorized operations
                # Create arrays for all coordinate indices and their corresponding geometry info
                coord_indices = np.arange(len(all_coords))
                geom_indices = all_coords.index.values
                
                # Extract feature info as arrays for vectorized lookup
                feature_types = all_features_gdf["feature_type"].values[geom_indices]
                original_indices = all_features_gdf["original_index"].values[geom_indices]
                
                # Build cache with dictionary comprehension, ensuring Python int types
                self._coord_to_feature_cache = {
                    int(coord_idx): (feature_type, int(orig_idx))
                    for coord_idx, feature_type, orig_idx in zip(
                        coord_indices, feature_types, original_indices
                    )
                }

        return self._coord_to_feature_cache[coord_index]

    @property
    def vor(self) -> Voronoi:
        """
        The Voronoi diagram used for adjacency analysis.
        
        Lazily computed Voronoi diagram from all geometry coordinates. This property
        provides access to the underlying Scipy Voronoi object, which is useful 
        for debugging, visualization, or advanced analysis.

        Returns:
            scipy.spatial.Voronoi: The Voronoi diagram object containing regions, 
                                 vertices, and other spatial relationships.
        """
        if not self._vor:
            self._vor = Voronoi(self.all_features_gdf.geometry.get_coordinates().values)
        return self._vor

    @vor.setter
    def vor(self, _):
        raise ImmutablePropertyError("Property vor is immutable.")

    def _get_voronoi_vertex_idx_for_coord_idx(
        self, feature_coord_index: int
    ) -> Generator[int, None, None]:
        """
        For a given feature coordinate index, return the indices of the voronoi vertices. Ignore
        any "-1"s, which indicate vertices at infinity; these provide no adjacency information.

        Args:
            feature_coord_index (int): The index of the coordinate in self.all_coordinates

        Returns:
            Generator[int, None, None]: A generator of the indices of the voronoi vertices.
        """
        return (
            i
            for i in self.vor.regions[self.vor.point_region[feature_coord_index]]
            if i != -1
        )

    def _tag_geometries_with_voronoi_vertices(self):
        """
        Create mapping of geometries to their Voronoi vertices. Runs the voronoi analysis
        if it has not been done already.

        Returns:
            None
        """
        # Initialize geometry-to-voronoi mapping
        self._geometry_voronoi_vertices = {}

        # Iterate through ALL coordinates (since Voronoi is built from all coordinates)
        # but only map non-obstacle geometries
        total_coord_count = len(self.all_features_gdf.geometry.get_coordinates())
        for feature_coord_index in range(total_coord_count):
            dataframe_type, geometry_idx = self.get_geometry_from_coord_index(
                feature_coord_index
            )

            # Only process non-obstacle geometries for adjacency mapping
            if dataframe_type != "obstacle":
                # Create key for this geometry
                geom_key = (dataframe_type, geometry_idx)
                if geom_key not in self._geometry_voronoi_vertices:
                    self._geometry_voronoi_vertices[geom_key] = set()

                # Add Voronoi vertices for this coordinate
                for i in self._get_voronoi_vertex_idx_for_coord_idx(
                    feature_coord_index
                ):
                    self._geometry_voronoi_vertices[geom_key].add(i)

    def _determine_adjacency(
        self,
        source_gdf: gpd.GeoDataFrame,
        target_gdf: gpd.GeoDataFrame,
        source_type: str = "source",
        target_type: str = "target",
    ):
        """
        Determines the adjacency relationship between two GeoDataFrames using vectorized operations.
        Stores the result in self._adjacency_dict.

        Args:
            source_gdf (gpd.GeoDataFrame): The source GeoDataFrame.
            target_gdf (gpd.GeoDataFrame): The target GeoDataFrame.
            source_type (str): Type identifier for source ('source', 'target', etc.)
            target_type (str): Type identifier for target ('source', 'target', etc.')

        Returns:
            None
        """
        # Early return if either GeoDataFrame is empty
        if len(source_gdf) == 0 or len(target_gdf) == 0:
            return

        # Apply bounding rectangle filter to both source and target at once
        if self._bounding_rectangle is not None:
            source_mask = source_gdf.geometry.intersects(self._bounding_rectangle)
            target_mask = target_gdf.geometry.intersects(self._bounding_rectangle)
            
            valid_source_indices = source_gdf.index[source_mask].tolist()
            valid_target_indices = target_gdf.index[target_mask].tolist()
            
            # Early return if no valid geometries
            if not valid_source_indices or not valid_target_indices:
                return
        else:
            valid_source_indices = list(range(len(source_gdf)))
            valid_target_indices = list(range(len(target_gdf)))

        # Generate candidate pairs efficiently
        if self._max_distance is not None:
            # Spatial join for distance-constrained adjacency
            src_buffered = source_gdf.iloc[valid_source_indices].copy()
            src_buffered.geometry = src_buffered.geometry.buffer(self._max_distance)
            src_buffered["src_idx"] = valid_source_indices
            
            tgt_indexed = target_gdf.iloc[valid_target_indices].assign(tgt_idx=valid_target_indices)
            
            pairs = gpd.sjoin(src_buffered, tgt_indexed, predicate="intersects")
            if len(pairs) == 0:
                return
            
            source_indices, target_indices = pairs["src_idx"].values, pairs["tgt_idx"].values
        else:
            # All-pairs approach using numpy broadcasting
            source_indices, target_indices = np.meshgrid(valid_source_indices, valid_target_indices, indexing="ij")
            source_indices, target_indices = source_indices.ravel(), target_indices.ravel()

        # Filter out same-geometry pairs for source-to-source adjacency
        if source_gdf is target_gdf:
            mask = source_indices != target_indices
            source_indices = source_indices[mask]
            target_indices = target_indices[mask]

        # Voronoi adjacency check
        for source_idx, target_idx in zip(source_indices, target_indices):
            source_key = (source_type, int(source_idx))
            target_key = (target_type, int(target_idx))

            # Check if both geometries have Voronoi vertices
            if (source_key in self._geometry_voronoi_vertices and 
                target_key in self._geometry_voronoi_vertices):
                
                source_voronoi = self._geometry_voronoi_vertices[source_key]
                target_voronoi = self._geometry_voronoi_vertices[target_key]

                # Check if they share enough Voronoi vertices
                shared_vertices = len(source_voronoi.intersection(target_voronoi))
                if shared_vertices >= self._min_overlapping_voronoi_vertices:
                    self._adjacency_dict[int(source_idx)].append(int(target_idx))

    def get_adjacency_dict(self) -> Dict[int, List[int]]:
        """
        Returns a dictionary of adjacency relationships by index.

        The keys are the indices of source geometries. The values are lists of indices 
        of target geometries that are adjacent to each source geometry.

        If no targets were specified, then calculate adjacency between source features and other
        source features.

        Returns:
            Dict[int, List[int]]: A dictionary mapping source geometry indices to lists of 
                                adjacent target geometry indices.
        """

        """Note: We want adjacent features to have at least two overlapping vertices, otherwise we 
        might call the features adjacent when their Voronoi regions don't share any edges."""

        if self._adjacency_dict is None:
            self._tag_geometries_with_voronoi_vertices()

            # If any two geometries have shared voronoi vertices, then their voronoi regions
            # intersect, therefore the input geometries are adjacent.
            self._adjacency_dict = defaultdict(list)

            # Get adjacency between source and target features
            if self.target_gdf is not None and len(self.target_gdf) > 0:
                self._determine_adjacency(
                    self.source_gdf, self.target_gdf, "source", "target"
                )
            # If no target specified, get adjacency between source and other source features.
            else:
                self._determine_adjacency(
                    self.source_gdf, self.source_gdf, "source", "source"
                )

        # Convert numpy integers to regular Python integers to match return type annotation
        return {
            int(k): [int(v) for v in values]
            for k, values in self._adjacency_dict.items()
        }

    def get_adjacency_gdf(self) -> Union[gpd.GeoDataFrame, None]:
        """
        Returns adjacency relationships as a GeoDataFrame with source and target geometries and attributes.

        Returns:
            gpd.GeoDataFrame or None: DataFrame with adjacency relationships including geometries and
                                     any attributes from the original source/target GeoDataFrames.
                                     Returns None if no adjacencies found.
        """
        adjacency_dict = self.get_adjacency_dict()

        if not adjacency_dict or all(
            len(targets) == 0 for targets in adjacency_dict.values()
        ):
            return None

        # Prepare data for GeoDataFrame
        rows = []

        # Determine target set (targets if available, otherwise sources for source-source adjacency)
        target_gdf = (
            self.target_gdf if self.target_gdf is not None else self.source_gdf
        )

        for source_idx, target_list in adjacency_dict.items():
            for target_idx in target_list:
                source_geom = self.source_gdf.iloc[source_idx].geometry
                target_geom = target_gdf.iloc[target_idx].geometry

                row_data = {
                    "source_idx": source_idx,
                    "target_idx": target_idx,
                    "source_geometry": source_geom,
                    "target_geometry": target_geom,
                    "geometry": source_geom,  # Primary geometry column
                }

                # Add source attributes
                if len(self.source_gdf.columns) > 1:
                    source_row = self.source_gdf.iloc[source_idx]
                    for col in source_row.index:
                        if col != "geometry":
                            row_data[f"source_{col}"] = source_row[col]

                # Add target attributes
                if len(target_gdf.columns) > 1:
                    target_row = target_gdf.iloc[target_idx]
                    for col in target_row.index:
                        if col != "geometry":
                            row_data[f"target_{col}"] = target_row[col]

                rows.append(row_data)

        if not rows:
            return None

        return gpd.GeoDataFrame(rows)

    def plot_adjacency_dict(self) -> None:
        """
        Plot the adjacency linkages between source and target geometries using matplotlib.
        
        Runs the adjacency analysis if it has not already been run. Shows source geometries 
        in grey, target geometries in blue, obstacles in red, and adjacency links in green.

        Returns:
            None
        """
        # Plot the adjacency linkages between the source and target
        if self.target_gdf is not None and len(self.target_gdf) > 0:
            for source_i, target_is in self.get_adjacency_dict().items():
                source_poly = self.source_gdf.iloc[source_i].geometry
                target_polys = [
                    self.target_gdf.iloc[target_i].geometry for target_i in target_is
                ]

                # Plot the linestrings between the source and target polygons
                links = []
                for target_poly in target_polys:
                    if target_poly:
                        try:
                            links.append(
                                LineString(
                                    shapely_ops.nearest_points(target_poly, source_poly)
                                )
                            )
                        except ValueError:
                            log.error(
                                f"Error creating link between '{target_poly}' and '{source_poly}'"
                            )
                add_geometry_to_plot(links, "green")
        # If no target specified, get adjacency between source and other source features.
        else:
            for source_i, source_2_is in self.get_adjacency_dict().items():
                source_poly = self.source_gdf.iloc[source_i].geometry
                target_polys = [
                    self.source_gdf.iloc[source_2_i].geometry
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

        # Plot all geometries
        target_geoms = (
            list(self.target_gdf.geometry) if self.target_gdf is not None else []
        )
        source_geoms = list(self.source_gdf.geometry)
        obstacle_geoms = (
            list(self.obstacle_gdf.geometry) if self.obstacle_gdf is not None else []
        )

        add_geometry_to_plot(target_geoms, "blue")
        add_geometry_to_plot(source_geoms, "grey")
        add_geometry_to_plot(obstacle_geoms, "red")

        plt.title("Adjacency linkages between source and target")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()

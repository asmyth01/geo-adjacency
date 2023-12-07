"""
A series of example analyses.
"""

from matplotlib import pyplot as plt
from scipy.spatial import voronoi_plot_2d
from shapely.wkt import loads

from geo_adjacency.adjacency import AdjacencyEngine
import os.path
import json
from shapely.geometry import shape


##############
# Data setup #
##############

def load_geojson(path):
    with open(path) as f:
        return [shape(feature["geometry"]) for feature in json.load(f)["features"]]

# Load the example data
data_dir = os.path.join(os.path.dirname(__file__), 'data')
source_path = os.path.join(data_dir, 'Buildings.geojson')
target_path = os.path.join(data_dir, 'Parks.geojson')
obstacle_path = os.path.join(data_dir, 'Roads.geojson')

source_geoms = load_geojson(source_path)
target_geoms = load_geojson(target_path)
obstacle_geoms = load_geojson(obstacle_path)

#################
# Basic Example #
#################

# Find buildings that are adjacent to parks, except where a road interferes.
engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms)
print(engine.get_adjacency_dict())

# Plot the voronoi diagram used in the analysis
voronoi_plot_2d(engine.vor)
plt.show()

# Plot the adjacency graph
engine.plot_adjacency_dict()

########################
# Max Distance example #
########################
engine = AdjacencyEngine(source_geoms, target_geoms, **{"max_distance": 0.001})
engine.plot_adjacency_dict()


########################
# Bounding box example #
########################
engine = AdjacencyEngine(source_geoms, **{"bounding_box": (-122.33872, 47.645, -122.33391, 47.65)})
engine.plot_adjacency_dict()


##########################
# Segmentization example #
##########################

source_geoms = [loads("POLYGON ((0 0, 0 10, 1 10, 1 5, 1 0, 0 0))")]
# A 10x1 wkt 5 units away from the source
target_geoms = [loads("POLYGON ((5 0, 5 10, 6 10, 6 5, 6 0, 5 0))")]
# A 10x1 wkt 2 units away from the source
obstacle_geoms = [loads("POLYGON ((2 0, 2 10, 3 10, 3 0, 2 0))")]

engine = AdjacencyEngine(source_geoms, target_geoms, obstacle_geoms, densify_features=True)
engine.plot_adjacency_dict()



if __name__ == '__main__':
    pass
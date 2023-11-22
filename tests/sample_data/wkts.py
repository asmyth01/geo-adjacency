from shapely import LineString, Polygon, MultiPolygon, Point
from shapely.wkt import loads
import matplotlib.pyplot as plt


# A list of rectangular polygon WKTs with a small space between each. Order is clockwise




source_wkts = [
    "POINT(10 1)",
    "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)), ((3 0, 3 1, 5 1, 5 0, 3 0)))",
    "POLYGON((6 0, 6 1, 7 1, 7 0, 6 0))",
    "POLYGON((15 0, 15 1, 18 1, 18 0, 15 0))",
    "POLYGON((20 0, 20 1, 22 1, 22 0, 20 0))",
    "POLYGON((24 0, 24 1, 26 1, 26 0, 24 0))",
    "LINESTRING(27 1, 30 1)",
]

# A linestring that will serve as an obstacle.
obstacle_wkts = [
    "LINESTRING(0 1.5, 1 1.5, 1 1.5, 1.5 1.5)",
    "POLYGON(( 20 1.25, 20 1.75, 22 1.75, 22 1.25, 20 1.25))",
    "MULTIPOLYGON(((23 1.25, 23 1.75, 25 1.75, 25 1.25, 23 1.25)), ((26 1.25, 26 1.75, 28 1.75, 28 1.25, 26 1.25)))",
]

# Target polygons
target_wkts = [
    "POLYGON((0 2, 0 3, 5 3, 5 2, 0 2))",
    "POLYGON((6 2, 6 3, 8 3, 8 2, 6 2))",
    "POINT(9 2)",
    "POINT(12 2)",
    "POLYGON((15 2, 15 3, 17 3, 17 2, 15 2))",
    "POLYGON((18 2, 18 3, 20 3, 20 2, 18 2))",
    "LINESTRING(21 2, 26 2)",
    "MULTIPOLYGON(((27 2, 27 3, 29 3, 29 2, 27 2)), ((30 2, 30 3, 32 3, 32 2, 30 2)))"
]

source_geoms = [loads(wkt) for wkt in source_wkts]
target_geoms = [loads(wkt) for wkt in target_wkts]
obstacle_geoms = [loads(wkt) for wkt in obstacle_wkts]

# # Visualize the test data with pyplot
# add_geometry_to_plot(source_geoms, color="green")
# add_geometry_to_plot(target_geoms, color="blue")
# add_geometry_to_plot(obstacle_geoms, color="red")
#
# plt.title("Test data")
# plt.xlabel("Longitude")
# plt.ylabel("Latitude")
# plt.show()

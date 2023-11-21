from typing import Tuple, List

from shapely import Geometry
from shapely.wkt import loads
import os


def load_test_geoms(test_data_dir) -> Tuple[List[Geometry], List[Geometry], List[Geometry]]:
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
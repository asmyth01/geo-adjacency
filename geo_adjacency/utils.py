import numpy as np


def flatten_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

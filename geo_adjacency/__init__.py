"""
Geo-adjacency: Spatial adjacency analysis using Voronoi diagrams.

This package provides tools for determining adjacency relationships between 
geometric features, even when they don't directly touch. It uses Voronoi 
diagram analysis to identify spatial relationships that account for gaps 
and obstacles between features.

Main class:
    AdjacencyEngine: The primary class for performing adjacency analysis.

Example:
    >>> from geo_adjacency.adjacency import AdjacencyEngine
    >>> from shapely.geometry import Point
    >>> sources = [Point(0, 0), Point(1, 0)]
    >>> targets = [Point(0, 1), Point(1, 1)]
    >>> engine = AdjacencyEngine(sources, targets)
    >>> adjacencies = engine.get_adjacency_dict()
"""

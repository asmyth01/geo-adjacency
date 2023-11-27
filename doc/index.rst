.. geo-adjacency documentation master file, created by
   sphinx-quickstart on Wed Nov 22 10:11:07 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Geo-Adjacency Documentation
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Install
   Quickstart
   Methodology
   modules

These are the docs for geo-adjacency. This module determines adjacency relationships between
geometries that may have gaps between them. We use Voronoi diagram analysis to essentially close
these gaps. The analysis is lightning fast thanks to Qhull, a C library with advanced geospatial
capabilities.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

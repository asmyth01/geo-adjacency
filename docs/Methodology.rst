geo-adjacency Methodolgy
========================

This package aims to answer a seemingly simply question: is one thing next to another thing?

Unlike many geospatial problems, this one is surprisingly tricky. A check for intersection between
two geometries is pretty straightforard to implement. It's also quite easy to define. Adjacency is
much harder to define, rendering it a more challenging problem to solve algorithmically.

At the same time, questions of adjacency are often essential. There is a very large difference
between having a playground which is immediately adjacent to an active railway line, and one which
is merely nearby.

When it comes to spatial analysis, you can sometimes get away with an intersection to answer a
question of adjacency. But that only works with perfect data, where all features are perfectly
tiled across the plane, with no gaps in between.

.. note::
   This definition somewhat differs from another geometric concept of dajacency, in which adjacent
   geometries must be either touching, or share a corner. See this article for more: https://www.e-education.psu.edu/geog586/taxonomy/term/264

A adjacency analysis must take gaps between features into account. Simplistically, this could be
accomplished with ray-casting: you could send a ray out from every source towards every target,
and get if the ray intersects with any obstacles in between. But this doesn't always make sense.
Take the example below:

   .. image:: images/AdjacencyRaycast.png

A ray cast from geometry A will reach Geometry B some of the time, but clearly they are not adjacent,
because geometry C interferes.

We could tweak the scenario slightly, and give the two geoemtries a full line of sight. In other words,
A ray cast from any point to any other point would have a clear path.

   .. image:: images/AdjacencyRaycast2.png

But are these two geometries realy adjacent? Maybe. This is the grey area that makes any algorithmic
answer difficult.

Voronoi Diagrams to the Rescue
==============================

What we really need is a way to erase the gaps between the geometries. If we could only slowly expand
each geometry, as though inflating a series of balloons in a box, eventually they would touch, and
we could do a simply intersection. That would solve our adjacency problem in a deterministic,
objective way. Luckily, we have a way to do just that.

A voronoi diagram is defined like this, according to the `QHull <http://www.qhull.org/html/qvoronoi.htm>`_  library (which geo-adjacency relies
upon, incidentally).

  The Voronoi diagram is the nearest-neighbor map for a set of points. Each region contains those points that are nearer one input site than any other input site. It has many useful properties and applications

Another way of thinking of it, though, is a voronoi diagram fills in the spaces between points. In a
way, these regions are the "areas of influence" surrounding their input points. By looking at the
intersection of these regions, adjacency becomes a much more intuitive and solvable concept.

In this package, `scipy.spatial.Voronoi <https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html>`_ provides an interface to QHull, a C library which can
calculate the diagram very quickly.

Segementization
===============

There's a further problem, though: the Voronoi algorithm only works on points. What if our inputs
are polygons? How do we get a Voronoi diagram of a polygon?

Step one is obvious enough: Take the Voronoi diagram of all the vertices of each polygon, and union
the resulting regions. But what if our input polygon isn't very detailed. A long rectangle, for example.
The voronoi diagram would be based on only 4 points. What if there is an obstacle region somewhere
near the center of the rectangle's long side? The voronoi diagram would not account for this.

The solution is to add additional vertices to the input polygons until they are dense enough to produce
and accurate diagram.

Getting the right number of vertices takes a little bit of trial and error. If `densify_features` is
True, then the AdjacencyEngine will attempt to calculate a reasonable level of segemtization, as
Shapely calls is. This is based on the average segement length of all input features. This is sometimes
not enough, though, and it's adviseable to do some experimentation to find a level that generates an
accurate result, without compromising performance too much; every additional vertex makes the Voronoi
calculation a little more intensive.
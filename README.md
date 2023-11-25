# geo-adjacency
https://pypi.org/project/geo-adjacency/


# Installation

## pip
Recommended installation is with pip:
`python -m pip install geo-adjacency`

## Build from source
You must have Python "<3.13,>=3.9" installed.
```clone [URL]
cd [dir]
poetry install
```

# Usage

# How It Works
It's easy to determine if two geometries intersect one another. It's more ambiguous to classify them as adjacent.

Adjacency is one of those intuitive concepts: you know it when you see it, but you can't quite pin down why.

Adjacency is a critical question is spatial analysis, and in the real world. After all, it makes a big difference 
whether you are merely near a landfill, or if it is in your backyard.

What it boils down to is dealing with physical gaps between geometries. We need to decide if these two geometries
can "see" each other, without anything else getting in the way. But it's more complicated than that, even. What if two
geometries can partly "see" each other? What if they are 99% blocked from one another? Clearly line of sight alone 
isn't going to cut it with real-world applications. 

This module aims to zero in on a concept of adjacency which is intuitive and applicable to the real world, yet also rigorous
and deterministic.

## The Method
We use the concept of a Voronoi diagram to determine adjacency. A voronoi diagram creates regions in 2D space around a set
of points. Every point within each region must be closer to the source point than to any other point in the set. Another
way of thinking of it is, each voronoi region is the "sphere of influence" around each point in the set.

In this module, we define two geometries to be adjacent if the union of all the voronoi regions for each of the vertices in the geometry
intersects with the voronoi regions of any other input feature.

There's one catch: Voronoi diagrams are generated from a set of points, not polygons or linestrings. Therefore we break down
each geometry into its component vertices and generate a voronoi diagram from these. Then, combine the voronoi regions
for each input geometry.

In reality, we don't even have to union these geometries. Scipy.spatial.voronoi generates a set of vertices. Each input point 
is assigned the indices of the voronoi vertices that correspond to its voronoi region. It is enough to know whether any to
input points share any two voronoi vertices to know that their voronoi regions must intersect. Since we don't need to calculate
any unions or intersections, the adjacency calculation is very fast, limited principly by scipy.spatial.voronoi, which is
based on the very fast C library QHull.

often, though, an input geometry does not have enough vertices to create a combined voronoi diagram that can accurately be
used for adjacency. You can imagine using a long, straight road as an obstacle. It may have no vertices for several hundred feet.
Any source and target features along that stretch probably will have intersecting voronoi shapes, giving a false adjacency positive.
We can correct for this by "densifying" the input geometries. That is, we can use Shapely.segmentize to add vertices at
regular intervals along any linestring or polygon geometries. This creates a denser voronoi diagram. It will increase
processing time somewhat, but can lead to near-perfect accuracy when used appropriately.

In some cases, it may be more appropriate to pre-process the data to add more points as needed.


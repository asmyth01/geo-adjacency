Quickstart
==========

This guide will get you up and running with adjacency analysis quickly.

#. Load the data. geo-adjacency expects you to provide your data as Shapely geometries. You will provide three lists: source_geoemtries, target_geometries, and obstacle_geometries. What we are analyzing is which of the source geometries are adjacent to which of the target geometries. Obstacles can prevent a source and target from being adjacent, but they do not participate in the adjacency dictionary.
#. Create an AdjacencyEngine. In this case, we'll load the sample data which is available on `Github <https://github.com/asmyth01/geo-adjacency/>`_.

   ..code-block:: python

      s, t, o = load_test_geoms("../tests/sample_data")
      engine = AdjacencyEngine(s , t, o, True)
#. Run the analysis

   .. code-block:: python
   
      output = engine.get_adjacency_dict()
      # defaultdict(<class 'list'>, {0: [1, 2], 1: [1], 2: [1], 3: [2], 6: [1], 7: [1]})

    The output is a dictionary. Keys are the indices of source geometries in the input list, and values are a list of indices of adjacent target geometries in the input list.

#. You can visualize the output with a handy built-in method which uses pyplot.::
   engine.plot_adjacency_dict(). (Source geoms are grey, targets are blue, obstacles are red. Linkages
   are green.

   .. image:: images/adjacency_with_segmentation.png

#. You probably will want to match the adjacency dictionary back to the original data so that you can do something cool with it.

   .. code-block:: python

      for source_i, target_i_list in output.items():
          source_geom = source_geometries[source_i]
          target_geoms = [target_geometries[i] for i in target_i_list]

That's it!

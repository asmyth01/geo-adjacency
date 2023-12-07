Installation
============

Install with pip
----------------

Install with `pip`_::

   python -m pip install geo-adjacency

The guts of `geo-adjacency` depends on Scipy, and the QHull library.


Build from Source
-----------------

If you are a developer, you may want to build from the source. `geo-adjacency` is built
with Poetry. Installation of Poetry is covered `here`_.

.. code-block:: bash

   git clone git@github.com:asmyth01/geo-adjacency.git
   cd geo-adjacency
   poetry install

Or use `build`

.. code-block:: bash

   git clone git@github.com:asmyth01/geo-adjacency.git
   cd geo-adjacency
   python -m build .


.. _pip: https://pip.pypa.io/en/stable/installation/ 
.. _here: https://python-poetry.org/docs/#installation



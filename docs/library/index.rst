Library
=======

.. currentmodule:: veux

.. toctree::
   :hidden:
   :maxdepth: 1

   Library <self>


The :mod:`veux` package features the following high-level 
functions for quickly rendering finite element models:

.. autosummary::
   :caption: Basic Rendering
   :toctree: api/

   render
   draw_shape
   create_artist
   serve


An object-oriented interface provides more control over the rendering process.
This centers around the :ref:`Artist <artist>` class, which provides methods for drawing various types of finite element data.

.. toctree::
   :hidden:
   :caption: Advanced Rendering
   :maxdepth: 1

   artist/index
   model
   canvas
   state


.. top-level functions
.. -------------------
.. .. automodule:: veux
..    :members:
..    :undoc-members:
..    :show-inheritance:


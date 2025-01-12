Design 
======

``veux`` is a finite element visualization library that is particularly well-suited for use with OpenSees.
Unlike other frameworks targeting OpenSees, ``veux`` does not rely on the singular global state exposed in the OpenSeesPy library.
Rather, visualizations are created by explicitly passing data structures which represent the model of interest. 
This approach leads to a much more reliable and secure experience, meaning that ``veux`` is suitable for both research and production applications. 
See for example `this paper <https://doi.org/10.1002/nme.7506>`_ and the https://structures.live platform.


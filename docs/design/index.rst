Design 
======

``veux`` is designed around a set of core abstract classes:

- A ``Canvas`` abstracts away details about the rendering backend.
- An ``Artist`` abstracts away the drawing process. It owns a canvas.


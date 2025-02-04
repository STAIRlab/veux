# Artist

An ``Artist`` is a class that owns a `Model` and a `Canvas`, and provides a convenient interface for drawing 
entities associated with the model. That is, rather than manually drawing lines and surfaces
through the `Canvas`, an artist can be used to draw higher-level entities like frames and shells.

```{toctree}
:maxdepth: 1

draw_outlines
draw_surfaces
```


## Viewing a Rendering

To view a rendering generated with `canvas="gltf"` or `canvas="plotly"`, use the `veux.serve()` function::

    veux.serve(artist)

This will start a local web server and output a message like::

    Listening on http://localhost:8081/
    Hit Ctrl-C to quit.

Open the URL (e.g., http://localhost:8081) in a web browser to interactively view the rendering.

## Saving a Rendering

Use the `artist.save(...)` method to write the rendering to a file. The file format depends on the selected canvas:

- **gltf**: Files are saved in the glTF format with a `.glb` extension:
  ```python
  artist.save("model.glb")
  ```

- **plotly**: Files are saved as `.html`::
  ```python
  artist.save("model.html")
  ```

- **matplotlib**: Files are saved as `.png`::
  ```python
  artist.save("model.png")
  ```


```{currentmodule} veux
```

# Canvas


```{eval-rst}  
.. autofunction:: _create_canvas
```


`veux` supports several different rendering technologies through the `canvas` abstraction.

<dl>

<dt><code>"gltf"</code></dt><dd>
The <code>gltf</code> canvas uses <a href="https://www.khronos.org/gltf/">glTF</a> technology to build renderings. This is useful for generating publication-ready renderings and efficiently navigating large complex models. This canvas tends to create the most presentable and responsive renderings. When
saved to a <b>.glb</b> file and opened in a 3D model viewer, ray tracing can be used to 
add realistic shadows.

glTF’s internal structure mimics the memory buffers commonly used by graphics chips when rendering in real-time, such that assets can be delivered to desktop, web, or mobile clients and be promptly displayed with minimal processing.

Renderings on the <code>gltf</code> canvas can stored as <b>glb</b> or <b>html</b> files.
</dd>

<dt><code>"plotly"</code></dt><dd>
The <code>plotly</code> canvas is useful for model development and debugging because it can add model property summaries that show up when hovered over by the mouse. 
However, this canvas tends to be a bit slower and slightly less presentable than the <code>gltf</code> canvas. 
This canvas uses the <a href="https://plotly.com/">Plotly</a> library.

Renderings on the <code>plotly</code> canvas can stored as <b>html</b> files and opened in standard browsers.
</dd>
</dl>

```{admonition} Note
:class: warning

Renderings produced with the ``"matplotlib"`` canvas are typically of poor quality. For high-quality images, use the ``"gltf"`` canvas and take screen captures.
```



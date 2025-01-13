
# Canvas
![](image-1.png)

`sees` supports several different rendering technologies through the `canvas` option.

<dl>

<dt>gltf</dt><dd>
The <code>gltf</code> canvas is useful for generating publication-ready renderings and efficiently navigating large complex models. This canvas tends to create the most presentable and responsive renderings. When
saved to a <b>.glb</b> file and opened in a 3D model viewer, ray tracing can be used to 
add realistic shadows.

Renderings on the <code>gltf</code> canvas can stored as <b>glb</b> files and opened in standard browsers.
</dd>

<dt>plotly</dt><dd>
The <code>plotly</code> canvas is useful for model development and debugging because it can add model property summaries that show up when hovered over by the mouse. However, this canvas tends to be a bit slower and slightly less presentable than the <code>gltf</code> canvas.

Renderings on the <code>plotly</code> canvas can stored as <b>html</b> files and opened in standard browsers.
</dd>
</dl>

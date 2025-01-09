# Claudio Perez
# Summer 2024
import textwrap
from pathlib import Path

class Viewer:
    def __init__(self, viewer=None, src=None):
        self._glbsrc = "./model.glb" if src is None else src
        self._viewer = viewer if viewer is not None else "mv"

    def get_html(self):
        if self._viewer == "three-160":
            with open(Path(__file__).parents[0]/"gltf.html", "r") as f:
                return f.read()

        elif self._viewer == "three-130":
            with open(Path(__file__).parents[0]/"index.html", "r") as f:
                return f.read()

        elif self._viewer == "mv":
            html = textwrap.dedent(f"""
          <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
            "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
          <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>veux</title>
            <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js">
            </script>
          </head>
          <body>
            <model-viewer alt="rendering"
                          src="{self._glbsrc}"
                          autoplay
                          style="width: 100%; height: 500px;"
                          max-pixel-ratio="2"
                          shadow-intensity="1"
                          environment-image="/black_ground.hdr"
                          environment-image="neutral"
                          shadow-light="10000 10000 10000"
                          exposure="0.8"
                          camera-controls
                          min-camera-orbit="auto auto 0m"
                          touch-action="pan-y">
            </model-viewer>
          </body>
          </html>
        <!--
                          bounds="0 0 0 10000 10000 10000"
                          ar
                          environment-image="https://modelviewer.dev/shared-assets/environments/spruit_sunrise_1k_LDR.jpg"
                          shadow-softness="0.8"
                          ar-modes="scene-viewer; quick-look"
                          position="0 0 -50"
                          scale="0.01 0.01 0.01"
        -->
        """)
        return html


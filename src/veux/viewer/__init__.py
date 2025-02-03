# Claudio Perez
# Summer 2024
import base64
import textwrap
from pathlib import Path

class Viewer:
    """
    A class to represent a 3D model viewer.

    Methods:
    --------
    __init__(self, viewer=None, path=None, data=None):
        Initializes the Viewer with optional viewer type, file path, or binary data.

    """
    def __init__(self, viewer=None, path=None, data=None):
        if data is not None:
            data64 = base64.b64encode(data).decode('utf-8')
            self._glbsrc=f"data:model/gltf-binary;base64,{data64}"
        else:
            self._glbsrc = path 

        self._viewer = viewer if viewer is not None else "mv"

    def get_html(self):
        if self._viewer == "babylon":
            with open(Path(__file__).parents[0]/"babylon.html", "r") as f:
                return f.read()

        if self._viewer == "three-170":
            with open(Path(__file__).parents[0]/"three-170.html", "r") as f:
                return f.read()

        if self._viewer == "three-160":
            with open(Path(__file__).parents[0]/"gltf.html", "r") as f:
                return f.read()

        elif self._viewer == "three-130":
            with open(Path(__file__).parents[0]/"index.html", "r") as f:
                return f.read()

        elif self._viewer == "mv":
            return _model_viewer(self._glbsrc, control=False)


def _model_viewer(source, control=False):
      library = '<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js"></script>'

      try:
          with open(Path(__file__).parents[0]/"controls.css", "r") as f:
              control_style = f"<style>{f.read()}</style>"

          with open(Path(__file__).parents[0]/"controls.js", "r") as f:
              control_code = f"<script>{f.read()}</script>"
      except:
          control_code = ""
          control_style = ""

      control_html = """
        <div class="controls">
          <!-- <button id="step-backward">Step Left</button> -->
          <button id="toggle-animation">Pause</button>
          <!-- <button id="step-forward">Step Right</button> -->
        </div>
      """


      foot = "</body></html>"
      head = f"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>veux</title>
          {library}
          {control_style}
        </head>
        <body>
      """

      viewer = f"""
          <model-viewer id="veux-viewer"
                        alt="rendering"
                        src="{source}"
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
      """
      return textwrap.dedent(f"""
            {head}
            {viewer}
            {control_html if control else ""}
            {control_code if control else ""}
            {foot}
      """)

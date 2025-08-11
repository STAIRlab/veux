#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio M. Perez
#
# Summer 2024
#
import os
import base64
import textwrap
from pathlib import Path
import numpy as np
import numpy as np
from io import BytesIO

class Viewer:
    """
    A class to represent a 3D model viewer.

    Methods:
    --------
    __init__(self, viewer=None, path=None, data=None):
        Initializes the Viewer with optional viewer type, file path, or binary data.

    """
    def __init__(self, thing,
                 viewer=None, id=None, 
                 plane = False,
                 size=None,
                 hosted=None,
                 show_quit=True,
                 quit_on_load=False,
                 standalone=True,
                 lights=None):
        
        """
        If hosted is True, the viewier will fetch the model.

        If standalone is True, the viewer will be rendered as a standalone HTML page.
        """
        self._id = id if id is not None else "veux-viewer"
        self._viewer = viewer if viewer is not None else os.environ.get("VEUX_VIEWER","mv")
        self._lights = lights # light or dark mode
        self._plane = plane
        self._size = size
        self._show_quit = show_quit
        self._quit_on_load = quit_on_load

        self._hosted = hosted
        if hosted is None and self._viewer == "mv":
            self._hosted = False
        elif hosted is None:
            self._hosted = True

        if hasattr(thing, "canvas"):
            # artist was passed
            canvas = thing.canvas
            data = canvas.to_glb()
        elif hasattr(thing, "to_glb"):
            canvas = thing
            data = canvas.to_glb()
        else:
            data = thing

        self._standalone = standalone

        if not self._hosted:
            self._model_data = None
            data64 = base64.b64encode(data).decode('utf-8')
            self._glbsrc=f"data:model/gltf-binary;base64,{data64}"
        else:
            self._model_data = data
            self._glbsrc = "/model.glb" 


    def resources(self):
        if self._hosted:
            yield ("/model.glb", lambda : self._model_data)

            if self._viewer == "mv":
                yield ("/black_ground.hdr", _serve_black_ground_hdr)


    def get_html(self):
        if self._viewer == "babylon":
            with open(Path(__file__).parents[0]/"babylon.html", "r") as f:
                return f.read()

        if self._viewer in {"three-170", "three"}:
            with open(Path(__file__).parents[0]/"three-170.html", "r") as f:
                return f.read()

        if self._viewer == "three-160":
            with open(Path(__file__).parents[0]/"three-160.html", "r") as f:
                return f.read()

        elif self._viewer == "three-130":
            with open(Path(__file__).parents[0]/"three-130.html", "r") as f:
                return f.read()

        elif self._viewer == "mv":
            return _model_viewer(self._glbsrc,
                                 control=False,
                                 plane=self._plane,
                                 size=self._size,
                                 show_quit=self._show_quit,
                                 quit_on_load=self._quit_on_load,
                                 hosted=self._hosted,
                                 light_mode=self._lights,
                                 standalone=self._standalone)


def _model_viewer(source,
                  control=False,
                  size=None,
                  hosted=False,
                  plane=False,
                  show_quit=None,
                  quit_on_load=False,
                  standalone=True,
                  light_mode=None):

    if light_mode is None:
        light_mode = "light"

    lights = """
      <style>
      html {
        color-scheme: light; /* dark */
        background-color: #555555;
        --poster-color: #555555;
        --progress-bar-color: #fff;
        --progress-bar-background-color: rgba(255, 255, 255, 0.2);
      }
      @media (prefers-color-scheme: dark) {
        model-viewer {
          --poster-color: #555555;
          background-color: #555555;
        }
      }
      </style>
    """
    lights = ""

    with open(Path(__file__).parents[0]/"controls.css", "r") as f:
        control_style = f"<style>{f.read()}</style>"

    with open(Path(__file__).parents[0]/"controls.js", "r") as f:
        control_script = f"<script>{f.read()}</script>"

    with open(Path(__file__).parents[0]/"model-viewer.min.js", "r") as f:
        library = f'<script type="module">{f.read()}</script>'

    control_html = """
      <div class="controls">
        <button id="toggle-animation">Pause</button>
      </div>
    """

    
    if hosted:
        environment = "/black_ground.hdr"
    else:
        environment = "neutral"
    
    if False: #plane:
        camera = """
            camera-controls
            disable-rotate
            camera-orbit="0deg 90deg auto"
            auto-rotate="false"
        """
    else:
        camera = """
            camera-controls
            max-field-of-view="90deg" 
        """
            # min-camera-orbit='auto auto 100%'
            # max-camera-orbit='auto auto 100%'
            # min-camera-orbit="auto auto 0m"

    if size is None:
        size = 'style="width: 100%; height: 100vh;"'
    else:
        size = f'style="width: {size[0]}px; height: {size[1]}px;"'
    
    quit_button = ""
    if show_quit:
        quit_button = """<form action="/quit" method="get" target="quit-frame" style="display:inline;">
            <button type="submit" style="
                display:inline-flex;align-items:center;justify-content:center;
                width:24px;height:24px;border:none;border-radius:4px;
                background:#eee;color:#333;text-decoration:none;
                font-weight:bold;font-size:16px;
                transition:background 0.2s ease;cursor:pointer;"
                onmouseover="this.style.background='#ccc'"
                onmouseout="this.style.background='#eee'">
                <svg viewBox="0 0 10 10" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="1" y1="1" x2="9" y2="9" />
                <line x1="9" y1="1" x2="1" y2="9" />
                </svg>
            </button>
          </form>
          <iframe name="quit-frame" style="display:none;"></iframe>
        """
    
    quit_script = ""
    if quit_on_load:
        quit_script = """
        <script>
        window.addEventListener('load', function() {
            const quitButton = document.querySelector('form[action="/quit"] button');
            if (quitButton) {
                quitButton.click();
            }
        });
        </script>
        """

    capt_button = """<button id="capture-button">Capture</button>"""
    capt_script =  """
    <script>
    const modelViewer = document.getElementById("veux-viewer");

    async function downloadPosterToBlob() {
        const blob = await modelViewer.toBlob({ idealAspect: false });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "modelViewer_toBlob.png";
        a.click();
        URL.revokeObjectURL(url);
    }

    function downloadPosterToDataURL() {
        const url = modelViewer.toDataURL();
        const a = document.createElement("a");
        a.href = url;
        a.download = "modelViewer_toDataURL.png";
        a.click();
        URL.revokeObjectURL(url);
    }
    document.querySelector("#capture-button").addEventListener("click", downloadPosterToBlob);
    
    </script>
    """

    viewer = f"""
          {quit_button}
          {capt_button if show_quit else ""}

          <model-viewer 
            id="veux-viewer"
            alt="rendering"
            src="{source}"
            autoplay
            {size}
            max-pixel-ratio="2"
            interaction-prompt="none"
            shadow-intensity="1"
            environment-image="{environment}"
            shadow-light="10000 10000 10000"
            exposure="0.8"
            {camera}
            touch-action="pan-y">
            <div class="progress-bar hide" slot="progress-bar">
                <div class="update-bar"></div>
            </div>
          </model-viewer>
    """

    if not standalone:
        page = f"""
        <div style='display: flex; flex-direction: row;'>
        {library}
        {viewer}
        </div>
        """
    else:
        page = f"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
            "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>veux</title>
            {library}
            {lights}
            {control_style}
            </head>
            <body>
                {viewer}
                {control_html if control else ""}
                {control_script if control else ""}
            </body>
            {quit_script}
            {capt_script}
        </html>
        """
    return textwrap.dedent(page)


def _serve_black_ground_hdr():
    import bottle
    width, height = 1024, 512

    # Create a blank HDR image
    hdr_image = np.ones((height, width, 3), dtype=np.float32)  # Start with white
    horizon = int(height * 0.6)
    hdr_image[horizon:, :] = 0.0  # Black ground

    # Create the HDR header
    hdr_header = (
        "#?RADIANCE\n"
        "FORMAT=32-bit_rle_rgbe\n\n"
        f"-Y {height} +X {width}\n"
    )

    # Convert the RGB values to Radiance RGBE format
    rgbe_image = np.zeros((height, width, 4), dtype=np.uint8)
    brightest = np.maximum.reduce(hdr_image, axis=2)
    nonzero_mask = brightest > 0
    mantissa, exponent = np.frexp(brightest[nonzero_mask])
    rgbe_image[nonzero_mask, :3] = (hdr_image[nonzero_mask] / mantissa[:, None] * 255).astype(np.uint8)
    rgbe_image[nonzero_mask, 3] = (exponent + 128).astype(np.uint8)

    # Encode the HDR data to memory
    hdr_data = BytesIO()
    hdr_data.write(hdr_header.encode('ascii'))  # Write the header
    hdr_data.write(rgbe_image.tobytes())  # Write the pixel data

    # Serve the HDR file
    return bottle.HTTPResponse(
        body=hdr_data.getvalue(),
        status=200,
        headers={"Content-Type": "image/vnd.radiance"}
    )
#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
# Summer 2024
import sys
import bottle
from .viewer import Viewer
from PIL import Image
import numpy as np
from io import BytesIO

class Server:
    def __init__(self, glb=None, html=None, artist=None, viewer=None):
        # Create App
        self._app = bottle.Bottle()

        if glb is not None:
            self._source = "glb"
            html = Viewer(path="./model.glb",
                          data=glb,
                          viewer=viewer).get_html()

            # Create routes
            self._app.route("/model.glb")(lambda : glb  )
            self._app.route("/")(lambda          : html )

            @self._app.route('/black_ground.hdr')
            def serve_black_ground_hdr():
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


        elif artist is not None:
            self._source = "artist"

        else:
            self._source = "html"
            # Create routes
            self._app.route("/")(lambda : html )

    def run(self, port=None):
        if port is None:
            port = 8081

        print(f"  Displaying at http://localhost:{port}/ \n  Press Ctrl-C to quit.\n")
        try:
            bottle.run(self._app, host="localhost", port=port, quiet=True)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":

    options = {
        "viewer": None
    }
    argi = iter(sys.argv[1:])

    for arg in argi:
        if arg == "--viewer":
            options["viewer"] = next(argi)
        else:
            filename = arg

    with open(filename, "rb") as f:
        glb = f.read()

    Server(glb=glb, **options).run()

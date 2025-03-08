# Claudio Perez
# Summer 2024
import sys
import bottle
from veux.viewer import Viewer
from veux.server import Server


if __name__ == "__main__":

    options = {
        "viewer": "mv" #"three-170"
    }
    filename = sys.argv[1]

    with open(filename, "rb") as f:
        glb = f.read()


    Server(viewer=Viewer(glb, **options)).run()



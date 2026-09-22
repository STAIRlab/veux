# Claudio Perez
# Summer 2024
import sys
import bottle
from veux.viewer import Viewer
from veux.server import Server
from argparse import ArgumentParser


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--viewer", default="mv", help="Viewer to use (default: mv)")
    args = parser.parse_args()

    options = {
        "viewer": args.viewer
    }
    filename = args.filename

    with open(filename, "rb") as f:
        glb = f.read()


    Server(viewer=Viewer(glb, **options)).run()



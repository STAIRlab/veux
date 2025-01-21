#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Main command line interface
#
import sys

from veux import render
from veux.parser import parse_args, NAME
from veux.errors import RenderError
import veux.server


def main(argv):

    try:
        config = parse_args(argv)

        if config is None:
            sys.exit()

        artist = render(**config)

        # write plot to file if output file name provided
        if config["write_file"]:
            artist.save(config["write_file"])
            return

        # Otherwise either create popup, or start server
        elif hasattr(artist.canvas, "popup"):
            artist.canvas.popup()

        elif hasattr(artist.canvas, "to_glb"):
            import veux.server
            viewer = config["viewer_config"].get("name", None)
            port = config["server_config"].get("port", None)
            server = veux.server.Server(glb=artist.canvas.to_glb(),
                                        viewer=viewer)
            server.run(port=port)

        elif hasattr(artist.canvas, "to_html"):
            import veux.server
            port = config["server_config"].get("port", None)
            server = veux.server.Server(html=artist.canvas.to_html())
            server.run(port=port)

    except (FileNotFoundError, RenderError) as e:
        # Catch expected errors to avoid printing an ugly/unnecessary stack trace.
        print(f"ERROR - {e}", file=sys.stderr)
        print("         Run '{NAME} --help' for more information".format(NAME=NAME), file=sys.stderr)
        sys.exit(-1)


if __name__ == "__main__":
    main(sys.argv)


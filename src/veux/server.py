#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
# Summer 2024
#
import sys
import socket
import threading
from wsgiref.simple_server import make_server
import bottle



def _open_borderless_viewer(url):
    # TODO
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--app=' + url,     # launch in app mode
                '--window-size=800,600',
                '--disable-infobars',
                '--no-default-browser-check',
                '--disable-extensions',
            ]
        )
        context = browser.new_context()
        context.new_page()  # required to keep browser alive on some systems
        input("Press Enter to exit and close browser...")
        browser.close()

def _check_port(port):
    # Check if the port is available
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except OSError as e:
            return False

def _find_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

class Server:
    def __init__(self, viewer=None, html=None):
        self._app = bottle.Bottle()
        self._server = None

        if html is not None:
            self._app.route("/")(lambda : html )
            return

        if viewer is not None:

            html = viewer.get_html()
            self._app.route("/")(lambda : html )
            @self._app.route("/quit")
            def _quit():
                threading.Thread(target=self._shutdown).start()
                return "Shutting down..."


            for path, page in viewer.resources():
                self._app.route(path)(page)

    def _shutdown(self):
        if self._server:
            self._server.shutdown()

    def run(self, port=None):
        if port is None:
            # Default to something consistent
            port = 8081 if _check_port(8081) else _find_port()

        print(f"  Displaying at http://localhost:{port}/ \n  Press Ctrl-C to quit.\n")

        self._server = make_server("localhost", port, self._app)
        self._server.serve_forever()


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

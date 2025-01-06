#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
from pathlib import Path

from .errors import RenderError
from .config import Config, apply_config
from .parser import sketch_show
from .frame import FrameArtist
from . import utility

assets = Path(__file__).parents[0]/"assets/"

def Canvas(subplots=None, backend=None):
    pass

def __getattr__(name: str):
    import opensees.openseespy
    if name == "Model":
        return opensees.openseespy.Model
    elif name == "openseespy":
        return opensees.openseespy


def serve(artist, viewer="mv", port=None):
    import veux.server
    if hasattr(artist.canvas, "to_glb"):
        server = veux.server.Server(glb=artist.canvas.to_glb(),
                                    viewer=viewer)
        server.run(port=port)

    elif hasattr(artist.canvas, "to_html"):
        server = veux.server.Server(html=artist.canvas.to_html())
        server.run(port=port)

    elif hasattr(artist.canvas, "show"):
        artist.canvas.show()

    else:
        raise ValueError("Cannot serve artist")


def _create_canvas(name=None, config=None):
    if name is None:
        name = "gltf"

    if not isinstance(name, str):
        return name
    elif name == "matplotlib":
        import veux.canvas.mpl
        return veux.canvas.mpl.MatplotlibCanvas(config=config)
    elif name == "plotly":
        import veux.canvas.ply
        return veux.canvas.ply.PlotlyCanvas(config=config)
    elif name == "gltf":
        import veux.canvas.gltf
        return veux.canvas.gltf.GltfLibCanvas(config=config)
    elif name == "trimesh":
        import veux.canvas.tri
        return veux.canvas.tri.TrimeshCanvas(config=config)
    else:
        raise ValueError("Unknown canvas name " + str(name))

def render(sam_file, res_file=None, ndf=6,
           canvas=None,
           show=None,
           hide=None,
           verbose=False,
           vertical=2,
           displaced=None,
           reference=None,
           **opts):

    import veux.model

    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds 

    if sam_file is None:
        raise RenderError("Expected required argument <sam-file>")

    #
    # Read model data
    #
    if isinstance(sam_file, (str, Path)):
        model_data = veux.model.read_model(sam_file)

    elif hasattr(sam_file, "asdict"):
        # Assuming an opensees.openseespy.Model
        model_data = sam_file.asdict()

    elif hasattr(sam_file, "read"):
        model_data = veux.model.read_model(sam_file)

    elif isinstance(sam_file, tuple):
        # TODO: (nodes, cells)
        pass

    elif not isinstance(sam_file, dict):
        model_data = veux.model.FrameModel(sam_file)

    else:
        model_data = sam_file

    # Setup config
    config = Config()

    if "RendererConfiguration" in model_data:
        apply_config(model_data["RendererConfiguration"], config)

    config["artist_config"]["vertical"] = vertical
    apply_config(opts, config)
    if show is not None and reference is None and displaced is None: 
        reference = show 

    if reference is not None:
        preserve = set()
        sketch_show(config["artist_config"], f"reference", "show")
        for arg in reference:
            sketch_show(config["artist_config"], f"reference:{arg}", "show", exclusive=True, preserve=preserve)
    if displaced is not None:
        preserve = set()
        for arg in displaced:
            sketch_show(config["artist_config"], f"displaced:{arg}", "show", exclusive=True, preserve=preserve)

    if hide is not None:
        preserve = set()
        sketch = "reference"; # "displaced"
        for arg in hide:
            sketch_show(config["artist_config"], f"{sketch}:{arg}", "hide", exclusive=True, preserve=preserve)

    if verbose:
        import pprint
        pprint.pp(config["artist_config"])

    #
    # Create Artist
    #
    # A Model is created from model_data by the artist
    # so that the artist can inform it how to transform
    # things if neccessary.
    artist = FrameArtist(model_data, ndf=ndf,
                         config=config["artist_config"],
                         model_config=config["model_config"],
                         canvas=_create_canvas(canvas or config["canvas_config"]["type"],
                                               config=config["canvas_config"]))


    #
    # Read and process displacements 
    #
    if res_file is not None:
        artist.add_state(res_file,
                         scale=config["scale"],
                         only=config["mode_num"],
                         **config["state_config"])

    elif config["displ"] is not None:
        pass
        # TODO: reimplement point displacements
        # cases = [artist.add_point_displacements(config["displ"], scale=config["scale"])]

    if "Displacements" in model_data:
        cases.extend(artist.add_state(model_data["Displacements"],
                                        scale=config["scale"],
                                        only=config["mode_num"]))

    artist.draw()

    return artist


def render_mode(model, mode_number, scale=1, file_name=None, canvas="gltf", **kwds):

    # Define a function that tells the renderer the displacement
    # at a given node. We will pass this function as an argument
    # when constructing the "artist" object, which in turn will 
    # invoke this function for each node tag in the model.
    def displ_func(tag: int)->list:
        return [float(scale)*ui for ui in model.nodeEigenvector(tag, mode_number)]

    # Create the rendering
    return render(model, displ_func, canvas=canvas, **kwds)




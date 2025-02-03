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


def serve(thing, viewer="mv", port=None):
    """
    Serve the given thing using the specified viewer and port.

    Parameters
    ----------
    thing : object
        The object to be served. It can be an artist with a canvas attribute or a canvas itself.
    viewer : str, optional
        The viewer to use for serving the thing. Default is ``"mv"``.
    port : int, optional
        The port to run the server on. If not specified, a default port will be used.

    Raises
    ------
    ValueError
        If the thing cannot be served because it does not have the required methods.

    Notes
    -----
    The function checks the following in order:

    1. If the thing has a 'canvas' attribute, it uses the canvas.
    2. If the canvas has a 'to_glb' method, it serves using GLB format.
    3. If the canvas has a 'to_html' method, it serves using HTML format.
    4. If the canvas has a 'show' method, it calls the show method.
    5. If none of the above conditions are met, it raises a ValueError.
    """
    import veux.server

    if hasattr(thing, "canvas"):
        # artist was passed
        canvas = thing.canvas
    else:
        canvas = thing

    if hasattr(canvas, "to_glb"):
        server = veux.server.Server(glb=canvas.to_glb(),
                                    viewer=viewer)
        server.run(port=port)

    elif hasattr(canvas, "to_html"):
        server = veux.server.Server(html=canvas.to_html())
        server.run(port=port)

    elif hasattr(canvas, "show"):
        canvas.show()

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


def _create_model(sam_file, ndf=None):

    import veux.model

    if isinstance(sam_file, (str, Path)):
        model_data = veux.model.read_model(sam_file)

    elif hasattr(sam_file, "asdict"):
        # Assuming an opensees.openseespy.Model
        model_data = sam_file.asdict()

    elif hasattr(sam_file, "read"):
        model_data = veux.model.read_model(sam_file)

    elif isinstance(sam_file, tuple):
        from veux.plane import PlaneModel
        return PlaneModel(sam_file, ndf=ndf)

    elif not isinstance(sam_file, dict):
        model_data = veux.model.FrameModel(sam_file)

    else:
        model_data = sam_file

    return model_data

def create_artist(
           sam_file, ndf=6,
           canvas="gltf",
           vertical=2,
           **opts):
    """
    Create an artist for a model::

        artist = veux.create_artist(model, canvas=canvas)

    Parameters
    ----------
    model : str, dict, or Model
        The ``model`` parameter can be of several types:

        - **str**: Treated as a file path. Supported file formats are ``.json`` and ``.tcl``.
        - **dict**: A dictionary representation of the model.
        - **Model**: An instance of the ``Model`` class from the `sees <https://pypi.org/project/sees>`_ Python package. See the `documentation <https://stairlab.github.io/OpenSeesDocumentation/user/manual/model/model_class.html>`_ 
          for details.

    canvas : str, optional
        The rendering backend to use. Options are:

        - ``"gltf"`` (default): Produces high-quality renderings. Files can be saved as ``.html`` or ``.glb``. ``.glb`` is recommended for 3D object portability.
        - ``"plotly"``: Best for model debugging. Includes detailed annotations (e.g., node/element numbers, properties) but lower visual quality than  ``gltf``.
        - ``"matplotlib"``: Generates ``.png`` files programmatically. Note that renderings are lower quality compared to ``gltf``.

    Returns
    -------
    artist : Artist
        An object representing the rendered model. Can be used to view or save the rendering.

    """

    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds 

    if sam_file is None:
        raise RenderError("Expected required argument <sam-file>")

    model_data = _create_model(sam_file, ndf=ndf)

    # Setup config
    config = Config()

    if isinstance(model_data, dict) and "RendererConfiguration" in model_data:
        apply_config(model_data["RendererConfiguration"], config)

    config["artist_config"]["vertical"] = vertical
    apply_config(opts, config)

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


    return artist


def render(sam_file, res_file=None, ndf=6,
           canvas=None,
           show=None,
           hide=None,
           verbose=False,
           vertical=2,
           displaced=None,
           reference=None,
           **opts):
    """
    Primary rendering function.

    To render a model directly from Python::

        artist = veux.render(model, canvas=canvas)

    Parameters
    ----------
    model : str, dict, or Model
        The ``model`` parameter can be of several types:

        - **str**: Treated as a file path. Supported file formats are ``.json`` and ``.tcl``.
        - **dict**: A dictionary representation of the model.
        - **Model**: An instance of the ``Model`` class from the `sees <https://pypi.org/project/sees>`_ Python package. See the `documentation <https://stairlab.github.io/OpenSeesDocumentation/user/manual/model/model_class.html>`_ 
          for details.

    canvas : str, optional
        The rendering backend to use. Options are:

        - ``"gltf"`` (default): Produces high-quality renderings. Files can be saved as ``.html`` or ``.glb``. ``.glb`` is recommended for 3D object portability.
        - ``"plotly"``: Best for model debugging. Includes detailed annotations (e.g., node/element numbers, properties) but lower visual quality than  ``gltf``.
        - ``"matplotlib"``: Generates ``.png`` files programmatically. Note that renderings are lower quality compared to ``gltf``.

    Returns
    -------
    artist : Artist
        An object representing the rendered model. Can be used to view or save the rendering.


    """

    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds 

    if sam_file is None:
        raise RenderError("Expected required argument <sam-file>")

    #
    # Read model data
    #
    model_data = _create_model(sam_file)

    # Setup config
    config = Config()

    if isinstance(model_data, dict) and "RendererConfiguration" in model_data:
        apply_config(model_data["RendererConfiguration"], config)

    config["artist_config"]["vertical"] = vertical
    apply_config(opts, config)

    # TODO: Maybe this be moved after constructing FrameArtist;
    # that way we can just say 
    # artist = create_artist(sam_file, vertical=vertical, **)
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

    if isinstance(model_data, dict) and "Displacements" in model_data:
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




#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Command line parsing
#
import os
import ast
import sys
import json
import numpy as np
from veux import config
from veux.errors import RenderError


__version__ = "0.0.13"

NAME = "veux"

HELP = """
usage: {NAME} <sam-file>
       {NAME} --setup ...
       {NAME} [options] <sam-file>
       {NAME} [options] <sam-file> <res-file>
       {NAME} --section <py-file>#<py-object>

Generate a plot of a structural model.

Positional Arguments:
  <sam-file>                     JSON file defining the structural model.
  <res-file>                     JSON or YAML file defining a structural
                                 response.

Options:
  DISPLACEMENTS
  -s, --scale  <scale>           Set displacement scale factor.
  -d, --disp   <node>:<dof>...   Apply a unit displacement at node with tag
                                 <node> in direction <dof>.
  CANVAS
  --canvas <canvas>              trimesh, gnu, plotly, matplotlib

  ARTIST
  --view   {{elev|plan|sect}}      Set camera view.
  --vert   <int>                 Specify index of model's vertical coordinate
  --hide   <object>              Hide <object>; see '--show'.
  --show   <object>              Show <object>; accepts any of:
                                    {{origin|frames|frames.displ|nodes|nodes.displ|extrude}}

  SERVER
  --port <port>                  port to serve rendering

  MISC.
  -o, --save   <out-file>        Save plot to <out-file>.
      --conf   <conf-file>
  -c           <canvas>
      --version                  Print version and exit.
  -h, --help                     Print this message and exit.



  <dof>        {{long | tran | vert | sect | elev | plan}}
               {{  0  |   1  |   2  |   3  |   4  |   5 }}
  <object>     {{origin|frames|frames.displ|nodes|nodes.displ}}
    origin
    frames
    nodes
    legend
    extrude                      extrude cross-sections
    outline                      outline extrusion
    triads
    x,y,z

    fibers
"""


AXES = dict(zip(("long","tran","vert",
                 "sect","elev", "plan"), range(6)))

def dof_index(dof: str):
    try: return int(dof)
    except: return AXES[dof]


def sketch_show(artist_config, argn: str, arg="show", exclusive: bool=False, preserve: set=None):

    if argn == "reference" and "reference" not in artist_config["sketches"]:
        artist_config["sketches"]["reference"] = config.SketchConfig(artist_config["sketches"]["default"])
        return

    objects = argn

    if ":" in objects:
        sketches, objects = objects.split(":")
        sketches = [sketches]
    else:
        sketches = artist_config["sketches"].keys()

    if arg != "style":
        objects = objects.split(",")
    else:
        objects = [objects]

    for sketch in sketches:
        if sketch not in artist_config["sketches"]:
            artist_config["sketches"][sketch] = config.SketchConfig(artist_config["sketches"]["default"])

        for feature in objects:
            try:
                obj, feature = feature.split(".", 1)
            except:
                raise RenderError(f"Failed to parse argument {argn}; unknown object {feature}")

            if exclusive:
                for k, v in artist_config["sketches"][sketch][obj].items():
                    if preserve is not None and (sketch, obj, k) in preserve:
                        continue
                    if v is not None:
                        v["show"] = False

            if arg == "style":
                feature, val = feature.split("=")
                try:
                    feature, prop = feature.split(".")
                except ValueError:
                    raise RenderError(f"Failed to parse argument {argn}; cannot split {feature}")
                try:
                    val = ast.literal_eval(val)
                except Exception as e:
                    # If we fail to parse the value as a literal,
                    # we settle for a string
                    pass

                if  hasattr(artist_config["sketches"][sketch][obj][feature]["style"], prop):
                    setattr(artist_config["sketches"][sketch][obj][feature]["style"], prop, val)
                else:
                    artist_config["sketches"][sketch][obj][feature][prop] = val

                artist_config["sketches"][sketch][obj][feature]["show"] = True

            else:
                artist_config["sketches"][sketch][obj][feature]["show"] = (arg == "show")

            if preserve is not None:
                preserve.add((sketch, obj, feature))


def parse_args(argv)->dict:
    # 1. Defaults
    opts = config.Config()

    # 2. Local configuration file
    if os.path.exists(".render.yaml"):
        import yaml
        with open(".render.yaml", "r") as f:
            presets = yaml.load(f, Loader=yaml.Loader)

        config.apply_config(presets,opts)

    # 3. Command line

    canvas_config = opts["canvas_config"]
    artist_config = opts["artist_config"]

    args = iter(argv[1:])
    for arg in args:
        try:
            if arg == "--help" or arg == "-h":
                print(HELP.format(NAME=NAME))
                return None

            elif arg[:2] == "-o":
                filename = arg[2:] if len(arg) > 2 else next(args)
                opts["write_file"] = filename
                if "html" in filename or "json" in filename:
                    opts["canvas_config"]["type"] = "plotly"
                elif "glb" in filename or "gltf" in filename:
                    opts["canvas_config"]["type"] = "gltf"

            elif arg == "--version":
                print(__version__)
                return None

            elif arg == "--conf":
                with open(next(args), "r") as f:
                    presets = yaml.load(f, Loader=yaml.Loader)
                config.apply_config(presets,opts)

            elif arg == "--set":
                k,v = next(args).split("=")
                val = ast.literal_eval(v)
                d = opts
                keys = k.split(".")
                for key in keys[:-1]:
                    if key in d:
                        d = d[key]
                    elif f"{key}_config" in d:
                        d = d[f"{key}_config"]
                    else:
                        raise RenderError(f"Unknown config key {key}.")

                # TODO: implement type casting here
                d[keys[-1]] = val

#           elif hasattr(artist_config, "--" + arg):
#               pass

            #
            # Viewer
            #
            elif arg == "-V":
                pass
            elif arg == "--viewer":
                opts["viewer_config"]["name"] = next(args)
            elif arg == "--port":
                opts["server_config"]["port"] = int(next(args))

            #
            # Canvas
            #
            elif arg == "--canvas":
                opts["canvas_config"]["type"] = next(args)
            elif arg == "--gnu":
                opts["canvas_config"]["type"] = "gnu"
            elif arg == "--plotly":
                opts["canvas_config"]["type"] = "plotly"

            #
            # Artist
            #
            elif arg == "--vert":
                opts["artist_config"]["vertical"] = int(next(args))

            elif arg in {"--sketch", "--reference", "--displaced"}:
                if arg == "--sketch":
                    # --sketch <sketch>.frame.outline.color=black
                    sketch, *fields = next(args).split(".")
                    if sketch not in sketches:
                        sketch = "default"
                else:
                    sketch = arg[2:]
                    fields = next(args).split(".")

            elif arg in {"--show", "--hide", "--style"}:
                # --show sk1,sk2:frame.outline
                # --size sk1,sk2:frame.outline.basis=Lagrange
                sketch_show(artist_config, next(args), arg[2:])
                continue

                objects = argn = next(args)
                if objects == "reference":
                    artist_config["sketches"]["reference"] = config.SketchConfig(artist_config["sketches"]["default"])
                    continue


                if ":" in objects:
                    sketches, objects = objects.split(":")
                else:
                    sketches = artist_config["sketches"].keys()

                if arg != "--style":
                    objects = objects.split(",")
                else:
                    objects = [objects]

                for sketch in sketches:
                    if sketch not in artist_config["sketches"]:
                        artist_config["sketches"][sketch] = config.SketchConfig(artist_config["sketches"]["default"])

                    for stroke in objects:
                        try:
                            obj, stroke = stroke.split(".", 1)
                        except:
                            raise RenderError(f"Failed to parse argument {argn}; unknown object {stroke}")

                        if arg == "--style":
                            stroke, val = stroke.split("=")
                            try:
                                stroke, prop = stroke.split(".")
                            except ValueError:
                                raise RenderError(f"Failed to parse argument {argn}; cannot split {stroke}")
                            try:
                               #val = json.loads(val)
                                val = ast.literal_eval(val)
                            except Exception as e:
                                print(e, val)
                                pass
                            if hasattr(artist_config["sketches"][sketch][obj][stroke]["style"], prop):
                                setattr(artist_config["sketches"][sketch][obj][stroke]["style"], prop, val)
                            else:
                                artist_config["sketches"][sketch][obj][stroke][prop] = val
                            artist_config["sketches"][sketch][obj][stroke]["show"] = True
#                           print(f"{sketch = }", f"{obj = }", f"{stroke = }", artist_config["sketches"][sketch][obj][stroke], sep="\n", end="\n---\n")
                        else:
                            artist_config["sketches"][sketch][obj][stroke]["show"] = (arg == "--show")


            elif arg == "--view":
                opts["view"] = next(args)

            elif arg == "--default-section":
                opts["default_section"] = np.loadtxt(next(args))

            elif arg == "--extrude-default":
                opts["model_config"]["extrude_default"] = next(args)

            elif arg == "--extrude-outline":
                # outline used for everything
                opts["model_config"]["extrude_outline"] = next(args)


            #
            # STATE
            #
            elif arg[:2] == "-s":
                opts["scale"] = float(arg[2:]) if len(arg) > 2 else float(next(args))

            elif arg == "--scale":
                scale = next(args)
                if "=" in scale:
                    # Used like --scale <object>=<scale>
                    k,v = scale.split("=")
                    opts["objects"][k]["scale"] = float(v)
                else:
                    opts["scale"] = float(scale)

            elif arg[:2] == "-m":
                opts["mode_num"] = int(arg[2]) if len(arg) > 2 else int(next(args))

            elif arg == "--time":
                opts["state_config"]["time"] = json.loads(next(args))

            elif arg == "--recover-rotations":
                opts["state_config"]["recover_rotations"] = next(args)

            elif arg[:2] == "-d":
                node_dof = arg[2:] if len(arg) > 2 else next(args)
                for nd in node_dof.split(","):
                    node, dof = nd.split(":")
                    opts["displ"][int(node)].append(dof_index(dof))

            elif arg[:6] == "--disp":
                node_dof = next(args)
                for nd in node_dof.split(","):
                    node, dof = nd.split(":")
                    opts["displ"][int(node)].append(dof_index(dof))


            # Final check on options
            elif arg[0] == "-" and len(arg) > 1:
                raise RenderError(f"unknown option '{arg}'")

            #
            # Positional
            #
            elif not opts["model"]:
                if arg == "-": arg = sys.stdin
                opts["model"] = arg

            else:
                if arg == "-": arg = sys.stdin
                opts["res_file"] = arg

        except StopIteration:
            # `next(args)` was called in parse loop without successive arg
            raise RenderError(f"Argument '{arg}' expected value")

    return opts

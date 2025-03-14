# Command Line Interface

To create a rendering, execute the following command from the anaconda prompt (after activating the appropriate environment):

```shell
python -m veux model.json -o model.html
```

where `model.json` is a file that defines a finite element model. A common file type
is the JSON output produced by the OpenSees [`print`](https://xara.so/user/manual/output/print.html) method.

> **Note** Printing depends on the JSON output of a model. Several materials and
> elements in the OpenSeesPy and upstream OpenSees implementations do not
> correctly print to JSON. For the most reliable results, use the newer
> [`OpenSeesRT`](https://xara.so) distribution.

If you omit the `-o <file.html>` portion, it will plot immediately in a new
window using the `matplotlib` [canvas](https://veux.io/library/canvas.html). 
You can also use a `.png` extension to save a static image file, as
opposed to the interactive html.

By default, the rendering treats the $y$ coordinate as vertical.
In order to manually control this behavior, pass the option 
`--vert 3` to render model $z$ vertically, or `--vert 2` to render model $y$ vertically.

If the [`opensees`](https://pypi.org/project/opensees) package is installed,
you can directly render an [OpenSees](https://opensees.berkeley.edu) Tcl script without first printing to JSON, 
by just passing a Tcl script instead of the JSON file:

```shell
python -m veux model.tcl -o model.html
```

This is implemented efficiently leveraging the new OpenSeesRT interpreter backend to first disable all analysis commands
before the Tcl script is evaluated.

To plot an elevation (`elev`) plan (`plan`) or section (`sect`) view, use the `--view` flag:

```shell
python -m veux model.json --view elev
```

and add `-o <file.extension>` as appropriate.

To see the full help page run

```shell
python -m veux --help
```

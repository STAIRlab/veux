# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
from pathlib import Path
project = 'veux'
copyright = '2025, STAIRLab'
author = 'STAIRLab'
description = "Finite element visualization for xara and OpenSees/OpenSeesPy."
version = '0.0.26'
release = '0.0.26'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    # 'autoapi.extension',
    'myst_parser',
    'sphinx_copybutton',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages',
    'sphinx_sitemap'
]


# autoapi_dirs = ['../src/mdof']


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


source_suffix = '.rst'
root_doc = 'index'
language = 'en'

# -- Options for HTML output -------------------------------------------------
sitemap_url_scheme = "{link}"
sitemap_excludes = [
    "https://veux.io/index.html"
]
html_extra_path = ["robots.txt"]
html_baseurl = "https://veux.io/"
html_title = project
html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_favicon = './_static/images/favicon.ico'
html_css_files = [
    'css/home-css/'+str(file.name) for file in (Path(__file__).parents[0]/"_static/css/home-css/").glob("vars*.css")
] + [
     'css/css/'+str(file.name) for file in (Path(__file__).parents[0]/"_static/css/css/").glob("*.css")
] + [
    "css/veux.css",
]
html_additional_pages = {'index': 'home.html'}
g = "https://gallery.stairlab.io"
html_context = {
    "description": description,
    "examples": [
    ],
    **globals()
}
html_show_sphinx = False
html_show_sourcelink = False
html_theme_options = {
    "github_url": f"https://github.com/stairlab/{project}",
#   "footer_items": [], #["copyright", "sphinx-version"],
       "logo": {
        #   "text": "veux",
        "alt_text": "Veux Documentation - Home",
        "image_light": "_static/images/veux.svg",
        "image_dark":  "_static/images/veux.svg",
       }
}

autodoc_member_order = 'bysource'


html_static_path = ["_static"]

def _add_examples(app, pagename, templatename, context, doctree):
    if templatename == "home.html":
        context["home_image"] = "_static/images/girder-light.png"
        context["examples"] = [
            {"title": "Basics",      "link": f"{g}/examples/example6/",     "image": "../_static/images/gallery/Example6.png", "description": "Learn the basics of drawing models."},
            {"title": "Frames",      "link": f"{g}/examples/portal-moments/",     "image": "../_static/images/gallery/moments.png", "description": "Render structural models with extruded sections."},
#           {"title": "Sections",    "link": f"{g}/examples/framesections/",     "image": "../_static/images/gallery/Torsion.png", "description": "Detailed analysis of structural cross sections."},
            {"title": "Detailing",   "link": f"{g}/examples/example7/",     "image": "../_static/images/gallery/ShellFrame.png", "description": "."},
            {"title": "Finite Rotations",  "link": f"{g}/examples/framecircle/",  "image": "../_static/images/gallery/ShellCircle-576x324.webp", "description": "Render finite deformations in constrained members like Cosserat rods and shells."},
            {"title": "Versatility",     "link": f"{g}/examples/cablestayed/",  "image": "../_static/images/gallery/CableStayed02-576x324.webp", "description": "Import models from commercial platforms like ABAQUS."},
#           {"title": "Motions",     "link": f"{g}/examples/framehelix/",  "image": "../_static/images/gallery/sign-light-2800x2558.webp", "description": "Coming soon."},
#           {"title": "Interoperability", "link": f"{g}/examples/cablestayed/",  "image": "../_static/images/gallery/CableStayed02-576x324.webp", "description": "Coming soon."},
        ]

def _add_css(app, pagename, templatename, context, doctree):
    if pagename == "dontaddonthispage":
        return

    app.add_css_file("veux.css")

def setup(app):
    app.connect("html-page-context", _add_css)
    app.connect("html-page-context", _add_examples)

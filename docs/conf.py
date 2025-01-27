# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
from pathlib import Path
project = 'veux'
copyright = '2025, STAIRLab'
author = 'Claudio Perez'
description = "Portable, GPU accelerated, finite element processing and visualization of exact deformations."
version = '0.0.6'
release = '0.0.6'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    # 'autoapi.extension',
    'myst_parser',
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
html_baseurl = "https://veux.stairlab.io/"
html_title = project
html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_favicon = './_static/images/favicon.ico'
html_css_files = [
    "css/peer.css",
] + [
    'css/home-css/'+str(file.name) for file in (Path(__file__).parents[0]/"_static/css/home-css/").glob("vars*.css")
] + [
     'css/css/'+str(file.name) for file in (Path(__file__).parents[0]/"_static/css/css/").glob("*.css")
] + [
     'css/theme-css/'+str(file.name) for file in (Path(__file__).parents[0]/"_static/css/theme-css/").glob("*.css")
]
html_additional_pages = {'index': 'home.html'}
g = "https://gallery.stairlab.io"
html_context = {
    'description': description,
    'examples': [
        {"title": "Basics",      "link": f"{g}/examples/example6/",     "image": "../_static/images/gallery/Example6.png", "description": "Learn the basics of drawing models."},
        {"title": "Frames",      "link": f"{g}/examples/example5/",     "image": "../_static/images/gallery/Torsion.png", "description": "Comming soon."},
        {"title": "Sections",    "link": f"{g}/examples/framesections/",     "image": "../_static/images/gallery/HaywardSmall.png", "description": "Comming soon."},
        {"title": "Detailing",   "link": f"{g}/examples/example7/",     "image": "../_static/images/gallery/safeway.png", "description": "Comming soon."},
        {"title": "Motions",     "link": f"{g}/examples/framehockle/",  "image": "../_static/images/gallery/sign-light-2800x2558.webp", "description": "Comming soon."},
        {"title": "Interoperability", "link": f"{g}/examples/cablestayed/",  "image": "../_static/images/gallery/CableStayed02-576x324.webp", "description": "Coming soon."},
    ],
    **globals()
}
html_show_sphinx = False
html_show_sourcelink = False
html_theme_options = {
    "github_url": f"https://github.com/stairlab/{project}",
    "footer_items": [], #["copyright", "sphinx-version"],
}

autodoc_member_order = 'bysource'



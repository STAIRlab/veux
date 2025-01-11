# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
from pathlib import Path
project = 'veux'
copyright = '2024, STAIRLab'
author = 'Claudio Perez'
description = "Portable, GPU accelerated, finite element post-processing and visualization."
version = '0.0.5'
release = '0.0.5'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    # 'autoapi.extension',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages'
]


# autoapi_dirs = ['../src/mdof']


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


source_suffix = '.rst'
root_doc = 'index'
language = 'en'

# -- Options for HTML output -------------------------------------------------
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
        {"title": "Basics",         "link": f"{g}/examples/example7/",  "image": "../_static/images/gallery/safeway.png"},
        {"title": "Displacements",  "link": f"{g}/examples/example5/",  "image": "../_static/images/gallery/Example5.png"},
        {"title": "Motions",        "link": f"{g}/examples/example6/",  "image": "../_static/images/gallery/Example6.png"},
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



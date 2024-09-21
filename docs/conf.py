# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os

sys.path.insert(0, os.path.abspath('../src'))

import usbx

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'usbx'
copyright = '2024 Manuel Bleichenbacher'
author = 'Manuel Bl'
release = '0.8.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinxext.opengraph",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The master toctree document.
master_doc = "index"

# Open Graph metadata
ogp_title = "usbx documentation"
ogp_type = "website"
ogp_social_cards = {"image": "images/logo.png", "line_color": "#F09837"}
ogp_description = "usbx is a modern and user-friendly Python library for working with USB devices."


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "friendly"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ['_static']
html_favicon = "images/favicon.png"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_logo": "usbx.svg",
    "dark_logo": "usbx-dark.svg",
}

nitpicky = True

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

project = 'qmio'
copyright = '2024, Alvaro Caride, Javier Cacheiro'
author = 'Alvaro Caride, Javier Cacheiro'
extensions = [
    'sphinx.ext.autodoc',  # Para generar la documentación a partir de docstrings
    'sphinx.ext.napoleon',  # Opcional, para soporte de estilo Google y NumPy en docstrings
]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

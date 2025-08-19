import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'chaino'
copyright = '2025, Jang-Hyun Park'
author = 'Jang-Hyun Park'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
]

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# autodoc 설정
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
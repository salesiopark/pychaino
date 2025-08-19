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

# autodoc 설정 강화
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
    'exclude-members': '__weakref__'
}

# Mock imports for missing modules (MicroPython 관련)
autodoc_mock_imports = ['machine', 'binascii']

# Napoleon 설정 (Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
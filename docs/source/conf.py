"""Configuration file for the Sphinx documentation builder."""

# ruff: noqa: ARG001 # Allow unused function arguments

import re

# For the full list of built-in configuration values, see the
# documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'XBRL Filings API Documentation'
copyright = '2024, Lauri Salmela' # noqa: A001 # Ignore builtin shadow
author = 'Lauri Salmela'
release = '1.0'


# -- General configuration ---------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinxext.opengraph',
    'sphinx_copybutton',
    ]

templates_path = ['_templates']
exclude_patterns = []
default_role = 'any'


# -- Options for HTML output -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

trim_footnote_reference_space = True

rst_prolog = '''
.. role:: pt(code)
   :language: python
'''


# -- Settings for autodoc ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_class_signature = 'separated' # {'mixed', 'separated'}
# autodoc_mock_imports = ['django']
autodoc_default_options = {
    'member-order': 'bysource', # {'alphabetical', 'groupwise', 'bysource'}
    'class-doc-from': 'class', # {'class', 'both', 'init'}

    'members': None,
    'special-members': '__str__, __repr__, __hash__',
    'imported-members': None,
    'show-inheritance': None,
    # 'inherited-members': None,
    # 'private-members': None,
    # 'undoc-members': None,
    # 'ignore-module-all': None,
    # 'exclude-members': None,
    # 'no-value': None,
    }
autodoc_docstring_signature = False
# autodoc_mock_imports = ['requests']
autodoc_typehints = 'description'
    # Allowed: {'signature', 'description', 'none', 'both'}
autodoc_typehints_description_target = 'all'
    # Allowed: {'all', 'documented', 'documented_params'}
autodoc_type_aliases = {
    'DataAttributeType': 'xbrl_filings_api.options.DataAttributeType',
    'YearFilterMonthsType': 'xbrl_filings_api.options.YearFilterMonthsType',
    }
autodoc_typehints_format = 'short' # {'short', 'fully-qualified'}
autodoc_warningiserror = True
autodoc_inherit_docstrings = True
# suppress_warnings = [autodoc, autodoc.import_object]

name_re = re.compile(r'[^\.]*$')
def autodoc_skip_member(app, what, fullname, obj, would_skip, options):
    """
    Skip __init__ always.

    This event messes up autosummary member lists (magically starts to
    list all private members). This has been manually corrected in
    autosummary templates by excluding underscore-prefixed ones except
    ``autodoc_default_options['special-members']``. See
    ``sort_dunders_last()``.
    """
    if would_skip:
        return would_skip
    name_match = name_re.search(fullname)
    if name_match is None:
        return False
    return name_match[0] == '__init__'


# -- Settings for autosummary ------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html

retain_special_members = autodoc_default_options['special-members'].split(', ')
def sort_dunders_last(items):
    """Sort dunder members after other members."""
    # Filter due to bug in autosummary with autodoc-skip-member event
    items = filter(
        lambda item: (
            not item.startswith('_') or item in retain_special_members),
        items
        )
    return sorted(items, key=lambda item: item.startswith('__'))

autosummary_context = {
    # See autodoc_skip_member docstring
    'sort_dunders_last': sort_dunders_last
    }
autosummary_generate = True
autosummary_generate_overwrite = True
# autosummary_mock_imports = autodoc_mock_imports
autosummary_imported_members = True
autosummary_ignore_module_all = False
# autosummary_filename_map = {'object name': 'filename'}


# -- Settings for napoleon ---------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = {
    'collection': ':term:`collection`',
    'iterable': ':term:`iterable`',
    'mapping': ':term:`mapping`',
    'NO_LIMIT': ':data:`~xbrl_filings_api.constants.NO_LIMIT`',
    'GET_ONLY_FILINGS': ':attr:`~xbrl_filings_api.ScopeFlag.GET_ONLY_FILINGS`',
    'path-like': ':term:`path-like`',
    'sequence': ':term:`sequence`',
}
napoleon_attr_annotations = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest', None),
    'pandas': ('https://pandas.pydata.org/docs', None),
    }

ogp_site_url = 'https://lsalmela.github.io/xbrl-filings-api/'

copybutton_exclude = '.linenos, .gp, .go'

# -- Function setup() --------------------------------------------------

# Parameter `app` is the application object
# sphinx.application.Sphinx
def setup(app):
    """Connect event handlers."""
    app.connect('autodoc-skip-member', autodoc_skip_member)

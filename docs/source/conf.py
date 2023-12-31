import cbcflow

extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "sphinx_tabs.tabs",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = [".rst"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "cbcflow"
copyright = "2022, Greg Ashton, Rhiannon Udall, et al."
author = "Greg Ashton, Rhiannon Udall, et al."

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
fullversion = cbcflow.__version__

# The short X.Y version.
version = cbcflow.__version__

# The full version, including alpha/beta/rc tags.
release = fullversion

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "requirements.txt"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "canonical_url": "",
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

numpydoc_show_class_members = False

# Multiversion options
# Whitelist pattern for tags (set to None to ignore all tags)
smv_tag_whitelist = r"^(1.*|0.3.12)$"

# Whitelist pattern for branches (set to None to ignore all branches)
smv_branch_whitelist = r"^master$"

# Whitelist pattern for remotes (set to None to use local branches only)
smv_remote_whitelist = None

# Format for versioned output directories inside the build directory
smv_outputdir_format = "{ref.name}"

# Determines whether remote or local git branches/tags are preferred if their output dirs conflict
smv_prefer_remote_refs = False

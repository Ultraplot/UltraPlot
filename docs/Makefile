# Minimal makefile for Sphinx documentation
# You can set these variables from the command line.
# WARNING: Sphinx 2.0 fails with numpydoc style strings so far!
# See issue: https://github.com/readthedocs/sphinx_rtd_theme/issues/750
# BUILDDIR    = ../../ultraplot-doc # from gh-pages workflow
SPHINXOPTS  =
SPHINXBUILD = sphinx-build
SPHINXPROJ  = UltraPlot
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: help clean html html-exec Makefile

html:
	@UPLT_DOCS_EXECUTE=$${UPLT_DOCS_EXECUTE:-auto} $(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

html-exec:
	@UPLT_DOCS_EXECUTE=always $(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" -E -a $(SPHINXOPTS)

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

# Full reset of all build output and caches (gallery md5, executed notebooks,
# doctrees). Use this only when you need a genuinely cold rebuild; plain
# `make html` reuses cached figures and notebook outputs.
clean:
	rm -rf api/*
	rm -rf "$(BUILDDIR)"
	rm -rf gallery
	rm -rf sg_execution_times.rst

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option. See: https://github.com/sphinx-doc/sphinx/issues/6603
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

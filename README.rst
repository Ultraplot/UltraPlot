.. image:: UltraPlotLogo.svg
   :width: 100%

|build-status| |docs| |pypi| |code-style| |pr-welcome| |license| |gitter| |doi|

A succinct `matplotlib <https://matplotlib.org/>`__ wrapper for making beautiful,
publication-quality graphics. It builds upon Proplot and transports it into the modern age (supporting mpl 3.9.0+).

Under construction
==================
Please bear with us as we work to bring the full functionality of Proplot to UltraPlot. We are working to bring the full functionality of Proplot to UltraPlot, and we are working to make the transition as smooth as possible.

Documentation
=============

The documentation is `published on readthedocs <https://proplot.readthedocs.io>`__.

Installation
============

Proplot is published on `PyPi <https://pypi.org/project/proplot/>`__ and
`conda-forge <https://conda-forge.org>`__. It can be installed with ``pip`` or
``conda`` as follows:

.. code-block:: bash

   pip install ultraplot
   conda install -c conda-forge ultraplot

Likewise, an existing installation of proplot can be upgraded
to the latest version with:

.. code-block:: bash

   pip install --upgrade ultraplot
   conda upgrade ultraplot

To install a development version of proplot, you can use
``pip install git+https://github.com/ultraplot-dev/ultraplot.git``
or clone the repository and run ``pip install -e .``
inside the ``ultraplot`` folder.


.. |build-status| image:: https://travis-ci.com/ultraplot/ultraplot.svg?branch=main
   :alt: build status
   :target: https://app.travis-ci.com/ultraplot/ultraplot

.. |docs| image:: https://readthedocs.org/projects/ultraplot/badge/?version=latest
   :alt: docs
   :target: https://ultraplot.readthedocs.io/en/latest/?badge=latest

.. |pypi| image:: https://img.shields.io/pypi/v/ultrplot?color=83%20197%2052
   :alt: pypi
   :target: https://pypi.org/project/ultraplot/

.. |pr-welcome| image:: https://img.shields.io/badge/PR-Welcome-green.svg?
   :alt: PR welcome
   :target: https://git-scm.com/book/en/v2/GitHub-Contributing-to-a-Project

.. |license| image:: https://img.shields.io/github/license/ultraplot/ultraplot.svg
   :alt: license
   :target: LICENSE.txt

..
   |code-style| image:: https://img.shields.io/badge/code%20style-pep8-green.svg
   :alt: pep8
   :target: https://www.python.org/dev/peps/pep-0008/

..
   |coverage| image:: https://codecov.io/gh/ultraplot/ultraplot/branch/master/graph/badge.svg
   :alt: coverage
   :target: https://codecov.io/gh/ultraplot/ultraplot

..
   |quality| image:: https://api.codacy.com/project/badge/Grade/931d7467c69c40fbb1e97a11d092f9cd
   :alt: quality
   :target: https://www.codacy.com/app/proplot-dev/proplot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ultraplot/ultraplot&amp;utm_campaign=Badge_Grade

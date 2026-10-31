.. _mcp_install:

MCP server installation
=======================

UltraPlot includes a Model Context Protocol (MCP) server that lets AI assistants
search documentation and examples, inspect the live Python API, and read source
code and release notes.

Run directly with uvx
---------------------

With `uv <https://docs.astral.sh/uv/getting-started/installation/>`__ installed,
your MCP client can launch the server with ``uvx``. uv installs the package and
its dependencies in an isolated environment automatically, so you do not need
to create a virtual environment or install UltraPlot separately.

For a PyPI release containing the MCP server, the launch command is:

.. code-block:: bash

   uvx --from 'ultraplot[mcp]' ultraplot-mcp

For clients that use an ``mcpServers`` configuration, add:

.. code-block:: json

   {
     "mcpServers": {
       "ultraplot": {
         "command": "uvx",
         "args": ["--from", "ultraplot[mcp]", "ultraplot-mcp"]
       }
     }
   }

The client starts the server when needed and communicates with it over stdio.
Other clients may use a different configuration format; use the same command
and arguments. ``uvx`` is equivalent to ``uv tool run``.

Until the MCP server is released on PyPI, run it directly from the feature
branch instead:

.. code-block:: bash

   uvx --from 'ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp' ultraplot-mcp

For this development version, replace ``ultraplot[mcp]`` in the client
configuration with
``ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp``.

Install persistently with uv
----------------------------

Alternatively, keep the executable on your ``PATH`` by installing it as a uv
tool. For a PyPI release containing the MCP server:

.. code-block:: bash

   uv tool install 'ultraplot[mcp]'
   ultraplot-mcp --help

Before that release, install from the feature branch:

.. code-block:: bash

   uv tool install 'ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp'

Then configure your client to launch ``ultraplot-mcp`` with no arguments.
If uv reports that its executable directory is missing from ``PATH``, run
``uv tool update-shell`` and restart your shell.

Install from a checkout
-----------------------

From a checkout containing the MCP implementation, install the optional ``mcp``
extra in the Python environment you want the server to use:

.. code-block:: bash

   pip install -e '.[mcp]'

Connect an MCP client
---------------------

After installing persistently with uv or pip, register the server with an
installed Codex CLI:

.. code-block:: bash

   ultraplot-mcp install codex

Restart Codex after registration. Try asking it to search the UltraPlot
examples for shared colorbars or inspect ``ultraplot.subplots``.

For other MCP clients, configure a stdio server with ``ultraplot-mcp`` as the
command and no arguments. Use the executable's absolute path if the client does
not inherit your Python environment's ``PATH``. Running ``ultraplot-mcp`` starts
the server; ``ultraplot-mcp --help`` lists the available commands.

Documentation tools read the checkout's ``docs`` directory. Direct uvx and uv
tool installations require a separate documentation checkout for these tools.
If documentation lives elsewhere, set ``ULTRAPLOT_MCP_DOCS`` to its absolute path in the MCP
client's server environment. Documentation is not currently bundled in the
Python package; API and source inspection use the installed UltraPlot version.

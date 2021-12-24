Ignis
=====
Ignis is a library for interacting with Flair devices (such as vents, pucks, minisplits, etc.)

Usage
-----
A synchronous wrapper is planned, but is not yet implemented, so for the time being the builtin ``asyncio`` library must be used to properly use the coroutines.

Example:

.. code-block:: python
    
    from ignis.ignis import Ignis
    from ignis.entities import Vent

    async def main():
        i = Ignis("IDENT", "TOKEN", lazy_mode = False)

        vent1 = Vent(i, "patio-cottage")
        await vent1.toggle()

Planned Features
----------------
See `TODO.rst <https://github.com/insertdead/ignis/blob/master/TODO.rst>`_

Development
--------
To install dependencies, first make sure ``poetry`` is installed and on your PATH.

.. code-block:: sh

          $ poetry install
          $ poetry shell

Due to the nature of APIs and the way the library is tested, you must provide your own API key and identification as environment variables or in ``.envvars.sh`` (which be be loaded on git commit)

Testing
~~~~~~~
Ignis uses ``pytest`` for testing, and is run in CI on every commit

.. code-block:: sh

          $ poetry shell
          $ python -m pytest

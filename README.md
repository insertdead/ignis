# Ignis
Ignis is a library for interacting with Flair devices (such as vents, pucks, minisplits, etc.)

## Usage

The library must be used in an asynchronous context, otherwise it will raise a `RuntimeError`.

Example:
```python
from ignis.ignis import BasicConfig
from ignis.entities import Vent
from aiohttp import ClientSession

websession = ClientSession()

async def main():
    async with BasicConfig.create_config(websession, "IDENT", "TOKEN", lazy_mode = False) as config:
        vent1 = Vent(c, name="patio-cottage")
        await vent1.toggle()

asyncio.run(main)
```

## Planned Features
See [TODO.md](https://github.com/insertdead/ignis/blob/master/TODO.md)

## Development
To install dependencies, first make sure ``poetry`` is installed and on your PATH.

```sh
$ poetry install
$ poetry shell
```

Due to the nature of APIs and the way the library is tested, you must provide your own API key and identification as environment variables or in ``.envrc`` (which is loaded by direnv)

## Testing
Ignis uses ``pytest`` for testing, and is run in CI on every commit

```sh
$ poetry shell
$ python -m pytest
```

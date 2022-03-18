from ignis import __version__, utils


def test_version():
    assert __version__ == "0.1.0"


def test_credentials(credentials, legacy_credentials):
    assert credentials["client_id"], "$CLIENT_ID variable unset"
    assert credentials["client_secret"], "$CLIENT_SECRET variable unset"
    assert legacy_credentials["client_id"], "$LEGACY_CLIENT_ID variable unset"
    assert legacy_credentials["client_secret"], "$LEGACY_CLIENT_SECRET variable unset"


async def test_api_status(websession):
    url = await utils.create_url("/api/")
    headers = utils.DEFAULT_HEADERS
    resp = await websession.get(url, headers=headers)
    assert resp.status == 200, f"status code {resp.status} received from API"


async def test_auth(websession, config):
    vent_list: dict = await utils.get_list(websession, config.token, utils.Entities.VENT)
    assert type(vent_list) == dict, "Vent list returned is not a list!"

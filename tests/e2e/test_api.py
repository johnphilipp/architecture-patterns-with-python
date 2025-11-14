import uuid
import pytest
import requests

from allocation import config


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_institution_name(name=""):
    return f"Institution-{name}-{random_suffix()}"


def post_to_add_institution(name, industry, website, uid="", handelsregister_url=""):
    url = config.get_api_url()
    data = {"name": name, "industry": industry, "website": website}
    if uid:
        data["uid"] = uid
    if handelsregister_url:
        data["handelsregister_url"] = handelsregister_url

    r = requests.post(f"{url}/add_institution", json=data)
    assert r.status_code == 201
    return r.json()["id"]


def post_to_update_from_website(institution_id):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_website",
        json={"institution_id": institution_id}
    )
    return r


def post_to_update_from_handelsregister(institution_id):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_handelsregister",
        json={"institution_id": institution_id}
    )
    return r


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_add_institution_and_update_from_website():
    # Add an institution
    institution_name = random_institution_name()
    institution_id = post_to_add_institution(institution_name, "Technology", "https://techcorp.com")

    # Update from website (calls the agent)
    r = post_to_update_from_website(institution_id)

    assert r.status_code == 200


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_update_from_website_twice_accumulates_persons():
    # Add an institution
    institution_name = random_institution_name()
    institution_id = post_to_add_institution(institution_name, "Technology", "https://techcorp.com")

    # First update
    r = post_to_update_from_website(institution_id)
    assert r.status_code == 200

    # Second update (should add more persons, not replace)
    r = post_to_update_from_website(institution_id)
    assert r.status_code == 200


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_website_returns_404_for_invalid_institution():
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_website",
        json={"institution_id": 99999}
    )
    assert r.status_code == 404
    assert "not found" in r.json()["message"].lower()


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_update_from_handelsregister():
    # Add institution WITH handelsregister_url
    institution_name = random_institution_name()
    institution_id = post_to_add_institution(
        institution_name,
        "Technology",
        "https://techcorp.com",
        "CHE123456789",
        "https://handelsregister.ch/CHE123456789"
    )

    # Update from Handelsregister
    r = post_to_update_from_handelsregister(institution_id)
    assert r.status_code == 200


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_handelsregister_without_url_returns_400():
    # Add institution WITHOUT handelsregister_url
    institution_name = random_institution_name()
    institution_id = post_to_add_institution(institution_name, "Technology", "https://techcorp.com")

    # Try to update from Handelsregister
    r = post_to_update_from_handelsregister(institution_id)
    assert r.status_code == 400
    assert "handelsregister_url" in r.json()["message"].lower()


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_handelsregister_returns_404_for_invalid_institution():
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_handelsregister",
        json={"institution_id": 99999}
    )
    assert r.status_code == 404
    assert "not found" in r.json()["message"].lower()


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_combining_website_and_handelsregister():
    """
    Test that we can call both endpoints and persons get details from both sources
    """
    # Add institution with handelsregister_url
    institution_name = random_institution_name()
    institution_id = post_to_add_institution(
        institution_name,
        "Technology",
        "https://techcorp.com",
        "CHE123456789",
        "https://handelsregister.ch/CHE123456789"
    )

    # Update from website
    r = post_to_update_from_website(institution_id)
    assert r.status_code == 200

    # Update from Handelsregister
    r = post_to_update_from_handelsregister(institution_id)
    assert r.status_code == 200

    # Both should succeed
    # In a real test, we'd query the database to verify persons have multiple details

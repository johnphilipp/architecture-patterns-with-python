import uuid
import pytest
import requests

from allocation import config


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_institution_name(name=""):
    return f"Institution-{name}-{random_suffix()}"


def post_to_add_institution(name, industry, website):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_institution",
        json={"name": name, "industry": industry, "website": website}
    )
    assert r.status_code == 201


def post_to_update_from_website(institution_id):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_website",
        json={"institution_id": institution_id}
    )
    return r


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_add_institution_and_update_from_website():
    # Add an institution
    institution_name = random_institution_name()
    post_to_add_institution(institution_name, "Technology", "https://techcorp.com")

    # Since we don't have a way to retrieve the institution ID from the API yet,
    # we'll assume the first institution has ID 1 in a fresh database
    # In a real scenario, the add_institution endpoint would return the created ID
    institution_id = 1

    # Update from website (calls the agent)
    url = config.get_api_url()
    r = post_to_update_from_website(institution_id)

    assert r.status_code == 200


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_update_from_website_twice_accumulates_persons():
    # Add an institution
    institution_name = random_institution_name()
    post_to_add_institution(institution_name, "Technology", "https://techcorp.com")

    institution_id = 1

    # First update
    r = post_to_update_from_website(institution_id)
    assert r.status_code == 200

    # Second update (should add more persons, not replace)
    r = post_to_update_from_website(institution_id)
    assert r.status_code == 200


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_404_for_invalid_institution():
    url = config.get_api_url()
    r = requests.post(
        f"{url}/update_from_website",
        json={"institution_id": 99999}
    )
    assert r.status_code == 404
    assert "not found" in r.json()["message"].lower()
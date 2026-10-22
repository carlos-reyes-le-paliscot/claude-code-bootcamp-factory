import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import ItemCreate
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def _create_item_for(
    db: Session, email: str, title: str, description: str | None
) -> None:
    user = crud.get_user_by_email(session=db, email=email)
    assert user is not None
    crud.create_item(
        session=db,
        item_in=ItemCreate(title=title, description=description),
        owner_id=user.id,
    )


def test_search_items_matches_title_or_description_ignoring_case(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    tag = random_lower_string()[:8]
    _create_item_for(db, settings.EMAIL_TEST_USER, f"Invoice {tag.upper()}", None)
    _create_item_for(db, settings.EMAIL_TEST_USER, "Receipt", f"about {tag}")
    _create_item_for(db, settings.EMAIL_TEST_USER, "Unrelated", "nothing here")

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        params={"q": tag},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    assert {i["title"] for i in content["data"]} == {
        f"Invoice {tag.upper()}",
        "Receipt",
    }


def test_search_items_never_returns_other_users_items(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    tag = random_lower_string()[:8]
    other = create_random_user(db)
    _create_item_for(db, other.email, f"secret {tag}", None)

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        params={"q": tag},
    )
    assert response.status_code == 200
    assert response.json() == {"data": [], "count": 0}


def test_search_items_superuser_searches_all_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    tag = random_lower_string()[:8]
    other = create_random_user(db)
    _create_item_for(db, other.email, f"shared {tag}", None)

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        params={"q": tag},
    )
    assert response.status_code == 200
    assert [i["title"] for i in response.json()["data"]] == [f"shared {tag}"]


def test_search_items_treats_wildcards_literally(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    tag = random_lower_string()[:8]
    _create_item_for(db, settings.EMAIL_TEST_USER, f"100% {tag}", None)
    _create_item_for(db, settings.EMAIL_TEST_USER, f"1000 {tag}", None)

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        params={"q": f"100% {tag}"},
    )
    assert [i["title"] for i in response.json()["data"]] == [f"100% {tag}"]


def test_search_items_empty_q_lists_everything(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    url = f"{settings.API_V1_STR}/items/"
    unfiltered = client.get(url, headers=normal_user_token_headers).json()
    blank = client.get(
        url, headers=normal_user_token_headers, params={"q": "  "}
    ).json()
    assert blank == unfiltered


def test_search_items_rejects_overlong_q(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        params={"q": "x" * 101},
    )
    assert response.status_code == 422

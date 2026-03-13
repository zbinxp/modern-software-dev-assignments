def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["ok"] is True
    assert item["data"]["completed"] is False

    r = client.put(f"/action-items/{item['data']['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["ok"] is True
    assert done["data"]["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert items["ok"] is True
    assert len(items["data"]) == 1


def test_action_items_without_trailing_slash_returns_json(client):
    """Test that /action-items (without trailing slash) returns JSON, not HTML."""
    # TestClient follows redirects by default, so we get the final response
    r = client.get("/action-items")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.headers["content-type"].startswith("application/json"), \
        f"Expected JSON, got {r.headers.get('content-type')}: {r.text[:100]}"
    # Should be an envelope with data list
    data = r.json()
    assert data["ok"] is True
    assert "data" in data
    assert isinstance(data["data"], list), "Expected JSON array in data"


def test_filter_completed_true(client):
    """Filter returns only completed items."""
    # Create two items, complete one
    r = client.post("/action-items/", json={"description": "Item 1"})
    assert r.status_code == 201
    item1 = r.json()

    r = client.post("/action-items/", json={"description": "Item 2"})
    assert r.status_code == 201
    item2 = r.json()

    # Complete one item
    client.put(f"/action-items/{item1['data']['id']}/complete")

    # Filter by completed=true
    r = client.get("/action-items/?completed=true")
    assert r.status_code == 200
    items = r.json()
    assert len(items["data"]) == 1
    assert items["data"][0]["completed"] is True
    assert items["data"][0]["description"] == "Item 1"


def test_filter_completed_false(client):
    """Filter returns only incomplete items."""
    # Create two items, complete one
    r = client.post("/action-items/", json={"description": "Item 1"})
    assert r.status_code == 201
    item1 = r.json()

    r = client.post("/action-items/", json={"description": "Item 2"})
    assert r.status_code == 201
    item2 = r.json()

    # Complete one item
    client.put(f"/action-items/{item1['data']['id']}/complete")

    # Filter by completed=false
    r = client.get("/action-items/?completed=false")
    assert r.status_code == 200
    items = r.json()
    assert len(items["data"]) == 1
    assert items["data"][0]["completed"] is False
    assert items["data"][0]["description"] == "Item 2"


def test_bulk_complete_success(client):
    """Bulk complete marks items as complete."""
    # Create multiple items
    r = client.post("/action-items/", json={"description": "Item 1"})
    item1 = r.json()
    r = client.post("/action-items/", json={"description": "Item 2"})
    item2 = r.json()
    r = client.post("/action-items/", json={"description": "Item 3"})
    item3 = r.json()

    # Bulk complete items 1 and 2
    r = client.post("/action-items/bulk-complete", json={"ids": [item1["data"]["id"], item2["data"]["id"]]})
    assert r.status_code == 200
    completed = r.json()
    assert completed["ok"] is True
    assert len(completed["data"]) == 2
    assert all(item["completed"] is True for item in completed["data"])

    # Verify item 3 is still incomplete
    r = client.get("/action-items/")
    items = r.json()
    item3_data = next(i for i in items["data"] if i["id"] == item3["data"]["id"])
    assert item3_data["completed"] is False


def test_bulk_complete_with_invalid_id(client):
    """404 error for invalid ID."""
    # Try to bulk complete with non-existent ID
    r = client.post("/action-items/bulk-complete", json={"ids": [9999]})
    assert r.status_code == 404
    data = r.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_bulk_complete_transaction_rollback(client):
    """Transaction rolls back on error."""
    from unittest.mock import patch
    from sqlalchemy.exc import SQLAlchemyError

    # Create two items
    r = client.post("/action-items/", json={"description": "Item 1"})
    item1 = r.json()
    r = client.post("/action-items/", json={"description": "Item 2"})
    item2 = r.json()

    # Verify both start as incomplete
    assert item1["data"]["completed"] is False
    assert item2["data"]["completed"] is False

    # Get the session from the app's dependency overrides to mock commit
    from backend.app.main import app
    from backend.app.db import get_db

    # Find the override and patch its commit
    override_func = app.dependency_overrides.get(get_db)

    # Test that bulk complete with a mocked commit failure returns 500
    # We do this by patching at a lower level
    with patch('sqlalchemy.orm.Session.commit', side_effect=SQLAlchemyError("Simulated commit error")):
        r = client.post("/action-items/bulk-complete", json={"ids": [item1["data"]["id"], item2["data"]["id"]]})
        assert r.status_code == 500
        data = r.json()
        assert data["ok"] is False
        assert "rolled back" in data["error"]["message"]


# Envelope format tests
def test_create_action_item_returns_envelope(client):
    """Test create action item returns envelope format."""
    payload = {"description": "Test item"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["ok"] is True
    assert "data" in data
    assert data["data"]["description"] == "Test item"


def test_complete_nonexistent_action_item_returns_error_envelope(client):
    """Test complete nonexistent action item returns error envelope."""
    r = client.put("/action-items/99999/complete")
    assert r.status_code == 404
    data = r.json()
    assert data["ok"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_create_action_item_with_empty_description_returns_validation_error(client):
    """Test create action item with empty description returns validation error."""
    payload = {"description": ""}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 422
    data = r.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_list_action_items_returns_envelope(client):
    """Test list action items returns envelope format."""
    r = client.get("/action-items/")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "data" in data
    assert isinstance(data["data"], list)

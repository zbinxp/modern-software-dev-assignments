def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1


def test_action_items_without_trailing_slash_returns_json(client):
    """Test that /action-items (without trailing slash) returns JSON, not HTML."""
    # TestClient follows redirects by default, so we get the final response
    r = client.get("/action-items")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.headers["content-type"].startswith("application/json"), \
        f"Expected JSON, got {r.headers.get('content-type')}: {r.text[:100]}"
    # Should be a list of action items
    assert isinstance(r.json(), list), "Expected JSON array"


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
    client.put(f"/action-items/{item1['id']}/complete")

    # Filter by completed=true
    r = client.get("/action-items/?completed=true")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["completed"] is True
    assert items[0]["description"] == "Item 1"


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
    client.put(f"/action-items/{item1['id']}/complete")

    # Filter by completed=false
    r = client.get("/action-items/?completed=false")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["completed"] is False
    assert items[0]["description"] == "Item 2"


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
    r = client.post("/action-items/bulk-complete", json={"ids": [item1["id"], item2["id"]]})
    assert r.status_code == 200
    completed = r.json()
    assert len(completed) == 2
    assert all(item["completed"] is True for item in completed)

    # Verify item 3 is still incomplete
    r = client.get("/action-items/")
    items = r.json()
    item3_data = next(i for i in items if i["id"] == item3["id"])
    assert item3_data["completed"] is False


def test_bulk_complete_with_invalid_id(client):
    """404 error for invalid ID."""
    # Try to bulk complete with non-existent ID
    r = client.post("/action-items/bulk-complete", json={"ids": [9999]})
    assert r.status_code == 404
    assert "9999" in r.json()["detail"]


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
    assert item1["completed"] is False
    assert item2["completed"] is False

    # Get the session from the app's dependency overrides to mock commit
    from backend.app.main import app
    from backend.app.db import get_db

    # Find the override and patch its commit
    override_func = app.dependency_overrides.get(get_db)

    # Test that bulk complete with a mocked commit failure returns 500
    # We do this by patching at a lower level
    with patch('sqlalchemy.orm.Session.commit', side_effect=SQLAlchemyError("Simulated commit error")):
        r = client.post("/action-items/bulk-complete", json={"ids": [item1["id"], item2["id"]]})
        assert r.status_code == 500
        assert "rolled back" in r.json()["detail"]

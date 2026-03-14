def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"


def test_sort_parameter_sql_injection(client):
    """Test that SQL injection via sort parameter is prevented."""
    # Attempt SQL injection through sort parameter - should be sanitized
    r = client.get("/action-items/", params={"sort": "id); DROP TABLE action_items;--"})
    # The server should either reject this or sanitize it, not execute arbitrary SQL
    assert r.status_code == 200  # Should still return 200 but use safe default

    # Attempt to access non-existent column via injection
    r = client.get("/action-items/", params={"sort": "id, (SELECT * FROM users)"})
    assert r.status_code == 200  # Should use safe default

    # Valid sort should work
    r = client.get("/action-items/", params={"sort": "created_at"})
    assert r.status_code == 200

    r = client.get("/action-items/", params={"sort": "-description"})
    assert r.status_code == 200
def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


def test_delete_note(client):
    # Create a note
    payload = {"title": "To Delete", "content": "This will be deleted"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    # Delete the note
    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204, r.text

    # Verify note is gone
    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404


def test_delete_nonexistent_note(client):
    r = client.delete("/notes/99999")
    assert r.status_code == 404


def test_validation_empty_title(client):
    payload = {"title": "", "content": "Some content"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 422


def test_validation_empty_content(client):
    payload = {"title": "Some title", "content": ""}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 422


def test_validation_title_too_long(client):
    payload = {"title": "x" * 201, "content": "Some content"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 422


def test_validation_patch_empty_title(client):
    # Create a note first
    payload = {"title": "Valid title", "content": "Valid content"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201
    note_id = r.json()["id"]

    # Try to patch with empty title
    r = client.patch(f"/notes/{note_id}", json={"title": ""})
    assert r.status_code == 422



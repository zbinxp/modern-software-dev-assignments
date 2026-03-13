import pytest


@pytest.fixture
def sample_note(client):
    """Create a sample note for testing."""
    response = client.post("/notes/", json={"title": "Test Note", "content": "Test content"})
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture
def sample_tags(client):
    """Create sample tags for testing."""
    tag1 = client.post("/tags/", json={"name": "work"})
    tag2 = client.post("/tags/", json={"name": "personal"})
    tag3 = client.post("/tags/", json={"name": "urgent"})
    return [tag1.json()["data"], tag2.json()["data"], tag3.json()["data"]]


class TestTags:
    """Tests for tag CRUD operations."""

    def test_list_tags_empty(self, client):
        """Test listing tags when none exist."""
        response = client.get("/tags/")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"] == []

    def test_create_tag(self, client):
        """Test creating a new tag."""
        response = client.post("/tags/", json={"name": "important"})
        assert response.status_code == 201
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["name"] == "important"
        assert "id" in data["data"]

    def test_create_tag_duplicate(self, client):
        """Test creating a duplicate tag fails."""
        client.post("/tags/", json={"name": "duplicate"})
        response = client.post("/tags/", json={"name": "duplicate"})
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "already exists" in data["error"]["message"]

    def test_list_tags(self, client, sample_tags):
        """Test listing all tags."""
        response = client.get("/tags/")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        tags = data["data"]
        assert len(tags) == 3
        # Should be ordered by name
        assert tags[0]["name"] == "personal"
        assert tags[1]["name"] == "urgent"
        assert tags[2]["name"] == "work"

    def test_delete_tag(self, client, sample_tags):
        """Test deleting a tag."""
        tag_id = sample_tags[0]["id"]
        response = client.delete(f"/tags/{tag_id}")
        assert response.status_code == 204

        # Verify tag is deleted
        response = client.get("/tags/")
        data = response.json()
        assert len(data["data"]) == 2

    def test_delete_nonexistent_tag(self, client):
        """Test deleting a non-existent tag fails."""
        response = client.delete("/tags/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"


class TestNoteTags:
    """Tests for note-tag many-to-many relationship."""

    def test_attach_tags_to_note(self, client, sample_note, sample_tags):
        """Test attaching tags to a note."""
        note_id = sample_note["id"]
        tag_ids = [sample_tags[0]["id"], sample_tags[1]["id"]]

        response = client.post(f"/notes/{note_id}/tags", json={"tag_ids": tag_ids})
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        note_data = data["data"]
        assert len(note_data["tags"]) == 2
        tag_names = [t["name"] for t in note_data["tags"]]
        assert "work" in tag_names
        assert "personal" in tag_names

    def test_attach_nonexistent_tag(self, client, sample_note):
        """Test attaching a non-existent tag fails."""
        response = client.post(f"/notes/{sample_note['id']}/tags", json={"tag_ids": [99999]})
        assert response.status_code == 404
        data = response.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_detach_tag_from_note(self, client, sample_note, sample_tags):
        """Test detaching a tag from a note."""
        note_id = sample_note["id"]
        tag_id = sample_tags[0]["id"]

        # First attach the tag
        client.post(f"/notes/{note_id}/tags", json={"tag_ids": [tag_id]})

        # Then detach it
        response = client.delete(f"/notes/{note_id}/tags/{tag_id}")
        assert response.status_code == 204

        # Verify tag is detached
        response = client.get(f"/notes/{note_id}")
        data = response.json()
        assert len(data["data"].get("tags", [])) == 0

    def test_get_notes_by_tag(self, client, sample_note, sample_tags):
        """Test getting notes filtered by tag."""
        note_id = sample_note["id"]
        tag_id = sample_tags[0]["id"]

        # Attach tag to note
        client.post(f"/notes/{note_id}/tags", json={"tag_ids": [tag_id]})

        # Get notes by tag
        response = client.get(f"/notes/by-tag/{tag_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == note_id

    def test_get_notes_by_nonexistent_tag(self, client):
        """Test getting notes by non-existent tag fails."""
        response = client.get("/notes/by-tag/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_note_with_tags_search(self, client, sample_note, sample_tags):
        """Test that search returns notes with their tags."""
        note_id = sample_note["id"]
        tag_id = sample_tags[0]["id"]

        # Attach tag
        client.post(f"/notes/{note_id}/tags", json={"tag_ids": [tag_id]})

        # Search should include tags in response
        response = client.get(f"/notes/search/?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["data"]["items"]) == 1

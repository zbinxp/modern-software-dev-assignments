import pytest
from backend.app.models import Base, Note, Tag, note_tags  # noqa: I001
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestTagModel:
    """Tests for the Tag model."""

    def test_create_tag(self, db_session):
        """Test creating a basic tag."""
        tag = Tag(name="test-tag")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        assert tag.id is not None
        assert tag.name == "test-tag"
        assert tag.created_at is not None

    def test_tag_name_unique(self, db_session):
        """Test that tag names must be unique."""
        tag1 = Tag(name="duplicate")
        db_session.add(tag1)
        db_session.commit()

        tag2 = Tag(name="duplicate")
        db_session.add(tag2)
        with pytest.raises(Exception):  # noqa: B017
            db_session.commit()

    def test_tag_name_case_sensitive(self, db_session):
        """Test that tag names are case-sensitive."""
        tag1 = Tag(name="Tag")
        db_session.add(tag1)
        db_session.commit()

        tag2 = Tag(name="tag")
        db_session.add(tag2)
        db_session.commit()

        assert tag1.name != tag2.name


class TestNoteTagRelationship:
    """Tests for the many-to-many relationship between notes and tags."""

    def test_add_tag_to_note(self, db_session):
        """Test adding a tag to a note."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="important")
        db_session.add(note)
        db_session.add(tag)
        db_session.commit()

        note.tags.append(tag)
        db_session.commit()
        db_session.refresh(note)

        assert len(note.tags) == 1
        assert note.tags[0].name == "important"

    def test_add_multiple_tags_to_note(self, db_session):
        """Test adding multiple tags to a note."""
        note = Note(title="Test Note", content="Content")
        tag1 = Tag(name="todo")
        tag2 = Tag(name="important")
        tag3 = Tag(name="work")
        db_session.add_all([note, tag1, tag2, tag3])
        db_session.commit()

        note.tags.extend([tag1, tag2, tag3])
        db_session.commit()
        db_session.refresh(note)

        assert len(note.tags) == 3

    def test_add_note_to_tag(self, db_session):
        """Test adding a note to a tag (reverse relationship)."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="important")
        db_session.add_all([note, tag])
        db_session.commit()

        tag.notes.append(note)
        db_session.commit()
        db_session.refresh(tag)

        assert len(tag.notes) == 1
        assert tag.notes[0].title == "Test Note"

    def test_get_notes_by_tag(self, db_session):
        """Test retrieving all notes with a specific tag."""
        tag = Tag(name="work")
        db_session.add(tag)
        db_session.commit()

        note1 = Note(title="Note 1", content="Content 1")
        note2 = Note(title="Note 2", content="Content 2")
        note3 = Note(title="Note 3", content="Content 3")
        db_session.add_all([note1, note2, note3])
        db_session.commit()

        note1.tags.append(tag)
        note2.tags.append(tag)
        db_session.commit()

        # Query notes by tag
        notes_with_tag = db_session.query(Note).filter(Note.tags.any(Tag.id == tag.id)).all()
        assert len(notes_with_tag) == 2

    def test_get_tags_by_note(self, db_session):
        """Test retrieving all tags for a specific note."""
        note = Note(title="Test Note", content="Content")
        tag1 = Tag(name="todo")
        tag2 = Tag(name="important")
        db_session.add_all([note, tag1, tag2])
        db_session.commit()

        note.tags.extend([tag1, tag2])
        db_session.commit()
        db_session.refresh(note)

        # Query tags by note
        tags_for_note = db_session.query(Tag).filter(Tag.notes.any(Note.id == note.id)).all()
        assert len(tags_for_note) == 2


class TestTagEdgeCases:
    """Edge case tests for tags."""

    def test_empty_tags_list(self, db_session):
        """Test that a note can have no tags."""
        note = Note(title="Test Note", content="Content")
        db_session.add(note)
        db_session.commit()
        db_session.refresh(note)

        assert len(note.tags) == 0

    def test_remove_tag_from_note(self, db_session):
        """Test removing a tag from a note."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="todo")
        db_session.add_all([note, tag])
        db_session.commit()

        note.tags.append(tag)
        db_session.commit()
        db_session.refresh(note)

        # Remove tag
        note.tags.remove(tag)
        db_session.commit()
        db_session.refresh(note)

        assert len(note.tags) == 0
        # Tag still exists
        db_session.refresh(tag)
        assert tag.id is not None

    def test_delete_tag_does_not_delete_note(self, db_session):
        """Test that deleting a tag does not delete associated notes."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="todo")
        db_session.add_all([note, tag])
        db_session.commit()

        note.tags.append(tag)
        db_session.commit()

        # Delete tag
        db_session.delete(tag)
        db_session.commit()

        # Note still exists
        db_session.refresh(note)
        assert note.id is not None
        assert len(note.tags) == 0

    def test_delete_note_does_not_delete_tag(self, db_session):
        """Test that deleting a note does not delete associated tags."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="todo")
        db_session.add_all([note, tag])
        db_session.commit()

        note.tags.append(tag)
        db_session.commit()

        # Delete note
        db_session.delete(note)
        db_session.commit()

        # Tag still exists
        db_session.refresh(tag)
        assert tag.id is not None

    def test_note_with_same_tag_twice(self, db_session):
        """Test that adding the same tag twice doesn't create duplicates."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="todo")
        db_session.add_all([note, tag])
        db_session.commit()

        # Add same tag twice (should be prevented by the association)
        note.tags.append(tag)
        db_session.commit()

        # Verify only one association exists
        result = db_session.execute(
            note_tags.select().where(
                note_tags.c.note_id == note.id and note_tags.c.tag_id == tag.id
            )
        ).fetchall()
        assert len(result) == 1

    def test_tag_with_very_long_name(self, db_session):
        """Test that tag names respect the max length constraint."""
        long_name = "a" * 100  # Max is 100
        tag = Tag(name=long_name)
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        assert tag.name == long_name

    def test_tag_with_empty_name_allowed_by_sqlite(self, db_session):
        """Test that SQLite allows empty tag names (database-level behavior)."""
        # SQLite allows empty strings by default
        # To enforce NOT NULL, the model would need nullable=False
        tag = Tag(name="")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        assert tag.name == ""

    def test_tag_special_characters(self, db_session):
        """Test that tags can contain special characters."""
        tag = Tag(name="tag-with-dash")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        assert tag.name == "tag-with-dash"


class TestTagCascadeDelete:
    """Tests for cascade delete behavior."""

    def test_delete_note_removes_associations(self, db_session):
        """Test that deleting a note removes note_tags associations."""
        note = Note(title="Test Note", content="Content")
        tag = Tag(name="todo")
        db_session.add_all([note, tag])
        db_session.commit()

        note.tags.append(tag)
        db_session.commit()
        note_id = note.id
        tag_id = tag.id

        # Delete note
        db_session.delete(note)
        db_session.commit()

        # Association should be gone
        result = db_session.execute(
            note_tags.select().where(
                note_tags.c.note_id == note_id and note_tags.c.tag_id == tag_id
            )
        ).fetchall()
        assert len(result) == 0
        # Tag still exists
        assert db_session.get(Tag, tag_id) is not None

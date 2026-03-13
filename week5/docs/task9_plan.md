# Plan: Task 9 - Query Performance and Indexes

## Context
Task 9 requires adding SQLite indexes to improve query performance. The current codebase lacks indexes on frequently queried columns, which can lead to slow queries as data grows.

## Current State

### Existing Indexes
- `notes.id` - primary key (auto-indexed)
- `tags.id` - primary key (auto-indexed)
- `tags.name` - unique index (explicitly added)
- `action_items.id` - primary key (auto-indexed)
- `note_tags` - composite primary key (note_id, tag_id)

### Missing Indexes (Identified from Query Analysis)

| Table | Column | Query Usage | Benefit |
|-------|--------|-------------|---------|
| notes | title | Search (LIKE), Sort by title | HIGH |
| notes | content | Search (LIKE) | MEDIUM |
| note_tags | note_id | JOIN to find notes by tag | HIGH |
| note_tags | tag_id | JOIN to find tags by note | HIGH |
| action_items | completed | Filter by completed status | MEDIUM |
| action_items | note_id | Foreign key lookup | MEDIUM |

## Implementation Plan

### Phase 1: Add Indexes to Models

Modify `/home/dd/lab/modern-software-dev-assignments/week5/backend/app/models.py`:

```python
from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, Table, Index

# 1. Add index on notes.title (for search and sorting)
class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # Add index for title search and sorting
    __table_args__ = (
        Index('ix_notes_title', 'title'),
    )

    tags = relationship("Tag", secondary=note_tags, back_populates="notes")
    action_items = relationship("ActionItem", back_populates="note", cascade="all, delete-orphan")


# 2. Add indexes on note_tags join table for efficient JOINs
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    # Add separate indexes for each column to optimize JOINs
    Index('ix_note_tags_note_id', 'note_id'),
    Index('ix_note_tags_tag_id', 'tag_id'),
)


# 3. Add partial index on action_items.completed (only incomplete items)
# Note: SQLAlchemy doesn't directly support partial indexes, so we'll use a hybrid approach
# Add regular index and consider partial index at migration level
class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False, index=True)  # Add index
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True, index=True)  # Add FK index

    note = relationship("Note", back_populates="action_items")
```

### Phase 2: Create Database Migration

Create a migration script to add indexes to existing database. Create `/home/dd/lab/modern-software-dev-assignments/week5/backend/migrations/versions/add_indexes.py`:

```python
"""Add performance indexes

Revision ID: add_indexes
Revises: 
Create Date: 2026-03-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index on notes.title for search and sorting
    op.create_index('ix_notes_title', 'notes', ['title'])
    
    # Indexes on note_tags for JOIN optimization
    op.create_index('ix_note_tags_note_id', 'note_tags', ['note_id'])
    op.create_index('ix_note_tags_tag_id', 'note_tags', ['tag_id'])
    
    # Index on action_items.completed for filtering
    op.create_index('ix_action_items_completed', 'action_items', ['completed'])
    
    # Index on action_items.note_id for foreign key lookups
    op.create_index('ix_action_items_note_id', 'action_items', ['note_id'])


def downgrade() -> None:
    op.drop_index('ix_notes_title', table_name='notes')
    op.drop_index('ix_note_tags_note_id', table_name='note_tags')
    op.drop_index('ix_note_tags_tag_id', table_name='note_tags')
    op.drop_index('ix_action_items_completed', table_name='action_items')
    op.drop_index('ix_action_items_note_id', table_name='action_items')
```

### Phase 3: Verify Query Plan Improvements

Create a test script to verify query plans before and after indexes. Create `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_query_performance.py`:

```python
"""
Tests to verify query performance improvements with indexes.
Run with: pytest backend/tests/test_query_performance.py -v
"""
import pytest
from sqlalchemy import inspect, text
from backend.app.db import engine, Base
from backend.app.models import Note, Tag, ActionItem, note_tags


class TestIndexesExist:
    """Verify that all expected indexes exist."""
    
    def test_notes_title_index_exists(self):
        """Verify index on notes.title exists."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('notes')
        index_names = [idx['name'] for idx in indexes]
        assert 'ix_notes_title' in index_names, "Index on notes.title should exist"
    
    def test_note_tags_indexes_exist(self):
        """Verify indexes on note_tags table exist."""
        inspector = inspect(engine)
        
        # Check note_id index
        indexes = inspector.get_indexes('note_tags')
        index_names = [idx['name'] for idx in indexes]
        assert 'ix_note_tags_note_id' in index_names
        assert 'ix_note_tags_tag_id' in index_names
    
    def test_action_items_completed_index_exists(self):
        """Verify index on action_items.completed exists."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('action_items')
        index_names = [idx['name'] for idx in indexes]
        assert 'ix_action_items_completed' in index_names
    
    def test_action_items_note_id_index_exists(self):
        """Verify index on action_items.note_id exists."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('action_items')
        index_names = [idx['name'] for idx in indexes]
        assert 'ix_action_items_note_id' in index_names


class TestQueryPlans:
    """Verify that queries use the new indexes."""
    
    def test_search_by_title_uses_index(self, db_session):
        """Verify search by title uses index."""
        query = "EXPLAIN QUERY PLAN SELECT * FROM notes WHERE title LIKE '%test%'"
        result = db_session.execute(text(query))
        plan = [row for row in result]
        # Should use ix_notes_title index
        plan_str = str(plan)
        assert 'ix_notes_title' in plan_str or 'SEARCH' in plan_str
    
    def test_filter_by_completed_uses_index(self, db_session):
        """Verify filter by completed uses index."""
        query = "EXPLAIN QUERY PLAN SELECT * FROM action_items WHERE completed = 1"
        result = db_session.execute(text(query))
        plan = [row for row in result]
        plan_str = str(plan)
        assert 'ix_action_items_completed' in plan_str or 'SEARCH' in plan_str
    
    def test_join_notes_tags_uses_indexes(self, db_session):
        """Verify JOIN between notes and tags uses indexes."""
        query = """
        EXPLAIN QUERY PLAN 
        SELECT notes.* FROM notes 
        JOIN note_tags ON notes.id = note_tags.note_id 
        WHERE note_tags.tag_id = 1
        """
        result = db_session.execute(text(query))
        plan = [row for row in result]
        plan_str = str(plan)
        # Should use note_id index for JOIN
        assert 'ix_note_tags_note_id' in plan_str or 'SEARCH' in plan_str


class TestPerformanceWithLargerDataset:
    """Test query performance with larger datasets."""
    
    @pytest.fixture
    def seeded_database(self, db_session):
        """Seed database with larger dataset for performance testing."""
        # Create 1000 notes
        notes = []
        for i in range(1000):
            note = Note(title=f"Test Note {i}", content=f"Content {i}")
            db_session.add(note)
            notes.append(note)
        
        # Create 50 tags
        tags = []
        for i in range(50):
            tag = Tag(name=f"tag{i}")
            db_session.add(tag)
            tags.append(tag)
        
        db_session.flush()
        
        # Create action items (5000 total)
        for i in range(5000):
            action = ActionItem(
                description=f"Action {i}",
                completed=i % 2 == 0,  # Half completed
                note_id=notes[i % 1000].id if i % 3 == 0 else None  # Some linked to notes
            )
            db_session.add(action)
        
        # Link notes to tags (many-to-many)
        for i, note in enumerate(notes[:500]):  # First 500 notes get tags
            note.tags = [tags[j % 50] for j in range(3)]
        
        db_session.commit()
        return {'notes': notes, 'tags': tags}
    
    def test_search_performance(self, db_session, seeded_database):
        """Verify search query performance with indexed title."""
        import time
        
        # Time a search query
        start = time.time()
        result = db_session.execute(
            text("SELECT * FROM notes WHERE title LIKE '%Note 5%' LIMIT 100")
        )
        rows = result.fetchall()
        elapsed = time.time() - start
        
        # Should complete quickly (< 100ms for 1000 rows)
        assert elapsed < 0.1, f"Search took {elapsed}s, should be < 0.1s"
    
    def test_join_performance(self, db_session, seeded_database):
        """Verify JOIN performance with indexed note_tags."""
        import time
        
        start = time.time()
        result = db_session.execute(
            text("""
                SELECT notes.* FROM notes 
                JOIN note_tags ON notes.id = note_tags.note_id 
                WHERE note_tags.tag_id = 1
            """)
        )
        rows = result.fetchall()
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 0.1, f"JOIN took {elapsed}s, should be < 0.1s"
    
    def test_filter_completed_performance(self, db_session, seeded_database):
        """Verify filter by completed performance."""
        import time
        
        start = time.time()
        result = db_session.execute(
            text("SELECT * FROM action_items WHERE completed = 0")
        )
        rows = result.fetchall()
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 0.1, f"Filter took {elapsed}s, should be < 0.1s"
```

### Phase 4: Update Tests Configuration

Ensure test fixtures are available in `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/conftest.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///test_performance.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        # Clean up
        Base.metadata.drop_all(engine)
```

### Phase 5: Run and Verify

1. Run existing tests to ensure no regressions:
   ```bash
   make test
   ```

2. Run new performance tests:
   ```bash
   pytest backend/tests/test_query_performance.py -v
   ```

3. Check query plans manually:
   ```bash
   sqlite3 backend/notes.db "EXPLAIN QUERY PLAN SELECT * FROM notes WHERE title LIKE '%test%';"
   ```

## Edge Cases and Considerations

### 1. Partial Indexes for Boolean Columns
SQLite supports partial indexes with the `WHERE` clause. For `action_items.completed`, consider:
```sql
CREATE INDEX ix_action_items_incomplete ON action_items(note_id) WHERE completed = 0;
```
This would only index incomplete items, which is likely the more frequently queried state.

**Decision**: Start with a regular index on `completed` for simplicity. Partial indexes can be added if performance testing shows it's beneficial.

### 2. Case-Insensitive Search
The current search uses `func.lower(Note.title).contains(q.lower())`, which cannot use a standard B-tree index. Consider:
- Adding a generated column: `title_lower = Column(String(200), computed=func.lower(title))`
- Creating an index on `title_lower`

**Decision**: Add index on `title` first (helps with sorting). For case-insensitive search optimization, this can be a follow-up task.

### 3. Index Overhead
Each index adds:
- Storage overhead (typically 10-30% of table size)
- Write overhead (INSERT/UPDATE must update indexes)

**Assessment**: With the expected data size (< 10,000 rows), the overhead is negligible and worth the read performance gain.

## Files to Modify

1. `/home/dd/lab/modern-software-dev-assignments/week5/backend/app/models.py` - Add index definitions
2. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_query_performance.py` - New test file
3. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/conftest.py` - Update if needed

## Verification Checklist

- [ ] All new indexes exist in database
- [ ] Query plans show index usage for:
  - [ ] Notes search by title
  - [ ] Notes sort by title
  - [ ] Notes JOIN to tags
  - [ ] Tags JOIN to notes
  - [ ] Action items filter by completed
  - [ ] Action items filter by note_id
- [ ] Existing tests pass (no regressions)
- [ ] Performance tests pass with larger datasets
- [ ] Query response times are acceptable (< 100ms for typical queries)

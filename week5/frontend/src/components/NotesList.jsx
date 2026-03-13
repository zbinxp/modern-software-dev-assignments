import { useState, useEffect } from 'react';
import { getNotes, createNote, deleteNote, searchNotes, getTags, createTag, addTagToNote, removeTagFromNote, getNotesByTag } from '../api';
import TagFilter from './TagFilter';

function NotesList() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tags, setTags] = useState([]);
  const [selectedTagId, setSelectedTagId] = useState(null);
  const [editingTagsNoteId, setEditingTagsNoteId] = useState(null);

  // Form state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  // Search and pagination state
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [sortBy, setSortBy] = useState('created_desc');
  const [totalNotes, setTotalNotes] = useState(0);

  const fetchTags = async () => {
    try {
      const data = await getTags();
      setTags(data);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  };

  const fetchNotes = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      if (selectedTagId) {
        data = await getNotesByTag(selectedTagId);
        setNotes(data);
        setTotalNotes(data.length);
      } else {
        data = await searchNotes(searchQuery, currentPage, pageSize, sortBy);
        setNotes(data.items);
        setTotalNotes(data.total);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  useEffect(() => {
    fetchNotes();
  }, [currentPage, sortBy, selectedTagId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Also re-fetch when searchQuery changes (debounced via submit)
  useEffect(() => {
    // This is handled by handleSearchSubmit
  }, [searchQuery]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    try {
      setError(null);

      // Parse hashtags from content before removing them
      const hashtagRegex = /#(\w+)/g;
      const matches = content.match(hashtagRegex);

      // Remove hashtags from content
      const contentWithoutHashtags = content.replace(hashtagRegex, '').trim();

      const newNote = await createNote({ title: title, content: contentWithoutHashtags });
      if (matches) {
        const uniqueTagNames = [...new Set(matches.map(tag => tag.slice(1).toLowerCase()))]; // Remove #, dedupe, lowercase

        // Get all existing tags
        let existingTags = await getTags();
        const tagIds = [];

        for (const tagName of uniqueTagNames) {
          let existingTag = existingTags.find(t => t.name.toLowerCase() === tagName);
          if (existingTag) {
            tagIds.push(existingTag.id);
          } else {
            // Create new tag - use lowercase for consistency
            try {
              const newTag = await createTag(tagName);
              tagIds.push(newTag.id);
              existingTags.push(newTag); // Add to local cache
            } catch (tagErr) {
              // Tag might already exist (race condition) - fetch it again
              try {
                existingTags = await getTags();
                existingTag = existingTags.find(t => t.name.toLowerCase() === tagName);
                if (existingTag) {
                  tagIds.push(existingTag.id);
                }
              } catch (fetchErr) {
                // Ignore fetch errors
              }
            }
          }
        }

        // Attach all tags to the note
        if (tagIds.length > 0) {
          try {
            await addTagToNote(newNote.id, tagIds);
          } catch (attachErr) {
            // Ignore attach errors
          }
        }
      }

      setTitle('');
      setContent('');
      fetchNotes();
      fetchTags(); // Refresh tags list
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await deleteNote(id);
      fetchNotes();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page on new search
    fetchNotes();
  };

  const handleSortChange = (e) => {
    setSortBy(e.target.value);
    setCurrentPage(1); // Reset to first page on sort change
  };

  const totalPages = Math.ceil(totalNotes / pageSize);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleTagSelect = (tagId) => {
    setSelectedTagId(tagId);
    setCurrentPage(1);
  };

  const handleEditTags = async (noteId, currentTagIds) => {
    const allTagIds = tags.map(t => t.id);
    const newTagIds = allTagIds.filter(id => !currentTagIds.includes(id));

    if (newTagIds.length > 0) {
      // Add the first available tag to demonstrate functionality
      await addTagToNote(noteId, [...currentTagIds, newTagIds[0]]);
      fetchNotes();
    }
    setEditingTagsNoteId(null);
  };

  const handleRemoveTag = async (noteId, tagId) => {
    try {
      await removeTagFromNote(noteId, tagId);
      fetchNotes();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <p>Loading notes...</p>;
  }

  return (
    <div>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
        />
        <button type="submit">Add</button>
      </form>

      {/* Search and Sort Controls */}
      <div style={{ margin: '1rem 0' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'inline' }}>
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>

        <select value={sortBy} onChange={handleSortChange} style={{ marginLeft: '0.5rem' }}>
          <option value="created_desc">Newest</option>
          <option value="created_asc">Oldest</option>
          <option value="title_asc">Title A-Z</option>
          <option value="title_desc">Title Z-A</option>
        </select>
      </div>

      {/* Tag Filter */}
      <TagFilter selectedTagId={selectedTagId} onTagSelect={handleTagSelect} />

      {/* Result count */}
      <p>Showing {notes.length} of {totalNotes} notes</p>

      {notes.length === 0 ? (
        <p>No notes found.</p>
      ) : (
        <ul>
          {notes.map((note) => (
            <li key={note.id} style={{ marginBottom: '1rem' }}>
              <strong>{note.title}</strong>: {note.content}
              {/* Tags display */}
              {note.tags && note.tags.length > 0 && (
                <div style={{ marginTop: '0.25rem' }}>
                  {note.tags.map((tag) => (
                    <span
                      key={tag.id}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '0.125rem 0.5rem',
                        backgroundColor: '#e0e7ff',
                        borderRadius: '1rem',
                        fontSize: '0.75rem',
                        marginRight: '0.25rem',
                      }}
                    >
                      {tag.name}
                      <button
                        onClick={() => handleRemoveTag(note.id, tag.id)}
                        style={{
                          marginLeft: '0.25rem',
                          padding: '0 0.25rem',
                          fontSize: '0.625rem',
                          background: 'none',
                          border: 'none',
                          color: '#666',
                          cursor: 'pointer',
                        }}
                        title="Remove tag"
                      >
                        x
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <button
                onClick={() => handleDelete(note.id)}
                style={{ marginLeft: '0.5rem' }}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ marginTop: '1rem' }}>
          <button onClick={handlePrevPage} disabled={currentPage === 1}>
            Previous
          </button>
          <span style={{ margin: '0 0.5rem' }}>
            Page {currentPage} of {totalPages}
          </span>
          <button onClick={handleNextPage} disabled={currentPage === totalPages}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default NotesList;

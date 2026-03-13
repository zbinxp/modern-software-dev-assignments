import { useState, useEffect } from 'react';
import { getNotes, createNote, deleteNote, searchNotes, getTags, createTag, addTagToNote, removeTagFromNote, getNotesByTag, updateNote, extractFromNote } from '../api';
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

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');

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

      // Extract and apply checkbox tasks and hashtags from original content
      try {
        await extractFromNote(newNote.id, true);
      } catch (extractErr) {
        // Ignore extraction errors
        console.log('Extraction error (ignored):', extractErr);
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
    // Optimistic delete: store current notes for rollback
    const previousNotes = [...notes];

    // Immediately remove note from state
    setNotes(notes.filter(note => note.id !== id));
    setTotalNotes(totalNotes - 1);
    setError(null);

    try {
      await deleteNote(id);
    } catch (err) {
      // Rollback on error
      setNotes(previousNotes);
      setTotalNotes(previousNotes.length);
      setError(err.message);
    }
  };

  const handleEditStart = (note) => {
    setEditingId(note.id);
    setEditTitle(note.title);
    setEditContent(note.content);
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditTitle('');
    setEditContent('');
  };

  const handleEditSave = async (id) => {
    if (!editTitle.trim() || !editContent.trim()) return;

    // Optimistic update: store previous state for rollback
    const previousNotes = [...notes];

    // Immediately update note in state
    setNotes(notes.map(note =>
      note.id === id ? { ...note, title: editTitle, content: editContent } : note
    ));
    setError(null);
    setEditingId(null);

    try {
      await updateNote(id, { title: editTitle, content: editContent });
    } catch (err) {
      // Rollback on error
      setNotes(previousNotes);
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
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '1rem' }}>
      {error && <p style={{ color: 'red', padding: '0.5rem', backgroundColor: '#fee', borderRadius: '4px' }}>Error: {error}</p>}

      {/* Create Note Form */}
      <div style={{ backgroundColor: '#f9f9f9', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem 0' }}>Create New Note</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '0.75rem' }}>
            <input
              type="text"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem',
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <textarea
              placeholder="Content (supports multi-line, #hashtags, - [ ] checkboxes)"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={4}
              style={{
                width: '100%',
                padding: '0.5rem',
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />
          </div>
          <button
            type="submit"
            style={{
              padding: '0.5rem 1.5rem',
              fontSize: '1rem',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Add Note
          </button>
        </form>
      </div>

      {/* Search and Sort Controls */}
      <div style={{ margin: '1rem 0', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearchSubmit}>
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '0.5rem',
              fontSize: '0.9rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '200px'
            }}
          />
          <button
            type="submit"
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.9rem',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginLeft: '0.25rem'
            }}
          >
            Search
          </button>
        </form>

        <select
          value={sortBy}
          onChange={handleSortChange}
          style={{
            padding: '0.5rem',
            fontSize: '0.9rem',
            border: '1px solid #ddd',
            borderRadius: '4px'
          }}
        >
          <option value="created_desc">Newest</option>
          <option value="created_asc">Oldest</option>
          <option value="title_asc">Title A-Z</option>
          <option value="title_desc">Title Z-A</option>
        </select>
      </div>

      {/* Tag Filter */}
      <TagFilter selectedTagId={selectedTagId} onTagSelect={handleTagSelect} />

      {/* Result count */}
      <p style={{ color: '#666' }}>Showing {notes.length} of {totalNotes} notes</p>

      {notes.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>No notes found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {notes.map((note) => (
            <div
              key={note.id}
              style={{
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '1rem',
                backgroundColor: 'white',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}
            >
              {editingId === note.id ? (
                // Edit mode
                <div>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      fontSize: '1rem',
                      fontWeight: 'bold',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      marginBottom: '0.5rem',
                      boxSizing: 'border-box'
                    }}
                  />
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      fontSize: '1rem',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontFamily: 'inherit',
                      resize: 'vertical',
                      marginBottom: '0.5rem',
                      boxSizing: 'border-box'
                    }}
                  />
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => handleEditSave(note.id)}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      Save
                    </button>
                    <button
                      onClick={handleEditCancel}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#9e9e9e',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{note.title}</h3>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleEditStart(note)}
                        style={{
                          padding: '0.25rem 0.75rem',
                          fontSize: '0.85rem',
                          backgroundColor: '#2196F3',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(note.id)}
                        style={{
                          padding: '0.25rem 0.75rem',
                          fontSize: '0.85rem',
                          backgroundColor: '#f44336',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div
                    style={{
                      whiteSpace: 'pre-wrap',
                      fontSize: '0.95rem',
                      lineHeight: '1.5',
                      color: '#333',
                      marginBottom: '0.75rem',
                      padding: '0.5rem',
                      backgroundColor: '#fafafa',
                      borderRadius: '4px'
                    }}
                  >
                    {note.content}
                  </div>
                  {note.tags && note.tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {note.tags.map((tag) => (
                        <span
                          key={tag.id}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '0.25rem 0.75rem',
                            backgroundColor: '#e3f2fd',
                            borderRadius: '1rem',
                            fontSize: '0.8rem',
                            color: '#1565c0'
                          }}
                        >
                          #{tag.name}
                          <button
                            onClick={() => handleRemoveTag(note.id, tag.id)}
                            style={{
                              marginLeft: '0.25rem',
                              padding: '0 0.25rem',
                              fontSize: '0.7rem',
                              background: 'none',
                              border: 'none',
                              color: '#666',
                              cursor: 'pointer'
                            }}
                            title="Remove tag"
                          >
                            x
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: currentPage === 1 ? '#e0e0e0' : '#2196F3',
              color: currentPage === 1 ? '#999' : 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            Previous
          </button>
          <span style={{ padding: '0 1rem' }}>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: currentPage === totalPages ? '#e0e0e0' : '#2196F3',
              color: currentPage === totalPages ? '#999' : 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
            }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default NotesList;

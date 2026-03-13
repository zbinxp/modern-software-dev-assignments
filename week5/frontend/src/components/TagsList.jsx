import { useState, useEffect } from 'react';
import { getTags, createTag, deleteTag } from '../api';

function TagsList() {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTagName, setNewTagName] = useState('');

  const fetchTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTags();
      setTags(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    try {
      setError(null);
      await createTag(newTagName.trim());
      setNewTagName('');
      fetchTags();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await deleteTag(id);
      fetchTags();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <p>Loading tags...</p>;
  }

  return (
    <div style={{ marginBottom: '2rem' }}>
      <h3>Tags</h3>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <form onSubmit={handleSubmit} style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="New tag name"
          value={newTagName}
          onChange={(e) => setNewTagName(e.target.value)}
        />
        <button type="submit">Add Tag</button>
      </form>

      {tags.length === 0 ? (
        <p>No tags yet.</p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {tags.map((tag) => (
            <span
              key={tag.id}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '0.25rem 0.5rem',
                backgroundColor: '#e0e7ff',
                borderRadius: '1rem',
                fontSize: '0.875rem',
              }}
            >
              {tag.name}
              <button
                onClick={() => handleDelete(tag.id)}
                style={{
                  marginLeft: '0.5rem',
                  padding: '0 0.25rem',
                  fontSize: '0.75rem',
                  background: 'none',
                  border: 'none',
                  color: '#666',
                  cursor: 'pointer',
                }}
                title="Delete tag"
              >
                x
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default TagsList;

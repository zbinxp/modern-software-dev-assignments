import { useState, useEffect } from 'react';
import { getTags } from '../api';

function TagFilter({ selectedTagId, onTagSelect }) {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const data = await getTags();
        setTags(data);
      } catch (err) {
        console.error('Failed to load tags:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTags();
  }, []);

  if (loading) {
    return null;
  }

  if (tags.length === 0) {
    return null;
  }

  return (
    <div style={{ margin: '1rem 0' }}>
      <span style={{ marginRight: '0.5rem' }}>Filter by tag:</span>
      <select
        value={selectedTagId || ''}
        onChange={(e) => {
          const value = e.target.value;
          onTagSelect(value ? parseInt(value, 10) : null);
        }}
      >
        <option value="">All notes</option>
        {tags.map((tag) => (
          <option key={tag.id} value={tag.id}>
            {tag.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default TagFilter;

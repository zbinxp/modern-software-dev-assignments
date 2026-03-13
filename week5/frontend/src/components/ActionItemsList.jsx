import { useState, useEffect } from 'react';
import { getActionItems, createActionItem, completeActionItem, deleteActionItem, bulkCompleteActionItems } from '../api';

function ActionItemsList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [description, setDescription] = useState('');
  const [filter, setFilter] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());

  const fetchItems = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getActionItems(filter);
      setItems(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [filter]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) return;

    try {
      setError(null);
      await createActionItem({ description });
      setDescription('');
      fetchItems();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleComplete = async (id) => {
    try {
      setError(null);
      await completeActionItem(id);
      fetchItems();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await deleteActionItem(id);
      fetchItems();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleBulkComplete = async () => {
    if (selectedIds.size === 0) return;
    try {
      setError(null);
      await bulkCompleteActionItems([...selectedIds]);
      setSelectedIds(new Set());
      fetchItems();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleSelection = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  if (loading) {
    return <p>Loading action items...</p>;
  }

  return (
    <div>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <button type="submit">Add</button>
      </form>

      <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
        <button onClick={() => setFilter(null)} disabled={filter === null}>All</button>
        <button onClick={() => setFilter(false)} disabled={filter === false} style={{ marginLeft: '0.5rem' }}>Open</button>
        <button onClick={() => setFilter(true)} disabled={filter === true} style={{ marginLeft: '0.5rem' }}>Completed</button>
        {selectedIds.size > 0 && (
          <button onClick={handleBulkComplete} style={{ marginLeft: '1rem' }}>
            Complete Selected ({selectedIds.size})
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p>No action items yet.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.id}>
              <input
                type="checkbox"
                checked={selectedIds.has(item.id)}
                onChange={() => toggleSelection(item.id)}
                disabled={item.completed}
                style={{ marginRight: '0.5rem' }}
              />
              {item.description} [{item.completed ? 'done' : 'open'}]
              {!item.completed && (
                <button
                  onClick={() => handleComplete(item.id)}
                  style={{ marginLeft: '0.5rem' }}
                >
                  Complete
                </button>
              )}
              <button
                onClick={() => handleDelete(item.id)}
                style={{ marginLeft: '0.5rem' }}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ActionItemsList;

import { useState, useEffect } from 'react';
import { getActionItems, createActionItem, completeActionItem, deleteActionItem, bulkCompleteActionItems } from '../api';

function ActionItemsList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [description, setDescription] = useState('');
  const [filter, setFilter] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  const fetchItems = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getActionItems(filter, currentPage, pageSize);
      setItems(data.items);
      setTotalItems(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [filter, currentPage]);

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

  const totalPages = Math.ceil(totalItems / pageSize);

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

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setCurrentPage(1); // Reset to first page on filter change
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
        <button onClick={() => handleFilterChange(null)} disabled={filter === null}>All</button>
        <button onClick={() => handleFilterChange(false)} disabled={filter === false} style={{ marginLeft: '0.5rem' }}>Open</button>
        <button onClick={() => handleFilterChange(true)} disabled={filter === true} style={{ marginLeft: '0.5rem' }}>Completed</button>
        {selectedIds.size > 0 && (
          <button onClick={handleBulkComplete} style={{ marginLeft: '1rem' }}>
            Complete Selected ({selectedIds.size})
          </button>
        )}
      </div>

      {/* Result count */}
      <p style={{ color: '#666' }}>Showing {items.length} of {totalItems} action items</p>

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

export default ActionItemsList;

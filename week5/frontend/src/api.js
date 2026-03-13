const API_BASE = ''; // Uses relative paths, proxied by Vite

async function fetchJSON(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `HTTP error ${res.status}`);
  }
  return res.json();
}

// Notes API
export async function getNotes() {
  return fetchJSON('/notes/');
}

export async function getNote(id) {
  return fetchJSON(`/notes/${id}`);
}

export async function searchNotes(query = '', page = 1, pageSize = 10, sort = 'created_desc') {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  params.append('page', page);
  params.append('page_size', pageSize);
  params.append('sort', sort);
  return fetchJSON(`/notes/search/?${params.toString()}`);
}

export async function createNote(note) {
  return fetchJSON('/notes/', {
    method: 'POST',
    body: JSON.stringify(note),
  });
}

export async function deleteNote(id) {
  return fetchJSON(`/notes/${id}`, {
    method: 'DELETE',
  });
}

// Action Items API
export async function getActionItems(completed = null) {
  const params = completed !== null ? `?completed=${completed}` : '';
  return fetchJSON(`/action-items/${params}`);
}

export async function createActionItem(item) {
  return fetchJSON('/action-items/', {
    method: 'POST',
    body: JSON.stringify(item),
  });
}

export async function completeActionItem(id) {
  return fetchJSON(`/action-items/${id}/complete`, {
    method: 'PUT',
  });
}

export async function deleteActionItem(id) {
  return fetchJSON(`/action-items/${id}`, {
    method: 'DELETE',
  });
}

export async function bulkCompleteActionItems(ids) {
  return fetchJSON('/action-items/bulk-complete', {
    method: 'POST',
    body: JSON.stringify({ ids }),
  });
}

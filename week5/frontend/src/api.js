const API_BASE = ''; // Uses relative paths, proxied by Vite

async function fetchJSON(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  // Handle 204 No Content responses
  if (res.status === 204) {
    return null;
  }

  const data = await res.json();

  // Handle envelope format
  if (data !== null && typeof data === 'object' && 'ok' in data) {
    if (data.ok === true) {
      return data.data;
    } else {
      // Error response - throw with the error message
      const errorMessage = data.error?.message || `HTTP error ${res.status}`;
      throw new Error(errorMessage);
    }
  }

  // Handle non-envelope error responses
  if (!res.ok) {
    throw new Error(typeof data === 'string' ? data : `HTTP error ${res.status}`);
  }

  return data;
}

// Notes API
export async function getNotes(page = 1, pageSize = 10) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  return fetchJSON(`/notes/?${params.toString()}`);
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
  const res = await fetch(`/notes/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `HTTP error ${res.status}`);
  }
  // DELETE returns 204 No Content, so we don't try to parse JSON
  return undefined;
}

export async function updateNote(id, note) {
  return fetchJSON(`/notes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(note),
  });
}

// Action Items API
export async function getActionItems(completed = null, page = 1, pageSize = 10) {
  const params = new URLSearchParams();
  if (completed !== null) params.append('completed', completed);
  params.append('page', page);
  params.append('page_size', pageSize);
  return fetchJSON(`/action-items/?${params.toString()}`);
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

// Tags API
export async function getTags() {
  return fetchJSON('/tags/');
}

export async function createTag(name) {
  return fetchJSON('/tags/', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function deleteTag(id) {
  return fetchJSON(`/tags/${id}`, {
    method: 'DELETE',
  });
}

export async function addTagToNote(noteId, tagIds) {
  return fetchJSON(`/notes/${noteId}/tags`, {
    method: 'POST',
    body: JSON.stringify({ tag_ids: tagIds }),
  });
}

export async function removeTagFromNote(noteId, tagId) {
  return fetchJSON(`/notes/${noteId}/tags/${tagId}`, {
    method: 'DELETE',
  });
}

export async function getNotesByTag(tagId) {
  return fetchJSON(`/notes/by-tag/${tagId}`);
}

// Extraction API
export async function extractFromNote(noteId, apply = false) {
  return fetchJSON(`/notes/${noteId}/extract`, {
    method: 'POST',
    body: JSON.stringify({ apply }),
  });
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return null;
  return res.json();
}

function showError(msg) {
  const el = document.getElementById('note-error');
  el.textContent = msg;
  setTimeout(() => { el.textContent = ''; }, 5000);
}

async function loadNotes(params = {}) {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const query = new URLSearchParams(params);
  const notes = await fetchJSON('/notes/?' + query.toString());
  for (const n of notes) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${escapeHtml(n.title)}</strong>: ${escapeHtml(n.content)} `;

    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.onclick = () => editNote(n.id, n.title, n.content);
    li.appendChild(editBtn);

    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.onclick = () => deleteNote(n.id);
    li.appendChild(delBtn);

    list.appendChild(li);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function editNote(id, title, content) {
  document.getElementById('edit-note-id').value = id;
  document.getElementById('edit-note-title').value = title;
  document.getElementById('edit-note-content').value = content;
  document.getElementById('note-edit-form').style.display = 'block';
  document.getElementById('note-error').textContent = '';
}

async function deleteNote(id) {
  if (!confirm('Delete this note?')) return;
  try {
    await fetchJSON(`/notes/${id}`, { method: 'DELETE' });
    loadNotes();
  } catch (e) {
    showError('Failed to delete note: ' + e.message);
  }
}

async function loadActions(params = {}) {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  const query = new URLSearchParams(params);
  const items = await fetchJSON('/action-items/?' + query.toString());
  for (const a of items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions(params);
      };
      li.appendChild(btn);
    } else {
      const btn = document.createElement('button');
      btn.textContent = 'Reopen';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed: false }),
        });
        loadActions(params);
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-search-btn').addEventListener('click', async () => {
    const q = document.getElementById('note-search').value;
    loadNotes({ q });
  });

  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    try {
      await fetchJSON('/notes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      e.target.reset();
      loadNotes();
    } catch (err) {
      showError(err.message);
    }
  });

  document.getElementById('save-note-btn').addEventListener('click', async () => {
    const id = document.getElementById('edit-note-id').value;
    const title = document.getElementById('edit-note-title').value;
    const content = document.getElementById('edit-note-content').value;
    try {
      await fetchJSON(`/notes/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      document.getElementById('note-edit-form').style.display = 'none';
      loadNotes();
    } catch (err) {
      showError(err.message);
    }
  });

  document.getElementById('cancel-edit-btn').addEventListener('click', () => {
    document.getElementById('note-edit-form').style.display = 'none';
    document.getElementById('note-error').textContent = '';
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    loadActions();
  });

  document.getElementById('filter-completed').addEventListener('change', (e) => {
    const checked = e.target.checked;
    loadActions({ completed: checked });
  });

  loadNotes();
  loadActions();
});



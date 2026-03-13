import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NotesList from '../components/NotesList';

// Mock the API module
vi.mock('../api', () => ({
  getNotes: vi.fn(),
  createNote: vi.fn(),
  deleteNote: vi.fn(),
  updateNote: vi.fn(),
  searchNotes: vi.fn(),
  getTags: vi.fn(),
  createTag: vi.fn(),
  addTagToNote: vi.fn(),
  removeTagFromNote: vi.fn(),
  getNotesByTag: vi.fn(),
}));

import { getNotes, createNote, deleteNote, updateNote, searchNotes, getTags, createTag, addTagToNote, removeTagFromNote, getNotesByTag } from '../api';

describe('NotesList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mocks for getTags - returns empty array on every call by default
    getTags.mockResolvedValue([]);
    getNotesByTag.mockResolvedValue([]);
  });

  it('renders loading state initially', () => {
    searchNotes.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<NotesList />);
    expect(screen.getByText('Loading notes...')).toBeDefined();
  });

  it('renders notes after loading', async () => {
    const mockResponse = {
      items: [
        { id: 1, title: 'Test Note', content: 'Test content', tags: [] },
        { id: 2, title: 'Another Note', content: 'Another content', tags: [] },
      ],
      total: 2,
      page: 1,
      page_size: 10,
    };
    searchNotes.mockResolvedValue(mockResponse);

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText(/Test Note/)).toBeDefined();
      expect(screen.getByText(/Test content/)).toBeDefined();
      expect(screen.getByText(/Another Note/)).toBeDefined();
      expect(screen.getByText(/Another content/)).toBeDefined();
    });
  });

  it('renders empty state when no notes', async () => {
    searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText('No notes found.')).toBeDefined();
    });
  });

  it('renders error message on failure', async () => {
    searchNotes.mockRejectedValue(new Error('Failed to fetch'));

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeDefined();
    });
  });

  it('can create a new note', async () => {
    searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
    createNote.mockResolvedValue({ id: 1, title: 'New', content: 'Note' });

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notes...')).toBeNull();
    });

    const titleInput = screen.getByPlaceholderText('Title');
    const contentInput = screen.getByPlaceholderText(/^Content/);
    const submitButton = screen.getByText('Add Note');

    fireEvent.change(titleInput, { target: { value: 'New' } });
    fireEvent.change(contentInput, { target: { value: 'Note' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(createNote).toHaveBeenCalledWith({ title: 'New', content: 'Note' });
    });
  });

  it('can delete a note', async () => {
    const mockResponse = {
      items: [{ id: 1, title: 'Test', content: 'Content', tags: [] }],
      total: 1,
      page: 1,
      page_size: 10,
    };
    searchNotes.mockResolvedValue(mockResponse);
    deleteNote.mockResolvedValue(undefined);

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText(/Test/)).toBeDefined();
      expect(screen.getByText(/Content/)).toBeDefined();
    });

    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(deleteNote).toHaveBeenCalledWith(1);
    });
  });

  it('shows result count correctly', async () => {
    const mockResponse = {
      items: [{ id: 1, title: 'Test', content: 'Content' }],
      total: 15,
      page: 1,
      page_size: 10,
    };
    searchNotes.mockResolvedValue(mockResponse);

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText('Showing 1 of 15 notes')).toBeDefined();
    });
  });

  it('shows pagination controls when there are multiple pages', async () => {
    const mockResponse = {
      items: [{ id: 1, title: 'Test', content: 'Content' }],
      total: 25,
      page: 1,
      page_size: 10,
    };
    searchNotes.mockResolvedValue(mockResponse);

    render(<NotesList />);

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeDefined();
      expect(screen.getByText('Previous')).toBeDefined();
      expect(screen.getByText('Next')).toBeDefined();
    });
  });
});

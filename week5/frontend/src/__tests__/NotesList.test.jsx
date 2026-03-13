import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NotesList from '../components/NotesList';

// Mock the API module
vi.mock('../api', () => ({
  getNotes: vi.fn(),
  createNote: vi.fn(),
  deleteNote: vi.fn(),
  searchNotes: vi.fn(),
  getTags: vi.fn(),
  createTag: vi.fn(),
  addTagToNote: vi.fn(),
  removeTagFromNote: vi.fn(),
  getNotesByTag: vi.fn(),
}));

import { getNotes, createNote, deleteNote, searchNotes, getTags, createTag, addTagToNote, removeTagFromNote, getNotesByTag } from '../api';

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
    const contentInput = screen.getByPlaceholderText('Content');
    const submitButton = screen.getByText('Add');

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

  describe('hashtag handling', () => {
    it('creates new tag when hashtag does not exist', async () => {
      // Return empty on ALL calls so createTag is always attempted
      getTags.mockResolvedValue([]);

      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Test #newtag' });
      createTag.mockResolvedValue({ id: 1, name: 'newtag' });
      addTagToNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Test #newtag', tags: [{ id: 1, name: 'newtag' }] });

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Test #newtag' } });
      fireEvent.click(submitButton);

      // Wait for note to be created first
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // CreateTag should have been called since getTags returned empty
      expect(createTag).toHaveBeenCalled();
    });

    it('uses existing tag when hashtag already exists', async () => {
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Buy milk #shopping' });
      getTags.mockResolvedValue([{ id: 1, name: 'shopping' }]);
      addTagToNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Buy milk #shopping', tags: [{ id: 1, name: 'shopping' }] });

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Buy milk #shopping' } });
      fireEvent.click(submitButton);

      // Wait for note to be created first
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // Should NOT create a new tag (createTag should not be called)
      expect(createTag).not.toHaveBeenCalled();

      // Should attach the existing tag to the note
      await waitFor(() => {
        expect(addTagToNote).toHaveBeenCalledWith(1, [1]);
      });
    });

    it('does not create tags when no hashtags are present', async () => {
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Just a note without tags' });
      getTags.mockResolvedValue([]);

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Just a note without tags' } });
      fireEvent.click(submitButton);

      // Wait for note to be created
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      expect(createTag).not.toHaveBeenCalled();
      expect(addTagToNote).not.toHaveBeenCalled();
    });

    it('handles case-insensitive hashtag matching', async () => {
      // Setup: existing tag is lowercase
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Buy milk #SHOPPING' });
      getTags.mockResolvedValue([{ id: 1, name: 'shopping' }]);

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Buy milk #SHOPPING' } });
      fireEvent.click(submitButton);

      // Wait for note to be created first
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // Should NOT create a new tag - should match existing lowercase tag
      expect(createTag).not.toHaveBeenCalled();

      // Should attach the existing tag to the note
      await waitFor(() => {
        expect(addTagToNote).toHaveBeenCalledWith(1, [1]);
      });
    });

    it('calls getTags when creating a note with hashtags', async () => {
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Test #tag' });
      getTags.mockResolvedValue([{ id: 1, name: 'tag' }]);
      addTagToNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Test #tag', tags: [{ id: 1, name: 'tag' }] });

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Test #tag' } });
      fireEvent.click(submitButton);

      // Wait for note to be created
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // getTags should have been called at least once during submit
      expect(getTags).toHaveBeenCalled();
    });

    it('removes hashtags from note content when creating', async () => {
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      // The note should be saved WITHOUT hashtags in content
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Buy milk' });
      getTags.mockResolvedValue([{ id: 1, name: 'shopping' }]);
      addTagToNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Buy milk', tags: [{ id: 1, name: 'shopping' }] });

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Buy milk #shopping' } });
      fireEvent.click(submitButton);

      // Wait for note to be created
      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // Verify that the note was created WITHOUT the hashtag in content
      expect(createNote).toHaveBeenCalledWith({ title: 'Test', content: 'Buy milk' });
    });

    it('removes multiple hashtags from note content', async () => {
      searchNotes.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });
      createNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Task with tags' });
      getTags.mockResolvedValue([
        { id: 1, name: 'work' },
        { id: 2, name: 'urgent' }
      ]);
      addTagToNote.mockResolvedValue({ id: 1, title: 'Test', content: 'Task with tags', tags: [{ id: 1, name: 'work' }, { id: 2, name: 'urgent' }] });

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.queryByText('Loading notes...')).toBeNull();
      });

      const titleInput = screen.getByPlaceholderText('Title');
      const contentInput = screen.getByPlaceholderText('Content');
      const submitButton = screen.getByText('Add');

      fireEvent.change(titleInput, { target: { value: 'Test' } });
      fireEvent.change(contentInput, { target: { value: 'Task with tags #work #urgent' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(createNote).toHaveBeenCalled();
      });

      // Verify that the note was created WITHOUT hashtags in content
      expect(createNote).toHaveBeenCalledWith({ title: 'Test', content: 'Task with tags' });
    });
  });

  describe('tag removal', () => {
    it('can remove a tag from a note', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            title: 'Test Note',
            content: 'Test content',
            tags: [{ id: 1, name: 'shopping' }],
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
      };
      searchNotes.mockResolvedValue(mockResponse);
      getTags.mockResolvedValue([{ id: 1, name: 'shopping' }]);
      removeTagFromNote.mockResolvedValue(null);

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.getByText('shopping')).toBeDefined();
      });

      const removeTagButton = screen.getByTitle('Remove tag');
      fireEvent.click(removeTagButton);

      await waitFor(() => {
        expect(removeTagFromNote).toHaveBeenCalledWith(1, 1);
      });
    });

    it('handles remove tag failure gracefully', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            title: 'Test Note',
            content: 'Test content',
            tags: [{ id: 1, name: 'shopping' }],
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
      };
      searchNotes.mockResolvedValue(mockResponse);
      getTags.mockResolvedValue([{ id: 1, name: 'shopping' }]);
      removeTagFromNote.mockRejectedValue(new Error('Failed to remove tag'));

      render(<NotesList />);

      await waitFor(() => {
        expect(screen.getByText('shopping')).toBeDefined();
      });

      const removeTagButton = screen.getByTitle('Remove tag');
      fireEvent.click(removeTagButton);

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeDefined();
      });
    });
  });
});

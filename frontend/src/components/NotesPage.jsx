import { useState, useEffect, useRef } from 'react';
import { getNotes, createNote, updateNote, deleteNote } from '../services/api';

function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const saveTimer = useRef(null);

  useEffect(() => {
    loadNotes();
  }, []);

  async function loadNotes() {
    try {
      const res = await getNotes();
      setNotes(res.data);
      if (res.data.length > 0 && !activeId) {
        selectNote(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to load notes', err);
    } finally {
      setLoading(false);
    }
  }

  function selectNote(note) {
    if (saveTimer.current) {
      clearTimeout(saveTimer.current);
      saveTimer.current = null;
    }
    setActiveId(note.id);
    setTitle(note.title);
    setContent(note.content);
  }

  async function handleNew() {
    try {
      const res = await createNote({ title: 'Untitled', content: '' });
      setNotes((prev) => [res.data, ...prev]);
      selectNote(res.data);
    } catch (err) {
      console.error('Failed to create note', err);
    }
  }

  async function handleDelete() {
    if (!activeId) return;
    try {
      await deleteNote(activeId);
      setNotes((prev) => {
        const remaining = prev.filter((n) => n.id !== activeId);
        if (remaining.length > 0) {
          selectNote(remaining[0]);
        } else {
          setActiveId(null);
          setTitle('');
          setContent('');
        }
        return remaining;
      });
    } catch (err) {
      console.error('Failed to delete note', err);
    }
  }

  function scheduleAutosave(newTitle, newContent) {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      if (!activeId) return;
      setSaving(true);
      try {
        const res = await updateNote(activeId, { title: newTitle, content: newContent });
        setNotes((prev) =>
          prev.map((n) => (n.id === activeId ? res.data : n))
        );
      } catch (err) {
        console.error('Failed to save note', err);
      } finally {
        setSaving(false);
      }
    }, 500);
  }

  function handleTitleChange(e) {
    const val = e.target.value;
    setTitle(val);
    scheduleAutosave(val, content);
  }

  function handleContentChange(e) {
    const val = e.target.value;
    setContent(val);
    scheduleAutosave(title, val);
  }

  if (loading) {
    return <div className="loading">Loading notes...</div>;
  }

  return (
    <div className="notes-layout">
      <aside className="notes-sidebar">
        <div className="notes-sidebar-header">
          <h3>Notes</h3>
          <button className="btn btn-secondary btn-sm" onClick={handleNew}>
            + New
          </button>
        </div>
        <ul className="notes-list">
          {notes.map((note) => (
            <li
              key={note.id}
              className={`notes-list-item ${note.id === activeId ? 'active' : ''}`}
              onClick={() => selectNote(note)}
            >
              <span className="notes-list-title">{note.title || 'Untitled'}</span>
              <span className="notes-list-date">
                {new Date(note.updated_at).toLocaleDateString()}
              </span>
            </li>
          ))}
          {notes.length === 0 && (
            <li className="notes-list-empty">No notes yet</li>
          )}
        </ul>
      </aside>

      <main className="notes-editor">
        {activeId ? (
          <>
            <div className="notes-editor-header">
              <input
                type="text"
                className="notes-title-input"
                value={title}
                onChange={handleTitleChange}
                placeholder="Note title"
              />
              <div className="notes-editor-actions">
                {saving && <span className="notes-saving">Saving...</span>}
                <button className="btn btn-danger btn-sm" onClick={handleDelete}>
                  Delete
                </button>
              </div>
            </div>
            <textarea
              className="notes-content-input"
              value={content}
              onChange={handleContentChange}
              placeholder="Start writing..."
            />
          </>
        ) : (
          <div className="notes-empty-state">
            <p>Select a note or create a new one</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default NotesPage;

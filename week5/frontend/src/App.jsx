import NotesList from './components/NotesList';
import ActionItemsList from './components/ActionItemsList';
import TagsList from './components/TagsList';

function App() {
  return (
    <main>
      <h1>Modern Software Dev Starter</h1>

      <section>
        <h2>Notes</h2>
        <NotesList />
      </section>

      <section>
        <h2>Action Items</h2>
        <ActionItemsList />
      </section>

      <section>
        <h2>Tags</h2>
        <TagsList />
      </section>
    </main>
  );
}

export default App;

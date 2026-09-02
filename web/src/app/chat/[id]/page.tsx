export default async function ChatThreadPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <main>
      <h1>Chat Thread</h1>
      <p>Placeholder — direct messaging for thread {id} goes here.</p>
    </main>
  );
}

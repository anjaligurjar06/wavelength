"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";

const POLL_MS = 4000;

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [myId, setMyId] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const loadMessages = useCallback(async () => {
    try {
      const res = await apiFetch(`/chat/threads/${id}/messages`);
      if (res.status === 403 || res.status === 404) {
        setError("This conversation doesn't exist or isn't yours.");
        return;
      }
      if (!res.ok) throw new Error(`Messages request failed: ${res.status}`);
      setMessages(await res.json());
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Couldn't load messages. RetryingÃ¢â‚¬Â¦");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    async function loadMe() {
      try {
        const res = await apiFetch("/users/me");
        if (res.ok) setMyId((await res.json()).id);
      } catch (err) {
        console.error(err);
      }
    }
    loadMe();
    const initialLoad = setTimeout(() => void loadMessages(), 0);
    const timer = setInterval(() => void loadMessages(), POLL_MS);
    return () => {
      clearTimeout(initialLoad);
      clearInterval(timer);
    };
  }, [loadMessages]);

  async function handleSend() {
    const content = text.trim();
    if (!content || sending) return;

    setSending(true);
    setSendError(null);
    try {
      const res = await apiFetch(`/chat/threads/${id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (res.status === 429) {
        setSendError("You're sending messages too fast. Wait a moment and try again.");
        return;
      }
      if (!res.ok) throw new Error(`Send failed: ${res.status}`);
      setText("");
      await loadMessages();
    } catch (err) {
      console.error(err);
      setSendError("Message failed to send. Try again.");
    } finally {
      setSending(false);
    }
  }

  if (loading) return <main><p>Loading chatÃ¢â‚¬Â¦</p></main>;

  return (
    <main>
      <p><Link href="/matches">Ã¢â€ Â Matches</Link></p>
      <h1>Chat</h1>
      {error && <p>{error}</p>}

      <div>
        {messages.length === 0 && <p>No messages yet. Say hi!</p>}
        {messages.map((m) => (
          <p key={m.id}>
            <strong>{m.sender_id === myId ? "You" : "Them"}:</strong> {m.content}
          </p>
        ))}
      </div>

      <div>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message"
          maxLength={2000}
        />
        <button disabled={sending || !text.trim()} onClick={handleSend}>
          Send
        </button>
      </div>
      {sendError && <p>{sendError}</p>}
    </main>
  );
}
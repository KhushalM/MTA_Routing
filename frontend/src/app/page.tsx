'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { Paperclip, Mic, CornerDownLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

function ChatBubble({ children, sender }: { children: React.ReactNode; sender: 'user' | 'ai' }) {
  return (
    <div className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`rounded-xl px-4 py-2 max-w-[70%] text-sm ${
        sender === 'user' ? 'bg-primary text-white' : 'bg-muted text-foreground'
      }`}>
        {children}
      </div>
    </div>
  );
}

export default function LandingPage() {
  const [messages, setMessages] = useState<{
    id: string;
    content: string;
    sender: 'user' | 'ai';
  }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user' as const,
    };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/conversation/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content, user_id: 'default' }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now().toString() + 'ai',
          content: data.response || '(No response)',
          sender: 'ai' as const,
        },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now().toString() + 'ai',
          content: 'Error fetching response.',
          sender: 'ai' as const,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} sender={msg.sender}>
            {msg.content}
          </ChatBubble>
        ))}
        {loading && (
          <ChatBubble sender="ai">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="animate-spin w-4 h-4" /> Generating response...
            </span>
          </ChatBubble>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form
        onSubmit={handleSend}
        className="flex gap-2 p-4 border-t bg-background items-center"
        autoComplete="off"
      >
        <Button type="button" tabIndex={-1} disabled>
          <Paperclip className="w-5 h-5" />
        </Button>
        <input
          type="text"
          className="flex-1 rounded border px-3 py-2 text-sm focus:outline-none focus:ring focus:border-primary bg-background"
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <Button type="button" tabIndex={-1} disabled>
          <Mic className="w-5 h-5" />
        </Button>
        <Button
          type="submit"
          className="bg-primary text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={loading || !input.trim()}
        >
          {loading ? <Loader2 className="animate-spin w-4 h-4" /> : <CornerDownLeft className="w-5 h-5" />}
        </Button>
      </form>
    </div>
  );
}

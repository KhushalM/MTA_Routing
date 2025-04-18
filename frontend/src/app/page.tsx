'use client';

import { useState, useRef, useEffect } from 'react';
import { Paperclip, Mic, CornerDownLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AIInputWithLoading } from '@/components/ui/ai-input-with-loading';
import { ResponseStream } from '@/components/ui/response-stream';
import MCPServerList, { MCPServer } from '@/components/MCPServerList';

interface Message {
  id: string;
  content: string | MCPServer[];
  sender: 'user' | 'ai';
}

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

// Helper: Parse Markdown MCP list into array of MCPServer
function parseMCPMarkdown(markdown: string): MCPServer[] | null {
  // Find the MCP list section
  const listMatch = markdown.match(/Here are available MCP servers[\s\S]*?repo:\n?([\s\S]*)/);
  if (!listMatch) return null;
  const list = listMatch[1];
  // Each line: - [name](link): description
  const regex = /- \[([^\]]+)\]\(([^\)]+)\): (.*)/g;
  const mcps: MCPServer[] = [];
  let match;
  while ((match = regex.exec(list))) {
    mcps.push({ name: match[1], link: match[2], description: match[3] });
  }
  return mcps.length > 0 ? mcps : null;
}

export default function LandingPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatboxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const chatbox = chatboxRef.current;
    if (!chatbox) return;
    const threshold = 100; // pixels from bottom
    const atBottom = chatbox.scrollHeight - chatbox.scrollTop <= chatbox.clientHeight + threshold;
    if (atBottom) {
      chatbox.scrollTop = chatbox.scrollHeight;
    }
  }, [messages, streamedResponse]);

  async function handleSend(input: string) {
    if (!input.trim()) return;
    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user' as const,
    };
    setMessages((msgs) => [...msgs, userMessage]);
    setLoading(true);
    setStreamedResponse(null);
    try {
      // For now, fetch the full response as before (not true streaming)
      const res = await fetch('http://localhost:8000/api/conversation/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content, user_id: 'default' }),
      });
      const data = await res.json();
      setStreamedResponse(data.response || '(No response)');
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now().toString() + 'ai',
          content: data.response || '(No response)',
          sender: 'ai' as const,
        },
      ]);
    } catch (err) {
      setStreamedResponse('Error fetching response.');
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
        <div
          id="chatbox"
          ref={chatboxRef}
          className="flex-1 overflow-y-auto p-20 pb-40"
          style={{ scrollBehavior: 'smooth' }}
        >
          {messages.map((msg, idx) => {
            // Handle MCP search results: if array, use directly; if string, try to parse as markdown
            if (msg.sender === 'ai') {
              let mcps: MCPServer[] | null = null;
              if (Array.isArray(msg.content)) {
                // Type guard: ensure every item is an MCPServer object
                if (msg.content.every(
                  (item) => typeof item === 'object' && item !== null && 'name' in item && 'link' in item && 'description' in item
                )) {
                  mcps = msg.content as MCPServer[];
                }
              } else if (typeof msg.content === 'string') {
                mcps = parseMCPMarkdown(msg.content);
              }
              if (mcps && mcps.length > 0) {
                return <MCPServerList key={msg.id} mcps={mcps} />;
              }
            }
            // For the last assistant message, show streaming if loading
            if (msg.sender === 'ai' && idx === messages.length - 1 && streamedResponse && loading) {
              return (
                <ChatBubble key={msg.id} sender={msg.sender}>
                  <ResponseStream textStream={streamedResponse} mode="typewriter" speed={30} />
                </ChatBubble>
              );
            }
            return (
              <ChatBubble key={msg.id} sender={msg.sender}>
                {typeof msg.content === 'string' ? msg.content : null}
              </ChatBubble>
            );
          })}
          {/* If loading but no assistant message yet, show streaming bubble */}
          {loading && !streamedResponse && (
            <ChatBubble sender="ai">
              <ResponseStream textStream={"..."} mode="typewriter" speed={40} />
            </ChatBubble>
          )}
          <div ref={messagesEndRef} />
        </div>
        {/* Make the input bar absolutely pinned to the bottom, static, and never scrollable */}
        <div className="w-full p-1 fixed bottom-0 left-0 z-20 shadow bg-background" style={{ maxWidth: '100vw', borderTop: 'none' }}>
          <AIInputWithLoading
            placeholder="Type your question..."
            onSubmit={handleSend}
            loadingDuration={loading ? 2000 : 1000}
          />
      </div>
    </div>
  );
}

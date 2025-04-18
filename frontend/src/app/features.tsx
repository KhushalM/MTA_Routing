import DisplayCards from '@/components/ui/display-cards';

export default function FeaturesPage() {
  // Example features, you can expand this list
  const features = [
    {
      title: 'Real-time AI Chat',
      description: 'Interact with an LLM-powered assistant that streams responses in real time.'
    },
    {
      title: 'Tool-using AI',
      description: 'The agent can use external tools (via MCP servers) to answer questions or perform actions.'
    },
    {
      title: 'Groq LLaMA 3 Integration',
      description: 'Harnesses the power of LLaMA 3 via the Groq API for fast, accurate answers.'
    },
    {
      title: 'Multi-Tool Orchestration',
      description: 'Supports multiple tool servers and dynamic tool selection per query.'
    },
    {
      title: 'Modern Chat UI',
      description: 'A beautiful, animated chat interface with typewriter streaming and fixed input bar.'
    },
    {
      title: 'Secure Configuration',
      description: 'Sensitive config and API keys are kept secure and out of the codebase.'
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background py-12">
      <h1 className="text-3xl font-bold mb-8">Features</h1>
      <div className="flex flex-col gap-6 w-full max-w-2xl">
        <DisplayCards cards={features} />
      </div>
    </div>
  );
}
    
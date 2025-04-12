# X-Query: MCP-Powered Agentic RAG for Twitter Analysis

An intelligent agent that uses Retrieval-Augmented Generation (RAG) and Model Context Protocol (MCP) to analyze, summarize, and provide insights on X (Twitter) trends and tweets.

## Features

- Real-time trend summarization
- Tweet search and analysis
- Intelligent agent with reasoning capabilities
- RAG-powered responses grounded in actual tweet content
- Clean, responsive UI

## Tech Stack

- **Backend**: Python, FastAPI, LangChain, MCP
- **Frontend**: Next.js, React, TailwindCSS
- **Data**: Twitter API v2 / NITTER
- **Models**: Supports various LLMs (Mistral, Llama, etc.)

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Twitter API credentials (or alternative data source)

### Installation

1. Clone the repository
2. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```
4. Set up environment variables (see `.env.example` files)
5. Run the application (see Development section)

## Development

### Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

## Project Structure

```
X_Query/
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Core application logic
│   │   ├── models/        # Data models
│   │   ├── services/      # Services (Twitter, LLM, etc.)
│   │   │   ├── twitter/   # Twitter API integration
│   │   │   └── llm/       # LLM integration
│   │   ├── tools/         # Agent tools
│   │   └── main.py        # Application entry point
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Example environment variables
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   ├── styles/        # CSS styles
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── .env.example       # Example environment variables
└── README.md              # Project documentation
```

## License

MIT

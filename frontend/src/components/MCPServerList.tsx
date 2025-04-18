import React, { useEffect, useState } from 'react';
import { CodeBlock, CodeBlockCode } from './CodeBlock';

export interface MCPServer {
  name: string;
  link: string;
  description: string;
}

interface MCPServerListProps {
  mcps: MCPServer[];
}

// Helper to get GitHub raw README.md URL from repo link
function getReadmeUrl(repoUrl: string): string | null {
  const match = repoUrl.match(/github.com\/(.+?)\/(.+?)(?:$|\/|#)/);
  if (!match) return null;
  const owner = match[1];
  const repo = match[2].replace(/\.git$/, '');
  return `https://raw.githubusercontent.com/${owner}/${repo}/main/README.md`;
}

// Helper to extract mcpServers config JSON block from README
function extractMcpConfig(readme: string): string | null {
  // Look for a code block containing "mcpServers" as a JSON object
  const codeBlockRegex = /```json[\r\n]+({[\s\S]*?\"mcpServers\"[\s\S]*?})[\r\n]+```/g;
  let match;
  while ((match = codeBlockRegex.exec(readme))) {
    try {
      const obj = JSON.parse(match[1]);
      if (obj && typeof obj === 'object' && obj.mcpServers) {
        // Pretty-print
        return JSON.stringify(obj, null, 2);
      }
    } catch (e) {
      continue;
    }
  }
  // Fallback: try to find an inline JSON block
  const inlineRegex = /({[\s\S]*?\"mcpServers\"[\s\S]*?})/g;
  while ((match = inlineRegex.exec(readme))) {
    try {
      const obj = JSON.parse(match[1]);
      if (obj && typeof obj === 'object' && obj.mcpServers) {
        return JSON.stringify(obj, null, 2);
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

const MCPServerList: React.FC<MCPServerListProps> = ({ mcps }) => {
  const [configs, setConfigs] = useState<Record<string, string | null>>({});
  useEffect(() => {
    let isMounted = true;
    async function fetchConfigs() {
      const results: Record<string, string | null> = {};
      await Promise.all(
        mcps.map(async (mcp) => {
          const readmeUrl = getReadmeUrl(mcp.link);
          if (!readmeUrl) {
            results[mcp.link] = null;
            return;
          }
          try {
            const res = await fetch(readmeUrl);
            if (!res.ok) {
              results[mcp.link] = null;
              return;
            }
            const text = await res.text();
            const config = extractMcpConfig(text);
            results[mcp.link] = config;
          } catch {
            results[mcp.link] = null;
          }
        })
      );
      if (isMounted) setConfigs(results);
    }
    fetchConfigs();
    return () => {
      isMounted = false;
    };
  }, [mcps]);

  if (!mcps || mcps.length === 0) {
    return <div>No MCP servers found.</div>;
  }
  return (
    <div className="mcp-server-list">
      <h2 className="text-xl font-bold mb-4">Available MCP Servers</h2>
      <ul className="list-disc pl-6">
        {mcps.map((mcp) => (
          <li key={mcp.link} className="mb-6">
            <a
              href={mcp.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline font-semibold"
            >
              {mcp.name}
            </a>
            <div className="text-gray-700 ml-2 text-sm mt-1">{mcp.description}</div>
            {configs[mcp.link] === undefined && (
              <div className="text-xs text-gray-400 mt-2">Searching for config...</div>
            )}
            {configs[mcp.link] && (
              <div className="mt-2">
                <div className="font-mono text-xs mb-1 text-gray-500">Server config:</div>
                <CodeBlock className="mb-2">
                  <CodeBlockCode code={configs[mcp.link] ?? ''} language="json" theme="github-dark" />
                </CodeBlock>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MCPServerList;

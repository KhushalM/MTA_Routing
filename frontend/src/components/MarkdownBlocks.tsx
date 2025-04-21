import React from "react";
import type { ChatBlock } from "../utils/markdownToBlocks";

export function MarkdownBlocks({ blocks }: { blocks: ChatBlock[] }) {
  return (
    <div className="space-y-2">
      {blocks.map((block, i) => {
        switch (block.type) {
          case "heading":
            if (block.level === 1) return <h1 key={i} className="text-2xl font-bold">{block.text}</h1>;
            if (block.level === 2) return <h2 key={i} className="text-xl font-semibold">{block.text}</h2>;
            return <h3 key={i} className="text-lg font-semibold">{block.text}</h3>;
          case "bold":
            return <span key={i} className="font-bold">{block.text}</span>;
          case "italic":
            return <span key={i} className="italic">{block.text}</span>;
          case "bullet":
            return <li key={i} className="ml-4 list-disc">{block.text}</li>;
          case "ordered":
            return <li key={i} className="ml-4 list-decimal">{block.number}. {block.text}</li>;
          case "checklist":
            return (
              <li key={i} className="ml-4 flex items-center list-none">
                <input type="checkbox" checked={block.checked} readOnly className="mr-2" />
                <span>{block.text}</span>
              </li>
            );
          case "code":
            return (
              <pre key={i} className="bg-muted p-2 rounded text-sm overflow-x-auto">
                <code>{block.code}</code>
              </pre>
            );
          case "inline_code":
            return <code key={i} className="bg-muted px-1 rounded text-sm">{block.code}</code>;
          case "link":
            return <a key={i} href={block.url} className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">{block.text}</a>;
          case "paragraph":
            return <p key={i}>{block.text}</p>;
          default:
            return null;
        }
      })}
    </div>
  );
}

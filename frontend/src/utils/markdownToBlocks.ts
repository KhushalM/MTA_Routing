// Utility to parse markdown into structured chat blocks for rendering
export type ChatBlock =
  | { type: 'heading', level: 1 | 2 | 3, text: string }
  | { type: 'bold', text: string }
  | { type: 'italic', text: string }
  | { type: 'bullet', text: string }
  | { type: 'ordered', text: string, number: number }
  | { type: 'checklist', text: string, checked: boolean }
  | { type: 'code', code: string, language?: string }
  | { type: 'inline_code', code: string }
  | { type: 'link', text: string, url: string }
  | { type: 'paragraph', text: string };

export function parseMarkdownToBlocks(markdown: string): ChatBlock[] {
  const lines = markdown.split('\n');
  const blocks: ChatBlock[] = [];
  let codeBlock: { language?: string, code: string } | null = null;

  lines.forEach((line, i) => {
    // Code block start/end
    const codeMatch = line.match(/^```(\w*)?/);
    if (codeMatch) {
      if (codeBlock) {
        blocks.push({ type: 'code', code: codeBlock.code, language: codeBlock.language });
        codeBlock = null;
      } else {
        codeBlock = { language: codeMatch[1], code: '' };
      }
      return;
    }
    if (codeBlock) {
      codeBlock.code += line + '\n';
      return;
    }
    // Headings
    if (/^### /.test(line)) blocks.push({ type: 'heading', level: 3, text: line.replace(/^### /, '') });
    else if (/^## /.test(line)) blocks.push({ type: 'heading', level: 2, text: line.replace(/^## /, '') });
    else if (/^# /.test(line)) blocks.push({ type: 'heading', level: 1, text: line.replace(/^# /, '') });
    // Checklist
    else if (/^- \[([ xX])\] (.*)/.test(line)) {
      const [, checked, text] = line.match(/^- \[([ xX])\] (.*)/)!;
      blocks.push({ type: 'checklist', text, checked: checked !== ' ' });
    }
    // Bullets
    else if (/^[-*] /.test(line)) blocks.push({ type: 'bullet', text: line.replace(/^[-*] /, '') });
    // Ordered
    else if (/^\d+\. /.test(line)) blocks.push({ type: 'ordered', text: line.replace(/^\d+\. /, ''), number: parseInt(line, 10) });
    // Inline code
    else if (/`([^`]+)`/.test(line)) blocks.push({ type: 'inline_code', code: line.match(/`([^`]+)`/)![1] });
    // Links
    else if (/\[([^\]]+)\]\(([^)]+)\)/.test(line)) {
      const [, text, url] = line.match(/\[([^\]]+)\]\(([^)]+)\)/)!;
      blocks.push({ type: 'link', text, url });
    }
    // Bold (double asterisks or double underscores)
    else if (/^(\*\*|__)(.+)(\*\*|__)$/g.test(line.trim())) {
      blocks.push({ type: 'bold', text: line.trim().replace(/^(\*\*|__)(.+)(\*\*|__)$/, '$2') });
    }
    // Inline bold (within a sentence)
    else if (/\*\*([^*]+)\*\*/.test(line)) {
      // Split line into segments and push as paragraph with bold segments
      const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
      parts.forEach(part => {
        if (/^\*\*[^*]+\*\*$/.test(part)) {
          blocks.push({ type: 'bold', text: part.replace(/^\*\*|\*\*$/g, '') });
        } else {
          blocks.push({ type: 'paragraph', text: part });
        }
      });
    }
    // Bold/Italic (simple)
    else if (/\*([^*]+)\*/.test(line)) blocks.push({ type: 'italic', text: line.match(/\*([^*]+)\*/)! [1] });
    // Paragraph
    else if (line.trim() !== '') blocks.push({ type: 'paragraph', text: line });
  });
  return blocks;
}

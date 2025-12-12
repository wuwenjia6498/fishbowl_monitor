import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

/**
 * 简单的 Markdown 渲染器
 * 支持: **加粗**, * 列表项
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // 空行
    if (!trimmedLine) {
      elements.push(<div key={index} className="h-2" />);
      return;
    }

    // 标题（以 ** 开头的行作为标题）
    if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
      const title = trimmedLine.slice(2, -2);
      elements.push(
        <h3 key={index} className="text-base font-bold text-foreground mt-4 mb-2">
          {title}
        </h3>
      );
      return;
    }

    // 列表项（以 * 或 - 开头）
    if (trimmedLine.match(/^[*-]\s+/)) {
      const content = trimmedLine.replace(/^[*-]\s+/, '');
      const rendered = renderInlineMarkdown(content);
      elements.push(
        <div key={index} className="flex gap-2 mb-2 ml-2">
          <span className="text-blue-500 mt-1.5 flex-shrink-0">•</span>
          <span className="text-sm text-muted-foreground flex-1 leading-relaxed">{rendered}</span>
        </div>
      );
      return;
    }

    // 普通段落
    const rendered = renderInlineMarkdown(trimmedLine);
    elements.push(
      <p key={index} className="text-sm text-muted-foreground mb-2 leading-relaxed">
        {rendered}
      </p>
    );
  });

  return <div className="space-y-1">{elements}</div>;
};

/**
 * 渲染行内 Markdown（加粗、emoji等）
 */
function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // 匹配 **文本** 格式的加粗
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    // 添加前面的普通文本
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // 添加加粗文本
    parts.push(
      <strong key={match.index} className="font-semibold text-foreground">
        {match[1]}
      </strong>
    );

    lastIndex = match.index + match[0].length;
  }

  // 添加剩余的文本
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}


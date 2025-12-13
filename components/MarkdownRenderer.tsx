import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

/**
 * 简单的 Markdown 渲染器
 * 支持: **加粗**, * 列表项, 表格
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inTable = false;
  let tableRows: string[] = [];
  let tableHeaders: string[] = [];

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // 空行
    if (!trimmedLine) {
      // 如果正在处理表格，结束表格
      if (inTable && tableRows.length > 0) {
        elements.push(renderTable(tableHeaders, tableRows, index));
        tableRows = [];
        tableHeaders = [];
        inTable = false;
      } else if (!inTable) {
        elements.push(<div key={index} className="h-2" />);
      }
      return;
    }

    // 检测表格行（以 | 开头和结尾）
    if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
      const cells = trimmedLine
        .slice(1, -1)
        .split('|')
        .map(cell => cell.trim());

      // 检测表头分隔行（包含 :--- 或 ---: 或 ---）
      if (cells.some(cell => /^:?-+:?$/.test(cell))) {
        // 这是表头分隔行，跳过
        inTable = true;
        return;
      }

      // 如果是表头（还没有表头且这是第一行）
      if (!inTable && tableHeaders.length === 0) {
        tableHeaders = cells;
        inTable = true;
        return;
      }

      // 表格数据行
      if (inTable) {
        tableRows.push(trimmedLine);
        return;
      }
    }

    // 如果之前有表格，先渲染表格
    if (inTable && tableRows.length > 0) {
      elements.push(renderTable(tableHeaders, tableRows, index - tableRows.length));
      tableRows = [];
      tableHeaders = [];
      inTable = false;
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

  // 处理文件末尾的表格
  if (inTable && tableRows.length > 0) {
    elements.push(renderTable(tableHeaders, tableRows, lines.length));
  }

  return <div className="space-y-1">{elements}</div>;
};

/**
 * 渲染表格
 */
function renderTable(headers: string[], rows: string[], keyBase: number): React.ReactNode {
  const parseRow = (row: string): string[] => {
    return row
      .slice(1, -1)
      .split('|')
      .map(cell => cell.trim());
  };

  // 检测对齐方式（从第一行数据推断，因为分隔行已被跳过）
  const alignments: ('left' | 'center' | 'right')[] = headers.map(() => 'left');

  return (
    <table key={keyBase} className="w-full border-collapse text-sm table-fixed">
      <thead className="bg-muted/50">
        <tr>
          {headers.map((header, idx) => (
            <th
              key={idx}
              className={`px-4 py-2.5 font-semibold text-foreground text-xs align-middle border-b border-border ${
                idx === 0 ? 'w-[45%] text-left' : 
                idx === 1 ? 'w-[30%] text-left' : 
                'w-[25%] text-right'
              }`}
            >
              <>{renderInlineMarkdown(header)}</>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIdx) => {
          const cells = parseRow(row);
          return (
            <tr key={rowIdx} className="border-b border-border last:border-b-0">
              {cells.map((cell, cellIdx) => (
                <td
                  key={cellIdx}
                  className={`px-4 py-2.5 text-sm align-middle ${
                    cellIdx === 0 ? 'font-medium' : 
                    cellIdx === 1 ? 'font-mono text-muted-foreground text-xs' : 
                    'text-right font-medium'
                  }`}
                >
                  <>{renderInlineMarkdown(cell)}</>
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

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


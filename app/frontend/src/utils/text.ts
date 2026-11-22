// Display helpers for curriculum names and search highlighting.

export function toTitleCase(str: string): string {
  if (!str) return '';
  return str
    .replace(/_/g, ' ')
    .split(' ')
    .map((w) => (w.length > 0 ? w.charAt(0).toUpperCase() + w.slice(1) : ''))
    .join(' ');
}

export function cleanLessonTitle(raw: string): string {
  if (!raw) return '';
  return raw
    .replace(/^Lesson\s*\d+\s*[:.-]\s*/i, '')
    .replace(/^\d+\s*[:.-]\s*/, '')
    .trim();
}

export interface HighlightPart {
  text: string;
  isMatch: boolean;
}

export function splitHighlight(text: string, query: string): HighlightPart[] {
  if (!text) return [];
  if (!query || !query.trim()) return [{ text, isMatch: false }];
  const terms = query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (!terms.length) return [{ text, isMatch: false }];
  const regex = new RegExp(`(${terms.join('|')})`, 'gi');
  const parts = text.split(regex);
  return parts
    .filter((p) => p.length > 0)
    .map((part) => ({
      text: part,
      isMatch: regex.test(part),
    }));
}

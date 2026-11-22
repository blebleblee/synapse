// Display helpers for curriculum names.

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

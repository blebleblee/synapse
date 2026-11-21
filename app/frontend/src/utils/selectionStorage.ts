/**
 * Client-side active selection storage and validation utility.
 * Persists and validates the most recently selected topic and lesson in localStorage.
 */

export interface StoredSelection {
  path: string;
  lessonId: string;
}

export const SELECTION_STORAGE_KEY = 'synapse_active_selection';

export function parseStoredSelection(raw: string | null): StoredSelection | null {
  if (!raw || typeof raw !== 'string') return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
    if (typeof parsed.path !== 'string' || !parsed.path.trim()) return null;
    const lessonId = typeof parsed.lessonId === 'string' && parsed.lessonId.trim()
      ? parsed.lessonId.trim()
      : 'all';
    return {
      path: parsed.path.trim(),
      lessonId
    };
  } catch {
    return null;
  }
}

export function getStoredSelection(): StoredSelection | null {
  try {
    const raw = localStorage.getItem(SELECTION_STORAGE_KEY);
    return parseStoredSelection(raw);
  } catch {
    return null;
  }
}

export function saveStoredSelection(path: string, lessonId?: string | null): void {
  if (!path || typeof path !== 'string' || !path.trim()) return;
  try {
    const payload: StoredSelection = {
      path: path.trim(),
      lessonId: (lessonId && typeof lessonId === 'string' && lessonId.trim()) ? lessonId.trim() : 'all'
    };
    localStorage.setItem(SELECTION_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Gracefully handle storage quota or disabled localStorage exceptions
  }
}

export function clearStoredSelection(): void {
  try {
    localStorage.removeItem(SELECTION_STORAGE_KEY);
  } catch {
    // Gracefully handle exceptions
  }
}

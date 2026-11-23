import { useEffect, useState } from 'react';

/** Reading languages the lesson reader offers. */
export type ReadingLang = 'en' | 'cs' | 'de' | 'es';

export const READING_LANG_NAMES: Record<ReadingLang, string> = {
  en: 'English', cs: 'Čeština', de: 'Deutsch', es: 'Español',
};

/** Short badge shown next to a translated lesson in the sidebar. */
export const READING_LANG_BADGE: Record<ReadingLang, string> = { en: 'EN', cs: 'CS', de: 'DE', es: 'ES' };

const STORAGE_KEY = 'synapse_reading_lang';
const CHANGED = 'synapse:reading-lang-changed';

export function isReadingLang(v: unknown): v is ReadingLang {
  return v === 'en' || v === 'cs' || v === 'de' || v === 'es';
}

/** The language the learner last chose to read in (English by default). */
export function loadReadingLang(): ReadingLang {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return isReadingLang(v) ? v : 'en';
  } catch {
    return 'en';
  }
}

export function saveReadingLang(lang: ReadingLang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    /* private window: the choice lasts for this page only */
  }
  window.dispatchEvent(new CustomEvent(CHANGED, { detail: lang }));
}

/** The remembered reading language, updated when any view changes it. */
export function useReadingLang(): ReadingLang {
  const [lang, setLang] = useState<ReadingLang>(loadReadingLang);
  useEffect(() => {
    const onChange = (e: Event) => {
      const next = (e as CustomEvent).detail;
      if (isReadingLang(next)) setLang(next);
    };
    window.addEventListener(CHANGED, onChange);
    return () => window.removeEventListener(CHANGED, onChange);
  }, []);
  return lang;
}

export type LessonTranslationState = 'cached' | 'queued' | 'running' | 'none';

export interface LessonTranslation {
  state: LessonTranslationState;
  job_id?: string;
}

export interface CourseTranslationStatus {
  lang: ReadingLang;
  lessons: Record<string, LessonTranslation>;
  labs: LessonTranslation | null;
}

export function isPending(t: LessonTranslation | null | undefined): boolean {
  return t?.state === 'queued' || t?.state === 'running';
}

/**
 * Translation state of each lesson of the open course in the reading
 * language. Refreshes when a translation starts or finishes anywhere in the
 * app, and every few seconds while one of its lessons is queued or running.
 * Never starts a translation.
 */
export function useCourseTranslationStatus(
  query: string | null,
  lang: ReadingLang,
  enabled: boolean,
): CourseTranslationStatus | null {
  // Kept with the course and language it answers, so switching either shows
  // nothing stale while the new request is in flight.
  const [result, setResult] = useState<{ key: string; status: CourseTranslationStatus } | null>(null);
  const key = `${query}|${lang}`;

  useEffect(() => {
    if (!enabled || !query || lang === 'en') return;
    let alive = true;
    let timer: number | null = null;
    const refresh = async () => {
      if (timer) window.clearTimeout(timer);
      let pending = false;
      try {
        const res = await fetch(`/api/translate/status?query=${encodeURIComponent(query)}&lang=${lang}`);
        if (res.ok && alive) {
          const data = (await res.json()) as CourseTranslationStatus;
          setResult({ key: `${query}|${lang}`, status: data });
          pending = Object.values(data.lessons).some(isPending) || isPending(data.labs);
        }
      } catch {
        /* backend restarting: keep the last known state */
      }
      if (alive && pending) timer = window.setTimeout(refresh, 3000);
    };
    const onChanged = () => { void refresh(); };
    window.addEventListener('synapse:translations-changed', onChanged);
    void refresh();
    return () => {
      alive = false;
      if (timer) window.clearTimeout(timer);
      window.removeEventListener('synapse:translations-changed', onChanged);
    };
  }, [query, lang, enabled]);

  const status = enabled && query && lang !== 'en' && result?.key === key ? result.status : null;
  return status;
}

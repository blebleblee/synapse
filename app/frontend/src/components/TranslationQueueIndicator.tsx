import { useEffect, useRef, useState } from 'react';
import { Languages, Loader2, Square } from 'lucide-react';
import type { TranslationJobInfo } from '../types';

const LANG_NAMES: Record<string, string> = { cs: 'Čeština', de: 'Deutsch', es: 'Español', ru: 'Русский' };

/**
 * Status-bar entry for background lesson translations: what is running, what
 * is queued, and a Stop button for each. Hidden when nothing is active.
 */
export function TranslationQueueIndicator() {
  const [jobs, setJobs] = useState<TranslationJobInfo[]>([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    let alive = true;
    let lastActive = false;
    const refresh = async (): Promise<boolean> => {
      try {
        const res = await fetch('/api/translate/jobs');
        if (res.ok && alive) {
          const list = ((await res.json()).jobs || []) as TranslationJobInfo[];
          if (alive) setJobs(list);
          lastActive = list.some((j) => j.status === 'queued' || j.status === 'running');
        }
      } catch {
        /* backend restarting: keep the last known list */
      }
      return lastActive;
    };
    const tick = async () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
      const active = await refresh();
      if (alive) timerRef.current = window.setTimeout(tick, active ? 1500 : 10000);
    };
    const onChanged = () => { void tick(); };
    window.addEventListener('synapse:translations-changed', onChanged);
    void tick();
    return () => {
      alive = false;
      if (timerRef.current) window.clearTimeout(timerRef.current);
      window.removeEventListener('synapse:translations-changed', onChanged);
    };
  }, []);

  const active = jobs.filter((j) => j.status === 'queued' || j.status === 'running');
  const running = active.find((j) => j.status === 'running');
  const queued = active.filter((j) => j.status === 'queued').length;
  if (active.length === 0) return null;

  const stop = async (id: string) => {
    try {
      await fetch(`/api/translate/jobs/${id}`, { method: 'DELETE' });
    } finally {
      window.dispatchEvent(new Event('synapse:translations-changed'));
    }
  };

  const summary = running
    ? `Translating ${running.title}${running.total ? ` (${Math.min(running.done + 1, running.total)}/${running.total})` : ''}`
    : 'Translations queued';

  return (
    <div className="translation-queue">
      <button
        type="button"
        className="translation-queue-toggle"
        onClick={() => setOpen((o) => !o)}
        title="Show background translations"
      >
        {running ? <Loader2 size={12} className="animate-spin" /> : <Languages size={12} />}
        <span className="translation-queue-summary">{summary}</span>
        {queued > 0 && <span className="translation-queue-count">+{queued} queued</span>}
      </button>
      {open && (
        <div className="translation-queue-panel" role="dialog" aria-label="Background translations">
          {active.map((j) => (
            <div key={j.id} className="translation-queue-row">
              <div className="translation-queue-info">
                <span className="translation-queue-title" title={j.title}>{j.title}</span>
                <span className="translation-queue-meta">
                  {LANG_NAMES[j.target_lang] || j.target_lang} ·{' '}
                  {j.status === 'running'
                    ? j.stopping ? 'stopping after this section' : `section ${Math.min(j.done + 1, j.total)} of ${j.total}`
                    : `queued${j.position ? ` #${j.position}` : ''}`}
                </span>
              </div>
              {!j.stopping && (
                <button type="button" className="ai-stop-btn" onClick={() => stop(j.id)} title="Stop this translation">
                  <Square size={9} className="fill-current" />
                  <span>Stop</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

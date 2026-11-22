import { X } from 'lucide-react';

export type NoticeKind = 'error' | 'success' | 'info';
export interface Notice {
  id: number;
  kind: NoticeKind;
  text: string;
}

interface NoticeStackProps {
  notices: Notice[];
  onDismiss: (id: number) => void;
}

/** Short messages in the bottom-right corner: results and failures of actions. */
export function NoticeStack({ notices, onDismiss }: NoticeStackProps) {
  if (notices.length === 0) return null;
  return (
    <div className="notice-stack" aria-live="polite">
      {notices.map((n) => (
        <div key={n.id} className={`notice notice-${n.kind}`} role={n.kind === 'error' ? 'alert' : 'status'}>
          <span className="notice-text">{n.text}</span>
          <button type="button" className="notice-close" aria-label="Dismiss" onClick={() => onDismiss(n.id)}>
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

import { useEffect, useRef } from 'react';

/**
 * Closes a dialog when Escape is pressed. Listens on the window in the capture
 * phase, so it also works while the terminal (xterm swallows keys) or another
 * widget has focus, and stops the key there so nothing behind the dialog sees it.
 */
export function useEscapeToClose(onClose: () => void, enabled = true): void {
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    if (!enabled) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.defaultPrevented) return;
      e.preventDefault();
      e.stopPropagation();
      onCloseRef.current();
    };
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [enabled]);
}

// Lesson code goes to the terminal as typed text. On the host shell it is
// wrapped in a bracketed paste so it is only typed, never run. Lessons can
// come from imported packs (untrusted): an ESC[201~ inside a snippet would
// end the paste early and the following newline would run the rest. Control
// characters other than tab and newline are therefore removed.
export function terminalSafeText(command: string): string {
  return command
    .replace(/\r\n?/g, '\n')
    // eslint-disable-next-line no-control-regex
    .replace(/[\x00-\x08\x0b-\x1f\x7f-\x9f]/g, '')
    .trim();
}

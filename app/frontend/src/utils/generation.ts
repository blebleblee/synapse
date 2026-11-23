// What a finished /api/generate call means for the learner. The UI used to
// ignore the results, so a run where every file failed (no model reachable)
// just reloaded the course without a word.

export interface GenerationSummary {
  kind: 'success' | 'error' | 'info';
  text: string;
}

export function summarizeGeneration(
  results: Record<string, boolean> | undefined,
  skipped: string[] | undefined,
  force: boolean,
): GenerationSummary {
  const entries = Object.entries(results || {});
  const kept = new Set(skipped || []);
  const written = entries.filter(([, ok]) => ok).map(([name]) => name);
  const failed = entries.filter(([name, ok]) => !ok && !kept.has(name)).map(([name]) => name);
  if (failed.length) {
    const after = force
      ? (written.length ? '' : ' The existing lessons were kept.')
      : ' Run it again to generate the missing files.';
    return {
      kind: 'error',
      text: `${failed.length} file(s) could not be generated: ${failed.join(', ')}. Check that an AI model is reachable (Settings → AI models).${after}`,
    };
  }
  if (written.length) return { kind: 'success', text: `Generated ${written.length} file(s).` };
  return { kind: 'info', text: 'Nothing to generate: every file already exists.' };
}

/**
 * Turns a failed fetch response into a sentence a learner can act on.
 * The backend reports problems as `{ detail: "..." }`.
 */
export async function failureMessage(res: Response, action: string): Promise<string> {
  let detail = '';
  try {
    const data = await res.clone().json();
    if (typeof data?.detail === 'string') detail = data.detail;
    else if (Array.isArray(data?.detail)) detail = data.detail.map((d: any) => d?.msg).filter(Boolean).join('; ');
  } catch {
    /* not JSON */
  }
  return describeFailure(action, res.status, detail);
}

export function describeFailure(action: string, status: number, detail = ''): string {
  const reason = detail || (status === 503
    ? 'no AI model is reachable. Check the AI Engine settings.'
    : status === 401
      ? 'you are not signed in.'
      : `the server answered ${status}.`);
  return `${action} failed: ${reason}`;
}

/** For network errors (server stopped, connection dropped). */
export function networkFailure(action: string, err: unknown): string {
  const msg = err instanceof Error ? err.message : String(err);
  return `${action} failed: could not reach the Synapse backend (${msg}).`;
}

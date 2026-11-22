import test from 'node:test';
import assert from 'node:assert/strict';
import { speakText, stopSpeaking } from './speech.ts';

// Minimal browser stand-ins: a slow narration request and an Audio element.
function installFakes() {
  const played: string[] = [];
  let resolveFetch: (r: Response) => void = () => {};
  globalThis.fetch = ((_url: string, init?: RequestInit) => new Promise<Response>((resolve, reject) => {
    resolveFetch = resolve;
    init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
  })) as typeof fetch;
  (globalThis as any).URL.createObjectURL = () => 'blob:x';
  (globalThis as any).URL.revokeObjectURL = () => {};
  (globalThis as any).Audio = class {
    src: string; paused = true; ended = false; currentTime = 0;
    onplay: null | (() => void) = null; onended = null; onerror = null;
    constructor(src: string) { this.src = src; }
    play() { played.push(this.src); this.paused = false; this.onplay?.(); return Promise.resolve(); }
    pause() { this.paused = true; }
  };
  const respond = () => resolveFetch(new Response(new Uint8Array(2000), { status: 200 }));
  return { played, respond };
}

test('stopping while the audio is being prepared cancels it: nothing plays later', async () => {
  const { played, respond } = installFakes();
  const events: string[] = [];
  const pending = speakText('# Lesson A', () => events.push('start'), () => events.push('end'), () => events.push('preparing'));
  stopSpeaking();
  respond();
  await pending;
  assert.deepEqual(played, []);
  assert.deepEqual(events, ['preparing']);
});

test('audio plays once it is ready', async () => {
  const { played, respond } = installFakes();
  const events: string[] = [];
  const pending = speakText('# Lesson B', () => events.push('start'), () => events.push('end'), () => events.push('preparing'));
  respond();
  await pending;
  assert.equal(played.length, 1);
  assert.deepEqual(events, ['preparing', 'start']);
  stopSpeaking();
});

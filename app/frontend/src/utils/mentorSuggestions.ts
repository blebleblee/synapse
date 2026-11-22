/**
 * Starter prompts in the empty mentor panel. Terminal and debugging prompts
 * only make sense in hands-on technical courses; a drawing or history course
 * got "Inspect my live terminal output" and "misconceptions most engineers
 * have".
 */
export interface MentorSuggestion {
  label: string;
  prompt: string;
}

const TERMINAL_DOMAINS = new Set(['computing', 'engineering']);

export function mentorSuggestions(domain: string | undefined, topicName: string): MentorSuggestion[] {
  const about = topicName ? ` ${topicName}` : ' this topic';
  if (domain && TERMINAL_DOMAINS.has(domain)) {
    return [
      { label: 'Inspect my terminal output and diagnose my last error', prompt: 'Inspect my live terminal output and diagnose what caused my last error or command failure.' },
      { label: 'Explain the core invariants and failure modes', prompt: `What are the core invariants of${about} and where does it break in practice?` },
      { label: 'Give me a real-world debugging scenario', prompt: `Give me a challenging real-world debugging scenario on${about} to test my mental model.` },
      { label: 'What do people commonly get wrong?', prompt: `What are the subtle misconceptions people commonly have about${about}?` },
    ];
  }
  return [
    { label: 'Explain the key ideas of this lesson simply', prompt: 'Explain the key ideas of this lesson simply, with one concrete example.' },
    { label: 'Give me a practice exercise', prompt: `Give me a short practice exercise on${about}, then wait for my answer.` },
    { label: 'What do beginners commonly get wrong?', prompt: `What do beginners commonly get wrong about${about}, and how do I avoid it?` },
    { label: 'Quiz me with three questions', prompt: 'Ask me three questions about this lesson, one at a time, and tell me how I did.' },
  ];
}

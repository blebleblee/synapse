/**
 * Socratic Audio / Voice Synthesis Helper
 * Utilizes native browser Web Speech API (speechSynthesis) for zero-latency, private TTS.
 */

let activeUtterance: SpeechSynthesisUtterance | null = null;

export const speakText = (
  text: string,
  onStart?: () => void,
  onEnd?: () => void
) => {
  if (!('speechSynthesis' in window)) {
    console.warn('Web Speech API is not supported in this browser.');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Strip markdown formatting, code blocks, and math for natural speech
  const clean = text
    .replace(/```[\s\S]*?```/g, ' Code snippet omitted. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\$\$[\s\S]*?\$\$/g, ' Mathematical equation. ')
    .replace(/\$([^\$]+)\$/g, '$1')
    .replace(/#+\s/g, '')
    .replace(/\*+/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .trim();

  if (!clean) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.02;
  utterance.pitch = 1.0;

  // Pick preferred natural voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(
    (v) =>
      v.lang.startsWith('en') &&
      (v.name.includes('Natural') ||
        v.name.includes('Neural') ||
        v.name.includes('Samantha') ||
        v.name.includes('Daniel') ||
        v.name.includes('Google US'))
  );
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  utterance.onstart = () => {
    if (onStart) onStart();
  };

  utterance.onend = () => {
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  utterance.onerror = () => {
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  activeUtterance = utterance;
  window.speechSynthesis.speak(utterance);
};

export const stopSpeaking = () => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  activeUtterance = null;
};

export const isSpeaking = () => {
  return 'speechSynthesis' in window && (window.speechSynthesis.speaking || activeUtterance !== null);
};

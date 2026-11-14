/**
 * Socratic Audio / Voice Synthesis Helper
 * Streams studio-grade Neural Audio (MP3) from the Synapse backend (/api/audio/narrate)
 * with automatic fallback to native Web Speech API (speechSynthesis) if offline.
 */

let activeAudio: HTMLAudioElement | null = null;
let activeAudioUrl: string | null = null;
let activeUtterance: SpeechSynthesisUtterance | null = null;

function fallbackWebSpeech(
  text: string,
  onStart?: () => void,
  onEnd?: () => void
) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();

  // Strip markdown formatting, code blocks, and math for natural speech
  const clean = text
    .replace(/```[\s\S]*?```/g, ' Code snippet omitted. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\$\$[\s\S]*?\$\$/g, ' Mathematical equation. ')
    .replace(/\$([^$]+)\$/g, '$1')
    .replace(/#+\s/g, '')
    .replace(/\*+/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();

  if (!clean) {
    if (onEnd) onEnd();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.0;
  utterance.pitch = 0.95;

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
}

export const speakText = async (
  text: string,
  onStart?: () => void,
  onEnd?: () => void
) => {
  stopSpeaking();

  const preferredVoice = typeof window !== 'undefined'
    ? localStorage.getItem('synapse_narrator_voice') || 'en-US-GuyNeural'
    : 'en-US-GuyNeural';

  try {
    const response = await fetch('/api/audio/narrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        voice: preferredVoice,
        pitch: '-10Hz',
        rate: '-4%'
      })
    });

    if (!response.ok) {
      throw new Error(`Neural audio endpoint returned status ${response.status}`);
    }

    const blob = await response.blob();
    if (blob.size < 500) {
      throw new Error('Received invalid audio response');
    }

    const audioUrl = URL.createObjectURL(blob);
    activeAudioUrl = audioUrl;
    const audio = new Audio(audioUrl);
    activeAudio = audio;

    audio.onplay = () => {
      if (onStart) onStart();
    };

    audio.onended = () => {
      stopSpeaking();
      if (onEnd) onEnd();
    };

    audio.onerror = (e) => {
      console.warn('[Audio] Streaming error, falling back to browser synthesis:', e);
      stopSpeaking();
      fallbackWebSpeech(text, onStart, onEnd);
    };

    await audio.play();
  } catch (err) {
    console.warn('[Audio] Backend neural speech unavailable, falling back:', err);
    fallbackWebSpeech(text, onStart, onEnd);
  }
};

export const stopSpeaking = () => {
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }
  if (activeAudioUrl) {
    URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = null;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  activeUtterance = null;
};

export const isSpeaking = () => {
  const isAudioPlaying = activeAudio !== null && !activeAudio.paused && !activeAudio.ended;
  const isSynthSpeaking = typeof window !== 'undefined' && 'speechSynthesis' in window && window.speechSynthesis.speaking;
  return Boolean(isAudioPlaying || isSynthSpeaking || activeUtterance !== null);
};

import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import { sanitizeHtml } from '../utils/markdownRenderer';
import { toTitleCase } from '../utils/text';
import { mentorSuggestions } from '../utils/mentorSuggestions';
import {
  Send,
  Bot,
  User,
  MessageSquare,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Trash2,
  BookOpen,
  HelpCircle,
  X
} from 'lucide-react';
import type { ChatMessage, TopicDetails } from '../types';
import { getUIStrings } from '../utils/i18n';

interface TutorChatProps {
  topic: TopicDetails | null;
  activeLessonTitle?: string | null;
  history: ChatMessage[];
  isChatting: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onClearChat?: () => void;
  mentorConnected: 'checking' | 'connected' | 'error';
  /** Model that answers; differs from configuredMentorModel when it is a fallback. */
  mentorModel?: string | null;
  mentorFallback?: boolean;
  configuredMentorModel?: string | null;
  targetLanguage?: string;
  onDismissMessage?: (index: number) => void;
}

export const TutorChat: React.FC<TutorChatProps> = ({
  topic,
  activeLessonTitle,
  history,
  isChatting,
  onSendMessage,
  onClearChat,
  mentorConnected,
  mentorModel,
  mentorFallback = false,
  configuredMentorModel,
  targetLanguage,
  onDismissMessage,
}) => {
  const ui = getUIStrings(targetLanguage);
  // ... existing component logic ...
  // The course as the sidebar names it ("AI Foundations"), not its folder name.
  const topicName = topic ? toTitleCase(topic.display_title || topic.subtopic) : '';
  const [input, setInput] = useState('');
  const [personaExpanded, setPersonaExpanded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [chatWidth, setChatWidth] = useState<number>(() => {
    const saved = localStorage.getItem('synapse_chat_width');
    return saved ? parseInt(saved, 10) : 480;
  });
  const isDraggingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history, isChatting]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newWidth = window.innerWidth - moveEvent.clientX;
      if (newWidth >= 280 && newWidth <= window.innerWidth * 0.75) {
        setChatWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      setChatWidth((curr) => {
        localStorage.setItem('synapse_chat_width', curr.toString());
        return curr;
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isChatting) return;
    const msg = input.trim();
    setInput('');
    await onSendMessage(msg);
  };

  const handleSuggestionClick = (prompt: string) => {
    if (!isChatting) {
      onSendMessage(prompt);
    }
  };

  const suggestions = mentorSuggestions(topic?.domain, topicName);

  return (
    <aside className="chat-sidebar" style={{ width: `${chatWidth}px` }}>
      {/* Draggable Vertical Resize Handle */}
      <div
        className={`chat-resize-handle ${isDragging ? 'active' : ''}`}
        onMouseDown={handleMouseDown}
        title="Drag to resize AI chat panel"
      />

      <div className="chat-header">
        <div className="chat-header-top">
          <div
            className="persona-info clickable"
            onClick={() => setPersonaExpanded((prev) => !prev)}
            title={personaExpanded ? "Collapse Socratic mentor directives" : "Expand full Socratic mentor directives"}
          >
            <div
              className="persona-avatar-wrapper"
              title={`Mentor ${mentorConnected === 'connected' ? 'online' : mentorConnected === 'checking' ? 'connecting' : 'offline'}${mentorModel ? ` (${mentorModel})` : ''}${mentorFallback ? `. ${configuredMentorModel} is not available, so ${mentorModel} answers instead.` : ''}`}
            >
              <Bot size={16} className="persona-icon" />
              <span className={`persona-online-dot ${mentorConnected}${mentorConnected === 'connected' && mentorFallback ? ' fallback' : ''}`} />
            </div>
            <div className="persona-text">
              <div className="persona-label-row">
                <span className="persona-label" title={topicName ? `Socratic Mentor for ${topicName}` : 'Socratic Mentor'}>Socratic Mentor</span>
                {topic?.domain && (
                  <span className="persona-topic-tag" title={`Domain: ${topic.domain}`}>
                    {topic.domain.replace(/_/g, ' ')}
                  </span>
                )}
                {mentorModel && (
                  <span className="mentor-model-badge">({mentorModel.split(':')[0]}{mentorFallback ? ', fallback' : ''})</span>
                )}
                {personaExpanded ? <ChevronUp size={12} className="persona-chevron" /> : <ChevronDown size={12} className="persona-chevron" />}
              </div>
            </div>
          </div>

          <div className="chat-header-top-actions">
            {onClearChat && (
              <button
                type="button"
                className="chat-action-btn"
                onClick={async () => {
                  if (confirm(ui.clearChat + '?')) {
                    try {
                      // Only this topic's saved chat (owner decision); Settings
                      // → Clear chat sessions removes every topic's.
                      const qs = topic?.path ? `?query=${encodeURIComponent(topic.path)}` : '';
                      await fetch(`/api/chat/session${qs}`, { method: 'DELETE' });
                      onClearChat();
                    } catch (err) {
                      console.error('Failed to clear sessions:', err);
                    }
                  }
                }}
                disabled={history.length === 0}
                title={ui.clearChat}
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>

        {/* Active Lesson Context Bar */}
        {activeLessonTitle && (
          <div className="chat-lesson-context-bar">
            <div className="context-bar-header">
              <BookOpen size={11} className="context-icon" />
              <span className="context-title" title={activeLessonTitle}>{activeLessonTitle}</span>
            </div>
            <div className="context-quick-chips">
              <button
                type="button"
                className="context-quick-chip"
                onClick={() => onSendMessage(`Please explain the core invariants of '${activeLessonTitle}' in 2-3 direct sentences.`)}
                title="Ask mentor to explain this lesson"
              >
                <Lightbulb size={10} />
                <span>{ui.chipExplain}</span>
              </button>
              <button
                type="button"
                className="context-quick-chip"
                onClick={() => onSendMessage(`Can you give me a practical, hands-on example of '${activeLessonTitle}'?`)}
                title="Ask for a practical example"
              >
                <Sparkles size={10} />
                <span>{ui.chipExample}</span>
              </button>
              <button
                type="button"
                className="context-quick-chip"
                onClick={() => onSendMessage(`What is the most common pitfall or misconception when applying '${activeLessonTitle}'?`)}
                title="Ask about common pitfalls"
              >
                <HelpCircle size={10} />
                <span>{ui.chipPitfall}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {personaExpanded && topic?.persona && (
        <div className="persona-expanded-card">
          <div className="persona-expanded-header">
            <Sparkles size={13} className="sparkle-gold" />
            <span>Mentor Directives & Epistemic Tone</span>
          </div>
          <div className="persona-expanded-body">
            {topic.persona}
          </div>
        </div>
      )}

      <div className="chat-messages">
        {history.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-header">
              <MessageSquare size={28} className="chat-empty-icon" />
              <h3>Socratic Inquiry</h3>
            </div>
            <p>
              Ask about anything in the lesson, try out your own ideas, or ask for examples and exercises.
              {topic ? ` Current context: ${topicName}.` : ' Open any topic to explore with context.'}
            </p>

            <div className="chat-suggestions">
              <span className="suggestions-title">
                <Lightbulb size={12} /> Suggested Prompts:
              </span>
              {suggestions.map((s) => (
                <button key={s.label} className="suggestion-chip" onClick={() => handleSuggestionClick(s.prompt)}>
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          history.map((msg, idx) => {
            const isError = msg.content.includes('⚠️ **Unable to connect to AI Mentor**');
            return (
              <div key={idx} className={`chat-bubble ${msg.role} ${isError ? 'error-bubble' : ''}`}>
                <div className="bubble-header">
                  <div className="bubble-author">
                    {msg.role === 'student' ? (
                      <>
                        <User size={13} />
                        <span>You</span>
                      </>
                    ) : (
                      <>
                        <Bot size={13} />
                        <span>Tutor</span>
                      </>
                    )}
                  </div>
                  {isError && onDismissMessage && (
                    <button
                      type="button"
                      className="chat-dismiss-btn"
                      onClick={() => onDismissMessage(idx)}
                      title="Dismiss error notice"
                    >
                      <X size={12} />
                      <span>Dismiss</span>
                    </button>
                  )}
                </div>
                <div
                  className="bubble-content"
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(marked.parse(msg.content) as string) }}
                />
              </div>
            );
          })
        )}

        {isChatting && (
          <div className="chat-bubble tutor thinking">
            <div className="bubble-header">
              <Bot size={13} />
              <span>Tutor</span>
            </div>
            <div className="typing-indicator">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder={topic ? ui.askMentor : ui.mentorPlaceholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isChatting}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isChatting}
          title={ui.send}
        >
          <Send size={15} />
        </button>
      </form>
    </aside>
  );
};

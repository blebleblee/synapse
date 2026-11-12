import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import {
  Send,
  Bot,
  User,
  MessageSquare,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Terminal,
  Trash2
} from 'lucide-react';
import type { ChatMessage, TopicDetails } from '../types';

interface TutorChatProps {
  topic: TopicDetails | null;
  history: ChatMessage[];
  isChatting: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onClearChat?: () => void;
  isTerminalConnected?: boolean;
}

export const TutorChat: React.FC<TutorChatProps> = ({
  topic,
  history,
  isChatting,
  onSendMessage,
  onClearChat,
  isTerminalConnected = false,
}) => {
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

  const getDomainMentorRole = (domain?: string) => {
    switch (domain) {
      case 'computing':
        return 'Systems Software & Kernel Architect';
      case 'formal_sciences':
        return 'Pure Mathematics & Formal Logic Mentor';
      case 'natural_sciences':
        return 'Physics & Scientific Reasoning Specialist';
      case 'engineering':
        return 'Robotics & Hardware Systems Engineer';
      case 'crafts':
        return 'Mechanism Design & CAD Specialist';
      case 'arts':
        return 'Music Theory & Audio DSP Specialist';
      case 'business':
        return 'Economics & Systems Thinking Mentor';
      case 'humanities':
        return 'Cognitive Science & Epistemology Mentor';
      default:
        return 'Socratic Technical Mentor';
    }
  };

  const personaRole = topic?.domain
    ? getDomainMentorRole(topic.domain)
    : 'Universal Socratic Mentor';

  return (
    <aside className="chat-sidebar" style={{ width: `${chatWidth}px` }}>
      {/* Draggable Vertical Resize Handle */}
      <div
        className={`chat-resize-handle ${isDragging ? 'active' : ''}`}
        onMouseDown={handleMouseDown}
        title="Drag to resize AI chat panel"
      />

      <div className="chat-header">
        <div className="chat-header-main">
          <div
            className="persona-info clickable"
            onClick={() => setPersonaExpanded((prev) => !prev)}
            title={personaExpanded ? "Collapse Socratic mentor directives" : "Expand full Socratic mentor directives"}
          >
            <div className="persona-avatar-wrapper">
              <Bot size={18} className="persona-icon" />
              <span className="persona-online-dot" />
            </div>
            <div className="persona-text">
              <div className="persona-label-row">
                <span className="persona-label">Socratic Mentor</span>
                <span className="persona-badge">{topic?.domain ? topic.domain.replace('_', ' ') : 'Polymath'}</span>
                {personaExpanded ? <ChevronUp size={12} className="persona-chevron" /> : <ChevronDown size={12} className="persona-chevron" />}
              </div>
              <span className="persona-role" title={personaRole}>
                {personaRole}
              </span>
            </div>
          </div>

          <div className="chat-header-actions">
            <span
              className={`terminal-link-badge ${isTerminalConnected ? 'online' : 'offline'}`}
              title={
                isTerminalConnected
                  ? "Live Terminal Output Linked (Mentor automatically reads your terminal output & errors)"
                  : "Terminal Disconnected (Click terminal drawer to reconnect)"
              }
            >
              <Terminal size={11} />
              <span>{isTerminalConnected ? "Terminal Live" : "Terminal Offline"}</span>
            </span>
            {onClearChat && (
              <button
                type="button"
                className="chat-action-btn"
                onClick={onClearChat}
                disabled={history.length === 0}
                title="Clear conversation history"
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>

        {topic && (
          <div className="chat-subject-row" title={`Active Topic: ${topic.display_title || topic.subtopic}`}>
            <span className="chat-subject-label">Subject:</span>
            <span className="chat-subject-title">{topic.display_title || topic.subtopic?.replace(/_/g, ' ')}</span>
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
              Ask deep questions, test operational edge-cases, or request counter-examples.
              {topic ? ` Current context: ${topic.subtopic.replace(/_/g, ' ')}.` : ' Open any topic to explore with context.'}
            </p>

            <div className="chat-suggestions">
              <span className="suggestions-title">
                <Lightbulb size={12} /> Suggested Prompts:
              </span>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick("Inspect my live terminal output and diagnose what caused my last error or command failure.")}
              >
                Inspect my live terminal output and diagnose my last error
              </button>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(topic ? `What are the core architectural invariants of ${topic.subtopic.replace(/_/g, ' ')} and where does it break in production?` : "Explain the core architectural invariants of modern distributed systems.")}
              >
                Explain the core architectural invariants and failure modes
              </button>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(topic ? `Give me a challenging real-world debugging scenario on ${topic.subtopic.replace(/_/g, ' ')} to test my mental model.` : "Give me a challenging real-world debugging scenario to test my mental model.")}
              >
                Give me a challenging real-world debugging scenario
              </button>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(topic ? `What are the subtle misconceptions most engineers have about ${topic.subtopic.replace(/_/g, ' ')}?` : "What are the subtle misconceptions most engineers have about this topic?")}
              >
                What are the subtle misconceptions most engineers have?
              </button>
            </div>
          </div>
        ) : (
          history.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
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
              </div>
              <div
                className="bubble-content"
                dangerouslySetInnerHTML={{ __html: marked.parse(msg.content) as string }}
              />
            </div>
          ))
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
          placeholder={topic ? `Ask ${personaRole}...` : "Ask Socratic Mentor across 12 domains or about your terminal..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isChatting}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isChatting}
          title="Send inquiry (Enter)"
        >
          <Send size={15} />
        </button>
      </form>
    </aside>
  );
};

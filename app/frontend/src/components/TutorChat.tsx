import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import { Send, Bot, User, MessageSquare, Lightbulb, BookmarkCheck } from 'lucide-react';
import type { ChatMessage, TopicDetails } from '../types';

interface TutorChatProps {
  topic: TopicDetails | null;
  history: ChatMessage[];
  isChatting: boolean;
  onSendMessage: (message: string) => Promise<void>;
}

export const TutorChat: React.FC<TutorChatProps> = ({
  topic,
  history,
  isChatting,
  onSendMessage,
}) => {
  const [input, setInput] = useState('');
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

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= 320 && newWidth <= window.innerWidth * 0.6) {
        setChatWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        document.body.style.cursor = '';
        localStorage.setItem('synapse_chat_width', chatWidth.toString());
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [chatWidth]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isChatting || !topic) return;
    const msg = input.trim();
    setInput('');
    await onSendMessage(msg);
  };

  const handleSuggestionClick = (prompt: string) => {
    if (!isChatting && topic) {
      onSendMessage(prompt);
    }
  };

  const personaRole = topic?.persona
    ? topic.persona.split('**')[1] || 'Domain Expert & Socratic Mentor'
    : 'Domain Expert & Socratic Mentor';

  return (
    <aside className="chat-sidebar" style={{ width: `${chatWidth}px` }}>
      {/* Draggable Vertical Resize Handle */}
      <div
        className="chat-resize-handle"
        onMouseDown={(e) => {
          e.preventDefault();
          isDraggingRef.current = true;
          document.body.style.cursor = 'ew-resize';
        }}
        title="Drag to resize AI chat panel"
      />

      <div className="chat-header">
        <div className="persona-info">
          <Bot size={22} className="persona-icon" />
          <div className="persona-text">
            <span className="persona-label">Socratic Mentor</span>
            <span className="persona-role" title={personaRole}>
              {personaRole}
            </span>
          </div>
        </div>

        <div className="chat-header-actions">
          <div className="autosave-badge" title="All discussions are automatically saved to disk and versioned in Git">
            <BookmarkCheck size={12} className="autosave-icon" />
            <span>Auto-Saved</span>
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {history.length === 0 ? (
          <div className="chat-empty">
            <MessageSquare size={36} className="chat-empty-icon" />
            <h3>Socratic Inquiry</h3>
            <p>
              Ask deep questions, test operational edge-cases, or request counter-examples.
            </p>

            <div className="chat-suggestions">
              <span className="suggestions-title">
                <Lightbulb size={12} /> Suggested Prompts:
              </span>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick("Explain the core architectural invariants and where this commonly breaks in production.")}
              >
                Explain the core architectural invariants and failure modes
              </button>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick("Give me a challenging real-world debugging scenario to test my mental model.")}
              >
                Give me a challenging real-world debugging scenario
              </button>
              <button
                className="suggestion-chip"
                onClick={() => handleSuggestionClick("What are the subtle misconceptions most engineers have about this topic?")}
              >
                What are the subtle misconceptions most engineers have?
              </button>
            </div>
          </div>
        ) : (
          history.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
              <div className="bubble-header">
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
          placeholder={topic ? "Ask a question, test an edge-case, or discuss..." : "Select a topic first..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!topic || isChatting}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isChatting || !topic}
          title="Send inquiry (Enter)"
        >
          <Send size={15} />
        </button>
      </form>
    </aside>
  );
};

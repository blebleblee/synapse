import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import { Send, Bot, User, MessageSquare, Lightbulb, BookmarkCheck } from 'lucide-react';
import type { ChatMessage, TopicDetails } from '../types';

interface TutorChatProps {
  topic: TopicDetails | null;
  history: ChatMessage[];
  isChatting: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onSaveSession: () => Promise<void>;
  isSavingSession: boolean;
}

export const TutorChat: React.FC<TutorChatProps> = ({
  topic,
  history,
  isChatting,
  onSendMessage,
  onSaveSession,
  isSavingSession,
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history, isChatting]);

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
    <aside className="chat-sidebar">
      <div className="chat-header">
        <div className="persona-info">
          <Bot size={18} className="persona-icon" />
          <div className="persona-text">
            <span className="persona-label">Socratic AI Tutor</span>
            <span className="persona-role" title={personaRole}>
              {personaRole}
            </span>
          </div>
        </div>

        {history.length > 0 && (
          <button
            className="btn-secondary-sm"
            onClick={onSaveSession}
            disabled={isSavingSession}
            title="Save dialogue transcript to sessions/"
          >
            <BookmarkCheck size={13} />
            <span>{isSavingSession ? 'Saving...' : 'Save Session'}</span>
          </button>
        )}
      </div>

      <div className="chat-messages">
        {history.length === 0 ? (
          <div className="chat-empty">
            <MessageSquare size={32} className="chat-empty-icon" />
            <p>
              Ask your AI tutor questions, explore code, test your mental models, or ask for a quiz.
            </p>
            {topic && (
              <div className="suggestions-box">
                <span className="suggestions-title">
                  <Lightbulb size={12} /> Socratic Starters:
                </span>
                <button
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick(`Break down the core intuition of ${topic.subtopic} with a simple real-world analogy.`)}
                >
                  "Explain core intuition with an analogy"
                </button>
                <button
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick(`Give me a production-grade architecture walkthrough of ${topic.subtopic}.`)}
                >
                  "Walk me through the architecture"
                </button>
                <button
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick(`Quiz me on the key concepts of ${topic.subtopic}. Give me 1 scenario-based question.`)}
                >
                  "Quiz me on key concepts"
                </button>
              </div>
            )}
          </div>
        ) : (
          history.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
              <div className="bubble-author">
                {msg.role === 'student' ? <User size={13} /> : <Bot size={13} />}
                <span>{msg.role === 'student' ? 'You' : personaRole}</span>
              </div>
              <div
                className="bubble-content markdown-body"
                dangerouslySetInnerHTML={{ __html: marked.parse(msg.content) as string }}
              />
            </div>
          ))
        )}

        {isChatting && (
          <div className="chat-bubble tutor loading">
            <div className="bubble-author">
              <Bot size={13} />
              <span>{personaRole}</span>
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

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder={topic ? `Discuss ${topic.subtopic.replace(/_/g, ' ')}...` : 'Select a topic first...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!topic || isChatting}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || !topic || isChatting}
        >
          <Send size={15} />
        </button>
      </form>
    </aside>
  );
};

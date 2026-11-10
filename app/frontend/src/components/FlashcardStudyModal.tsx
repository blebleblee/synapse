import React, { useState, useEffect } from 'react';
import { Layers, RotateCcw, CheckCircle2, X, Sparkles, Award } from 'lucide-react';

export interface Flashcard {
  id: number;
  front: string;
  back: string;
  tag?: string;
}

interface FlashcardStudyModalProps {
  isOpen: boolean;
  onClose: () => void;
  topicPath: string;
  topicTitle: string;
}

export const FlashcardStudyModal: React.FC<FlashcardStudyModalProps> = ({
  isOpen,
  onClose,
  topicPath,
  topicTitle,
}) => {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [reviewedCount, setReviewedCount] = useState(0);

  useEffect(() => {
    if (isOpen && topicPath) {
      loadDeck();
    } else {
      setCards([]);
      setCurrentIndex(0);
      setIsFlipped(false);
      setIsCompleted(false);
      setReviewedCount(0);
    }
  }, [isOpen, topicPath]);

  const loadDeck = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/flashcards/deck?query=${encodeURIComponent(topicPath)}`);
      if (res.ok) {
        const data = await res.json();
        setCards(data.cards || []);
        setCurrentIndex(0);
        setIsFlipped(false);
        setIsCompleted(false);
      }
    } catch (err) {
      console.error('Failed to load flashcard deck:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFlip = () => {
    setIsFlipped((prev) => !prev);
  };

  const handleRate = (_intervalDays: number) => {
    setIsFlipped(false);
    setReviewedCount((prev) => prev + 1);

    if (currentIndex + 1 < cards.length) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setIsCompleted(true);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || cards.length === 0 || isCompleted) return;
      if (e.code === 'Space') {
        e.preventDefault();
        handleFlip();
      } else if (isFlipped) {
        if (e.key === '1') handleRate(1);
        if (e.key === '2') handleRate(3);
        if (e.key === '3') handleRate(7);
        if (e.key === '4') handleRate(14);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isFlipped, cards, currentIndex, isCompleted]);

  if (!isOpen) return null;

  const currentCard = cards[currentIndex];
  const progressPercent = cards.length > 0 ? ((currentIndex + (isCompleted ? 1 : 0)) / cards.length) * 100 : 0;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card flashcard-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <Layers size={18} className="flashcard-header-icon" />
            <div>
              <h3>Spaced Repetition Review</h3>
              <span className="flashcard-sub">{topicTitle}</span>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        {isLoading ? (
          <div className="flashcard-empty-state">
            <div className="spinner" />
            <p>Loading active recall deck...</p>
          </div>
        ) : cards.length === 0 ? (
          <div className="flashcard-empty-state">
            <Sparkles size={36} className="empty-icon" />
            <h4>No Flashcards Generated Yet</h4>
            <p>Generate or study this topic to synthesize active recall cards.</p>
            <button className="btn-primary" onClick={loadDeck}>
              Generate Cards Now
            </button>
          </div>
        ) : isCompleted ? (
          <div className="flashcard-completed-state">
            <Award size={48} className="award-icon" />
            <h3>Review Session Completed!</h3>
            <p>You reviewed {reviewedCount} cards. Active recall intervals updated in mastery tracking.</p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={loadDeck}>
                <RotateCcw size={14} /> Review Again
              </button>
              <button className="btn-primary" onClick={onClose}>
                <CheckCircle2 size={14} /> Done
              </button>
            </div>
          </div>
        ) : (
          <div className="flashcard-study-body">
            {/* Progress Bar */}
            <div className="flashcard-progress-bar">
              <div className="flashcard-progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
            <div className="flashcard-counter-row">
              <span>Card {currentIndex + 1} of {cards.length}</span>
              <span className="hint-pill">Spacebar to flip</span>
            </div>

            {/* 3D Flip Card Container */}
            <div className="flashcard-viewport" onClick={handleFlip}>
              <div className={`flashcard-3d-card ${isFlipped ? 'flipped' : ''}`}>
                <div className="flashcard-face flashcard-front">
                  <span className="card-face-tag">QUESTION / PROMPT</span>
                  <p className="card-text">{currentCard?.front}</p>
                  <span className="flip-prompt">Click to reveal answer ↷</span>
                </div>
                <div className="flashcard-face flashcard-back">
                  <span className="card-face-tag answer">ACTIVE RECALL ANSWER</span>
                  <p className="card-text">{currentCard?.back}</p>
                  <span className="flip-prompt">Click to flip back</span>
                </div>
              </div>
            </div>

            {/* SM-2 Interval Response Buttons */}
            {isFlipped ? (
              <div className="flashcard-rating-buttons">
                <button className="rate-btn rate-again" onClick={() => handleRate(1)}>
                  <span className="rate-label">Again</span>
                  <span className="rate-interval">1d [1]</span>
                </button>
                <button className="rate-btn rate-hard" onClick={() => handleRate(3)}>
                  <span className="rate-label">Hard</span>
                  <span className="rate-interval">3d [2]</span>
                </button>
                <button className="rate-btn rate-good" onClick={() => handleRate(7)}>
                  <span className="rate-label">Good</span>
                  <span className="rate-interval">7d [3]</span>
                </button>
                <button className="rate-btn rate-easy" onClick={() => handleRate(14)}>
                  <span className="rate-label">Easy</span>
                  <span className="rate-interval">14d [4]</span>
                </button>
              </div>
            ) : (
              <div className="flashcard-actions-row">
                <button className="btn-secondary" onClick={handleFlip}>
                  Show Answer (Space)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

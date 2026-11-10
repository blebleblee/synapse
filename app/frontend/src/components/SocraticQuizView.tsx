import React, { useState } from 'react';
import { HelpCircle, CheckCircle2, XCircle, RefreshCw, Sparkles } from 'lucide-react';
import type { QuizQuestion } from '../types';

interface SocraticQuizViewProps {
  subtopicTitle: string;
  questions: QuizQuestion[];
  isLoading: boolean;
  onRefreshQuiz: () => void;
}

export const SocraticQuizView: React.FC<SocraticQuizViewProps> = ({
  subtopicTitle,
  questions,
  isLoading,
  onRefreshQuiz,
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState<{ [qId: number]: number }>({});
  const [revealed, setRevealed] = useState<{ [qId: number]: boolean }>({});

  const handleSelect = (qId: number, optionIdx: number) => {
    setSelectedAnswers((prev) => ({ ...prev, [qId]: optionIdx }));
    setRevealed((prev) => ({ ...prev, [qId]: true }));
  };

  if (isLoading) {
    return (
      <div className="viewer-empty">
        <div className="spinner" />
        <p>Generating Socratic evaluation scenarios for {subtopicTitle}...</p>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="viewer-missing-card">
        <HelpCircle size={36} className="missing-icon" />
        <h3>Socratic Knowledge Check</h3>
        <p>Test your mental model and operational mechanics with scenario-based evaluation questions.</p>
        <button className="btn-primary" onClick={onRefreshQuiz}>
          <Sparkles size={16} />
          <span>Generate Knowledge Quiz</span>
        </button>
      </div>
    );
  }

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <div className="quiz-title-box">
          <HelpCircle size={18} className="quiz-icon" />
          <h3>Socratic Scenario Quiz: {subtopicTitle}</h3>
        </div>
        <button className="btn-secondary-sm" onClick={onRefreshQuiz} title="Generate new questions">
          <RefreshCw size={13} />
          <span>New Questions</span>
        </button>
      </div>

      <div className="quiz-questions-list">
        {questions.map((q, idx) => {
          const userChoice = selectedAnswers[q.id];
          const isCorrect = userChoice === q.correctIndex;
          const isRevealed = revealed[q.id];

          return (
            <div key={q.id} className="quiz-card">
              <div className="quiz-q-num">Question {idx + 1}</div>
              <p className="quiz-q-text">{q.question}</p>

              <div className="quiz-options">
                {q.options.map((opt, optIdx) => {
                  let optClass = 'quiz-opt-btn';
                  if (isRevealed) {
                    if (optIdx === q.correctIndex) {
                      optClass += ' correct';
                    } else if (optIdx === userChoice) {
                      optClass += ' incorrect';
                    }
                  } else if (userChoice === optIdx) {
                    optClass += ' selected';
                  }

                  return (
                    <button
                      key={optIdx}
                      className={optClass}
                      onClick={() => handleSelect(q.id, optIdx)}
                      disabled={isRevealed}
                    >
                      <span className="opt-letter">{String.fromCharCode(65 + optIdx)}</span>
                      <span className="opt-text">{opt}</span>
                      {isRevealed && optIdx === q.correctIndex && <CheckCircle2 size={16} className="opt-status-icon success" />}
                      {isRevealed && optIdx === userChoice && !isCorrect && <XCircle size={16} className="opt-status-icon error" />}
                    </button>
                  );
                })}
              </div>

              {isRevealed && (
                <div className={`quiz-explanation ${isCorrect ? 'exp-correct' : 'exp-incorrect'}`}>
                  <strong>{isCorrect ? '✔ Correct!' : '✘ Incorrect.'}</strong> {q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

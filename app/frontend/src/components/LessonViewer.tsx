import React, { useMemo, useRef, useEffect } from 'react';
import {
  BookOpen,
  FlaskConical,
  GraduationCap,
  HelpCircle,
  Sparkles,
  RefreshCw,
  FileCheck2,
  Gauge,
  Award,
  Layers,
  Download,
  FileText
} from 'lucide-react';
import type { TopicDetails, QuizQuestion } from '../types';
import { renderMarkdownWithMathAndMermaid, renderMermaidDiagramsInElement } from '../utils/markdownRenderer';
import { SocraticQuizView } from './SocraticQuizView';

interface LessonViewerProps {
  topic: TopicDetails | null;
  isLoading: boolean;
  isGenerating: boolean;
  onGenerate: (query: string, force?: boolean, level?: string) => void;
  onRunInTerminal: (command: string) => void;
  activeTab: 'summary' | 'foundation' | 'lesson' | 'labs' | 'quiz';
  setActiveTab: (tab: 'summary' | 'foundation' | 'lesson' | 'labs' | 'quiz') => void;
  currentLevel: string;
  onSelectLevel: (level: string) => void;
  quizQuestions: QuizQuestion[];
  isLoadingQuiz: boolean;
  onRefreshQuiz: () => void;
  onCompileGuide: () => void;
  isCompiling: boolean;
  onUpdateMastery: (state: string) => void;
  onDownloadFlashcards: () => void;
  onDownloadHandbook: () => void;
  onRegenerateSummary: () => Promise<void>;
  isRegeneratingSummary: boolean;
}

export const LessonViewer: React.FC<LessonViewerProps> = ({
  topic,
  isLoading,
  isGenerating,
  onGenerate,
  onRunInTerminal,
  activeTab,
  setActiveTab,
  currentLevel,
  onSelectLevel,
  quizQuestions,
  isLoadingQuiz,
  onRefreshQuiz,
  onCompileGuide,
  isCompiling,
  onUpdateMastery,
  onDownloadFlashcards,
  onDownloadHandbook,
  onRegenerateSummary,
  isRegeneratingSummary,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  const rawMarkdown = useMemo(() => {
    if (!topic) return '';
    if (activeTab === 'summary') return topic.summary || '';
    if (activeTab === 'foundation') return topic.foundation;
    if (activeTab === 'lesson') return topic.lesson;
    if (activeTab === 'labs') return topic.labs;
    return '';
  }, [topic, activeTab]);

  const htmlContent = useMemo(() => {
    if (!rawMarkdown) return '';
    return renderMarkdownWithMathAndMermaid(rawMarkdown);
  }, [rawMarkdown]);

  useEffect(() => {
    if (contentRef.current) {
      renderMermaidDiagramsInElement(contentRef.current);
    }
  }, [htmlContent, activeTab]);

  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    const runBtn = target.closest('.btn-run-code') as HTMLElement | null;
    if (runBtn && runBtn.dataset.code) {
      onRunInTerminal(runBtn.dataset.code);
    }
  };

  if (isLoading) {
    return (
      <div className="viewer-empty">
        <div className="spinner" />
        <p>Loading topic knowledge units...</p>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="viewer-empty">
        <BookOpen size={48} className="empty-icon" />
        <h2>Select a Topic from the Tree</h2>
        <p>Explore over 290 structured subtopics across Computing, Math, Sciences, and Arts.</p>
      </div>
    );
  }

  const hasAnyContent = Boolean(topic.summary || topic.foundation || topic.lesson || topic.labs);
  const masteryState = topic.mastery || 'not_started';

  return (
    <main className="lesson-viewer">
      <header className="viewer-header">
        <div className="breadcrumbs">
          <span className="crumb-domain">{topic.domain.replace(/_/g, ' ')}</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-category">{topic.category.replace(/_/g, ' ')}</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-subtopic">{topic.subtopic.replace(/_/g, ' ')}</span>
        </div>

        <div className="header-actions">
          {/* User Competence Mastery Selector */}
          <div className="mastery-selector">
            <Award size={13} className={`mastery-icon ${masteryState}`} />
            <select
              value={masteryState}
              onChange={(e) => onUpdateMastery(e.target.value)}
              className={`mastery-select ${masteryState}`}
            >
              <option value="not_started">Not Started</option>
              <option value="studying">Studying</option>
              <option value="lab_verified">Lab Verified</option>
              <option value="mastered">Mastered</option>
            </select>
          </div>

          <button
            className="btn-secondary-sm"
            onClick={onDownloadFlashcards}
            title="Download Anki spaced-repetition flashcards (.csv)"
          >
            <Layers size={13} />
            <span>Anki</span>
          </button>

          <button
            className="btn-secondary-sm"
            onClick={onDownloadHandbook}
            title={`Export complete ${topic.domain} handbook (.md)`}
          >
            <Download size={13} />
            <span>Handbook</span>
          </button>

          <button
            className="btn-secondary-sm"
            onClick={onCompileGuide}
            disabled={isCompiling}
            title="Compile mastered summary guide to artifacts/"
          >
            <FileCheck2 size={13} />
            <span>{isCompiling ? 'Compiling...' : 'Guide'}</span>
          </button>

          {activeTab === 'summary' ? (
            <button
              className="btn-secondary-sm"
              onClick={onRegenerateSummary}
              disabled={isRegeneratingSummary}
              title="Regenerate summary with latest discussion session insights"
            >
              <RefreshCw size={13} className={isRegeneratingSummary ? 'spin' : ''} />
              <span>{isRegeneratingSummary ? 'Updating Summary...' : 'Update Summary'}</span>
            </button>
          ) : (
            <button
              className="btn-secondary-sm"
              onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, true, currentLevel)}
              disabled={isGenerating}
              title="Regenerate this level"
            >
              <RefreshCw size={13} className={isGenerating ? 'spin' : ''} />
              <span>{isGenerating ? 'Generating...' : 'Regen'}</span>
            </button>
          )}
        </div>
      </header>

      {/* Progressive Difficulty Level Selector Bar (only shown for non-summary content) */}
      {activeTab !== 'summary' && (
        <div className="levels-bar">
          <span className="levels-label">
            <Gauge size={13} /> Mastery Level:
          </span>
          <div className="level-pills">
            {['beginner', 'intermediate', 'advanced'].map((lvl) => (
              <button
                key={lvl}
                className={`level-pill-btn ${currentLevel === lvl ? 'active' : ''}`}
                onClick={() => onSelectLevel(lvl)}
              >
                {lvl.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="tabs-bar">
        <button
          className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          <FileText size={14} />
          <span>Executive Summary</span>
          {topic.summary && <span className="tab-dot" />}
        </button>

        <button
          className={`tab-btn ${activeTab === 'foundation' ? 'active' : ''}`}
          onClick={() => setActiveTab('foundation')}
        >
          <BookOpen size={14} />
          <span>Foundation</span>
          {topic.foundation && <span className="tab-dot" />}
        </button>

        <button
          className={`tab-btn ${activeTab === 'lesson' ? 'active' : ''}`}
          onClick={() => setActiveTab('lesson')}
        >
          <GraduationCap size={14} />
          <span>In-Depth Lesson</span>
          {topic.lesson && <span className="tab-dot" />}
        </button>

        <button
          className={`tab-btn ${activeTab === 'labs' ? 'active' : ''}`}
          onClick={() => setActiveTab('labs')}
        >
          <FlaskConical size={14} />
          <span>Operational Labs</span>
          {topic.labs && <span className="tab-dot" />}
        </button>

        <button
          className={`tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
          onClick={() => setActiveTab('quiz')}
        >
          <HelpCircle size={14} />
          <span>Socratic Quiz</span>
        </button>
      </div>

      <div className="viewer-scroll-body" ref={contentRef} onClick={handleContentClick}>
        {activeTab === 'quiz' ? (
          <SocraticQuizView
            subtopicTitle={`${topic.subtopic.replace(/_/g, ' ')} (${currentLevel.toUpperCase()})`}
            questions={quizQuestions}
            isLoading={isLoadingQuiz}
            onRefreshQuiz={onRefreshQuiz}
          />
        ) : !hasAnyContent ? (
          <div className="viewer-missing-card">
            <Sparkles size={36} className="missing-icon" />
            <h3>No Content Generated Yet</h3>
            <p>
              Generate the curriculum units (Foundation, Lesson, and Labs) for this topic.
            </p>
            <button
              className="btn-primary"
              onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, false, currentLevel)}
              disabled={isGenerating}
            >
              <Sparkles size={16} />
              <span>{isGenerating ? `Synthesizing Units...` : `Generate Learning Units Now`}</span>
            </button>
          </div>
        ) : !rawMarkdown ? (
          <div className="viewer-missing-card">
            <h3>{activeTab === 'summary' ? 'Summary not yet generated' : `This unit is missing in ${currentLevel} tier`}</h3>
            <p>You can generate this unit using the action button in the top right.</p>
          </div>
        ) : (
          <article
            className="markdown-body"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        )}
      </div>
    </main>
  );
};

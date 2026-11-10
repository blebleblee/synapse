import React, { useMemo, useRef, useEffect } from 'react';
import {
  BookOpen,
  FlaskConical,
  GraduationCap,
  HelpCircle,
  Sparkles,
  RefreshCw,
  FileCheck2,
  Gauge
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
  activeTab: 'foundation' | 'lesson' | 'labs' | 'quiz';
  setActiveTab: (tab: 'foundation' | 'lesson' | 'labs' | 'quiz') => void;
  currentLevel: string;
  onSelectLevel: (level: string) => void;
  quizQuestions: QuizQuestion[];
  isLoadingQuiz: boolean;
  onRefreshQuiz: () => void;
  onCompileGuide: () => void;
  isCompiling: boolean;
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
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  const rawMarkdown = useMemo(() => {
    if (!topic) return '';
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
        <p>Explore over 280 structured subtopics across Computing, Math, Sciences, and Arts.</p>
      </div>
    );
  }

  const hasAnyContent = Boolean(topic.foundation || topic.lesson || topic.labs);

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
          <button
            className="btn-secondary-sm"
            onClick={onCompileGuide}
            disabled={isCompiling}
            title="Compile mastered summary guide to artifacts/"
          >
            <FileCheck2 size={13} />
            <span>{isCompiling ? 'Compiling...' : 'Compile Guide'}</span>
          </button>

          <button
            className="btn-secondary-sm"
            onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, true, currentLevel)}
            disabled={isGenerating}
            title="Regenerate this level"
          >
            <RefreshCw size={13} className={isGenerating ? 'spin' : ''} />
            <span>{isGenerating ? 'Generating...' : 'Regenerate'}</span>
          </button>
        </div>
      </header>

      {/* Progressive Difficulty Level Selector Bar */}
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

      <div className="tabs-bar">
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
            <h3>No Content Generated for {currentLevel.toUpperCase()} Level</h3>
            <p>
              Generate the {currentLevel} tier (Foundation, Lesson, and Labs) designed to build upon earlier concepts.
            </p>
            <button
              className="btn-primary"
              onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, false, currentLevel)}
              disabled={isGenerating}
            >
              <Sparkles size={16} />
              <span>{isGenerating ? `Synthesizing ${currentLevel} Units...` : `Generate ${currentLevel.toUpperCase()} Units Now`}</span>
            </button>
          </div>
        ) : !rawMarkdown ? (
          <div className="viewer-missing-card">
            <h3>This unit is missing in {currentLevel} tier</h3>
            <p>You can generate this unit using the Regenerate button above.</p>
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

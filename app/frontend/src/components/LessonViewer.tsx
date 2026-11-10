import React, { useMemo, useRef, useEffect, useState } from 'react';
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
  FileText,
  Volume2,
  VolumeX
} from 'lucide-react';
import type { TopicDetails, QuizQuestion } from '../types';
import { renderMarkdownWithMathAndMermaid, renderMermaidDiagramsInElement } from '../utils/markdownRenderer';
import { SocraticQuizView } from './SocraticQuizView';
import { speakText, stopSpeaking } from '../utils/speech';

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
  onOpenFlashcards: () => void;
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
  onOpenFlashcards,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [isSpeakingVoice, setIsSpeakingVoice] = useState(false);

  useEffect(() => {
    stopSpeaking();
    setIsSpeakingVoice(false);
  }, [topic?.path, activeTab, currentLevel]);

  const handleToggleVoice = () => {
    if (isSpeakingVoice) {
      stopSpeaking();
      setIsSpeakingVoice(false);
    } else if (rawMarkdown) {
      speakText(
        rawMarkdown,
        () => setIsSpeakingVoice(true),
        () => setIsSpeakingVoice(false)
      );
    }
  };

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
        <p>Explore over 340 structured study units across Computing, Engineering, and Sciences.</p>
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

        {/* User Competence Mastery Selector on Right */}
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
      </header>

      {/* Unified Permanent Non-Shifting Navigation Bar */}
      <div className="tabs-bar">
        <div className="tabs-group">
          <button
            className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            <FileText size={14} />
            <span>Summary</span>
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
            <span>Lesson</span>
            {topic.lesson && <span className="tab-dot" />}
          </button>

          <button
            className={`tab-btn ${activeTab === 'labs' ? 'active' : ''}`}
            onClick={() => setActiveTab('labs')}
          >
            <FlaskConical size={14} />
            <span>Labs</span>
            {topic.labs && <span className="tab-dot" />}
          </button>

          <button
            className={`tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
            onClick={() => setActiveTab('quiz')}
          >
            <HelpCircle size={14} />
            <span>Quiz</span>
          </button>
        </div>

        <div className="tabs-actions-group">
          <button
            className={`nav-action-btn ${isSpeakingVoice ? 'active-voice' : ''}`}
            onClick={handleToggleVoice}
            disabled={!rawMarkdown}
            title={isSpeakingVoice ? 'Stop audio playback' : 'Listen to this section (Speech Synthesis)'}
          >
            {isSpeakingVoice ? <VolumeX size={12} className="voice-pulse" /> : <Volume2 size={12} />}
            <span>{isSpeakingVoice ? 'Stop' : 'Listen'}</span>
          </button>

          <button
            className="nav-action-btn"
            onClick={onOpenFlashcards}
            title="Interactive in-app spaced repetition flashcards"
          >
            <Layers size={12} />
            <span>Study Cards</span>
          </button>

          <button
            className="nav-action-btn"
            onClick={onDownloadHandbook}
            title={`Export complete ${topic.domain} handbook (.md)`}
          >
            <Download size={12} />
            <span>Book</span>
          </button>

          <button
            className="nav-action-btn"
            onClick={onDownloadFlashcards}
            title="Download Anki spaced-repetition flashcards (.csv)"
          >
            <Layers size={12} />
            <span>Anki</span>
          </button>

          <button
            className="nav-action-btn"
            onClick={onCompileGuide}
            disabled={isCompiling}
            title="Compile mastered summary guide to artifacts/"
          >
            <FileCheck2 size={12} />
            <span>{isCompiling ? 'Compiling...' : 'Guide'}</span>
          </button>

          {activeTab === 'summary' ? (
            <button
              className="nav-action-btn"
              onClick={onRegenerateSummary}
              disabled={isRegeneratingSummary}
              title="Regenerate summary with latest discussion session insights"
            >
              <RefreshCw size={12} className={isRegeneratingSummary ? 'spin' : ''} />
              <span>Update</span>
            </button>
          ) : (
            <button
              className="nav-action-btn"
              onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, true, currentLevel)}
              disabled={isGenerating}
              title="Regenerate this level"
            >
              <RefreshCw size={12} className={isGenerating ? 'spin' : ''} />
              <span>Regen</span>
            </button>
          )}

          {/* Persistent Difficulty Level Selector */}
          <div
            className={`nav-level-selector ${activeTab === 'summary' ? 'summary-dimmed' : ''}`}
            title={activeTab === 'summary' ? 'Executive summary covers all tiers' : 'Select difficulty tier'}
          >
            <span className="levels-label">
              <Gauge size={12} /> Tier:
            </span>
            <div className="level-pills">
              {['beginner', 'intermediate', 'advanced'].map((lvl) => (
                <button
                  key={lvl}
                  className={`level-pill-btn ${currentLevel === lvl ? 'active' : ''}`}
                  onClick={() => onSelectLevel(lvl)}
                  disabled={activeTab === 'summary'}
                >
                  {lvl.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
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

import React, { useMemo, useRef, useEffect, useState } from 'react';
import {
  BookOpen,
  FlaskConical,
  GraduationCap,
  HelpCircle,
  Sparkles,
  RefreshCw,
  FileCheck2,
  Award,
  Layers,
  Download,
  FileText,
  Volume2,
  VolumeX,
  Columns,
  ZoomIn,
  ZoomOut,
  X,
  Maximize2
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
  targetLanguage?: string;
  onNavigateBreadcrumb?: (type: 'domain' | 'category' | 'subtopic', path: string) => void;
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
  targetLanguage,
  onNavigateBreadcrumb,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [isSpeakingVoice, setIsSpeakingVoice] = useState(false);
  const [translatedMarkdown, setTranslatedMarkdown] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);

  useEffect(() => {
    stopSpeaking();
    setIsSpeakingVoice(false);
  }, [topic?.path, activeTab, currentLevel]);

  const rawMarkdown = useMemo(() => {
    if (!topic) return '';
    if (activeTab === 'summary') return topic.summary || '';
    if (activeTab === 'foundation') return topic.foundation;
    if (activeTab === 'lesson') return topic.lesson;
    if (activeTab === 'labs') return topic.labs;
    return '';
  }, [topic, activeTab]);

  useEffect(() => {
    if (!targetLanguage || targetLanguage === 'en' || !rawMarkdown) {
      setTranslatedMarkdown(null);
      setIsTranslating(false);
      return;
    }

    let isMounted = true;
    setIsTranslating(true);

    fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: rawMarkdown, target_lang: targetLanguage }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data?.translated) {
          setTranslatedMarkdown(data.translated);
        }
      })
      .catch((err) => console.error('Translation error:', err))
      .finally(() => {
        if (isMounted) setIsTranslating(false);
      });

    return () => {
      isMounted = false;
    };
  }, [rawMarkdown, targetLanguage]);

  const [bilingualSplit, setBilingualSplit] = useState<boolean>(() => {
    return localStorage.getItem('synapse_bilingual_split') === 'true';
  });
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [lightboxSvg, setLightboxSvg] = useState<string | null>(null);
  const [lightboxZoom, setLightboxZoom] = useState(1);

  const [dependencies, setDependencies] = useState<{
    prerequisites: { id: string; label: string; domain: string }[];
    unlocks: { id: string; label: string; domain: string }[];
  }>({ prerequisites: [], unlocks: [] });

  useEffect(() => {
    if (!topic?.path) return;
    let isMounted = true;
    fetch(`/api/topic/dependencies?query=${encodeURIComponent(topic.path)}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data) {
          setDependencies({
            prerequisites: data.prerequisites || [],
            unlocks: data.unlocks || [],
          });
        }
      })
      .catch((err) => console.error('Failed to load topic dependencies:', err));

    return () => {
      isMounted = false;
    };
  }, [topic?.path]);

  const activeMarkdown = (targetLanguage && targetLanguage !== 'en' && translatedMarkdown) ? translatedMarkdown : rawMarkdown;

  const handleToggleVoice = () => {
    if (isSpeakingVoice) {
      stopSpeaking();
      setIsSpeakingVoice(false);
    } else if (activeMarkdown) {
      speakText(
        activeMarkdown,
        () => setIsSpeakingVoice(true),
        () => setIsSpeakingVoice(false)
      );
    }
  };

  const htmlContent = useMemo(() => {
    if (!activeMarkdown) return '';
    return renderMarkdownWithMathAndMermaid(activeMarkdown);
  }, [activeMarkdown]);

  const originalHtmlContent = useMemo(() => {
    if (!rawMarkdown) return '';
    return renderMarkdownWithMathAndMermaid(rawMarkdown);
  }, [rawMarkdown]);

  const translatedHtmlContent = useMemo(() => {
    const md = translatedMarkdown || rawMarkdown;
    if (!md) return '';
    return renderMarkdownWithMathAndMermaid(md);
  }, [translatedMarkdown, rawMarkdown]);

  useEffect(() => {
    if (contentRef.current) {
      renderMermaidDiagramsInElement(contentRef.current);
    }
  }, [htmlContent, originalHtmlContent, translatedHtmlContent, activeTab, bilingualSplit]);

  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;

    // 1. Executable code block runner
    const runBtn = target.closest('.btn-run-code') as HTMLElement | null;
    if (runBtn && runBtn.dataset.code) {
      onRunInTerminal(runBtn.dataset.code);
      return;
    }

    // 2. Zoomable Image Lightbox
    const imgEl = target.closest('img') as HTMLImageElement | null;
    if (imgEl && imgEl.src) {
      setLightboxImage(imgEl.src);
      setLightboxSvg(null);
      setLightboxZoom(1);
      return;
    }

    // 3. Zoomable Mermaid Vector Diagram Lightbox
    const svgEl = target.closest('.mermaid svg') as SVGElement | null;
    if (svgEl) {
      const serializer = new XMLSerializer();
      setLightboxSvg(serializer.serializeToString(svgEl));
      setLightboxImage(null);
      setLightboxZoom(1);
      return;
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
          <span
            className="crumb-domain clickable"
            onClick={() => onNavigateBreadcrumb && onNavigateBreadcrumb('domain', topic.domain)}
            title={`Browse ${topic.domain.replace(/_/g, ' ')}`}
          >
            {topic.domain.replace(/_/g, ' ')}
          </span>
          <span className="crumb-sep">/</span>
          <span
            className="crumb-category clickable"
            onClick={() => onNavigateBreadcrumb && onNavigateBreadcrumb('category', `${topic.domain}/${topic.category}`)}
            title={`Browse ${topic.category.replace(/_/g, ' ')}`}
          >
            {topic.category.replace(/_/g, ' ')}
          </span>
          <span className="crumb-sep">/</span>
          <span className="crumb-subtopic">
            {topic.subtopic.replace(/_/g, ' ')}
          </span>
        </div>

        {/* Top Right: Difficulty Tier Selector + Mastery Selector */}
        <div className="viewer-header-right">
          <div className="header-tier-pills" title="Difficulty Tier">
            {['beginner', 'intermediate', 'advanced'].map((lvl) => (
              <button
                key={lvl}
                className={`header-tier-btn ${currentLevel === lvl ? 'active' : ''}`}
                onClick={() => onSelectLevel(lvl)}
                disabled={activeTab === 'summary'}
                title={activeTab === 'summary' ? 'Summary covers all tiers' : `Switch difficulty tier to ${lvl}`}
              >
                {lvl.slice(0, 3).toUpperCase()}
              </button>
            ))}
          </div>

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
          {targetLanguage && targetLanguage !== 'en' && (
            <span className={`nav-lang-badge ${isTranslating ? 'translating' : ''}`} title="AI translation active">
              🌐 {targetLanguage.toUpperCase()}{isTranslating ? '...' : ''}
            </span>
          )}

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

          {/* Bilingual Dual Column Split View Toggle */}
          {targetLanguage && targetLanguage !== 'en' && (
            <button
              className={`nav-action-btn ${bilingualSplit ? 'active-bilingual' : ''}`}
              onClick={() => {
                const next = !bilingualSplit;
                setBilingualSplit(next);
                localStorage.setItem('synapse_bilingual_split', String(next));
              }}
              title={bilingualSplit ? "Switch to Single Column View" : "Switch to Bilingual Side-by-Side Dual View"}
            >
              <Columns size={12} />
              <span>{bilingualSplit ? 'Dual ◫' : 'Split ◫'}</span>
            </button>
          )}
        </div>
      </div>

      <div className="viewer-scroll-body" ref={contentRef} onClick={handleContentClick}>
        {/* In-Lesson Real-Time Dependency Navigation Bar */}
        {(dependencies.prerequisites.length > 0 || dependencies.unlocks.length > 0) && (
          <div className="in-lesson-deps-bar">
            {dependencies.prerequisites.length > 0 && (
              <div className="deps-group prereqs">
                <span className="deps-label">Prerequisite:</span>
                {dependencies.prerequisites.map((p) => (
                  <button
                    key={p.id}
                    className="dep-chip prereq-chip"
                    onClick={() => onNavigateBreadcrumb && onNavigateBreadcrumb('subtopic', p.id)}
                    title={`Prerequisite topic: ${p.label}`}
                  >
                    <span>⬅ {p.label}</span>
                  </button>
                ))}
              </div>
            )}

            {dependencies.unlocks.length > 0 && (
              <div className="deps-group unlocks">
                <span className="deps-label">Unlocks:</span>
                {dependencies.unlocks.map((u) => (
                  <button
                    key={u.id}
                    className="dep-chip unlock-chip"
                    onClick={() => onNavigateBreadcrumb && onNavigateBreadcrumb('subtopic', u.id)}
                    title={`Unlocked next: ${u.label}`}
                  >
                    <span>{u.label} ➡</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

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
        ) : bilingualSplit && targetLanguage && targetLanguage !== 'en' ? (
          <div className="bilingual-split-container">
            <div className="bilingual-col original">
              <div className="bilingual-col-header">
                <span>ORIGINAL (ENGLISH)</span>
              </div>
              <article
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: originalHtmlContent }}
              />
            </div>
            <div className="bilingual-col translated">
              <div className="bilingual-col-header">
                <span>TRANSLATED ({targetLanguage.toUpperCase()})</span>
                {isTranslating && <span className="translating-indicator">Translating...</span>}
              </div>
              <article
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: translatedHtmlContent }}
              />
            </div>
          </div>
        ) : (
          <article
            className="markdown-body"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        )}
      </div>

      {/* Lightbox Modal for Images and Vector Diagrams */}
      {(lightboxImage || lightboxSvg) && (
        <div className="lightbox-backdrop" onClick={() => { setLightboxImage(null); setLightboxSvg(null); }}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-toolbar">
              <button className="icon-btn" onClick={() => setLightboxZoom((z) => Math.min(z + 0.25, 3))} title="Zoom In">
                <ZoomIn size={16} />
              </button>
              <button className="icon-btn" onClick={() => setLightboxZoom((z) => Math.max(z - 0.25, 0.5))} title="Zoom Out">
                <ZoomOut size={16} />
              </button>
              <button className="icon-btn" onClick={() => setLightboxZoom(1)} title="Reset Zoom">
                <Maximize2 size={16} />
              </button>
              <button className="icon-btn" onClick={() => { setLightboxImage(null); setLightboxSvg(null); }} title="Close Lightbox">
                <X size={16} />
              </button>
            </div>
            <div className="lightbox-body" style={{ transform: `scale(${lightboxZoom})`, transformOrigin: 'center center', transition: 'transform 0.15s ease-out' }}>
              {lightboxImage && <img src={lightboxImage} alt="Diagram High-Res View" className="lightbox-img" />}
              {lightboxSvg && <div className="lightbox-svg-container" dangerouslySetInnerHTML={{ __html: lightboxSvg }} />}
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

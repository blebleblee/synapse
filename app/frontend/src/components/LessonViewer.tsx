import React, { useMemo, useEffect, useState } from 'react';
import {
  BookOpen,
  FlaskConical,
  HelpCircle,
  Sparkles,
  RefreshCw,
  FileCheck2,
  Award,
  Layers,
  Download,
  Volume2,
  VolumeX,
  Columns,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  ZoomIn,
  ZoomOut,
  Maximize2,
  X,
  Check
} from 'lucide-react';
import type { TopicDetails, QuizQuestion } from '../types';
import { renderMarkdownWithMathAndMermaid, renderMermaidDiagramsInElement } from '../utils/markdownRenderer';
import { synthesizeTerminalCommand } from '../utils/commandSynthesizer';
import { SocraticQuizView } from './SocraticQuizView';
import { speakText, stopSpeaking } from '../utils/speech';
import { getUIStrings } from '../utils/i18n';

function toTitleCase(str: string): string {
  if (!str) return '';
  return str
    .replace(/_/g, ' ')
    .split(' ')
    .map((w) => (w.length > 0 ? w.charAt(0).toUpperCase() + w.slice(1) : ''))
    .join(' ');
}

interface LessonViewerProps {
  topic: TopicDetails | null;
  contentRef: React.RefObject<HTMLDivElement>;
  isLoading: boolean;
  isGenerating: boolean;
  onGenerate: (query: string, force?: boolean, level?: string) => void;
  onRunInTerminal: (command: string) => void;
  activeTab: 'study' | 'labs' | 'quiz';
  setActiveTab: (tab: 'study' | 'labs' | 'quiz') => void;
  activeLessonId?: string | null;
  onToggleLessonCompletion?: (path: string, lessonId: string, completed?: boolean) => Promise<void>;
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
  onSelectLesson?: (lessonId: string) => void;
}

export const LessonViewer: React.FC<LessonViewerProps> = ({
  topic,
  contentRef,
  isLoading,
  isGenerating,
  onGenerate,
  onRunInTerminal,
  activeTab,
  setActiveTab,
  activeLessonId,
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
  onSelectLesson,
  onToggleLessonCompletion,
}) => {
  const [isSpeakingVoice, setIsSpeakingVoice] = useState(false);
  const [translatedMarkdown, setTranslatedMarkdown] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [optionsMenuOpen, setOptionsMenuOpen] = useState(false);

  // Interactive Diagram & Image Zoom State
  const [zoomedMedia, setZoomedMedia] = useState<{
    type: 'svg' | 'image';
    content: string;
    title?: string;
  } | null>(null);
  const [zoomScale, setZoomScale] = useState<number>(1);
  const [translate, setTranslate] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Escape key closes zoom modal, +/- zooms
  useEffect(() => {
    if (!zoomedMedia) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setZoomedMedia(null);
      } else if (e.key === '+' || e.key === '=') {
        setZoomScale((prev) => Math.min(prev + 0.25, 4));
      } else if (e.key === '-' || e.key === '_') {
        setZoomScale((prev) => Math.max(prev - 0.25, 0.4));
      } else if (e.key === '0') {
        setZoomScale(1);
        setTranslate({ x: 0, y: 0 });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [zoomedMedia]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.dropdown-container')) {
        setExportMenuOpen(false);
        setOptionsMenuOpen(false);
      }
    };
    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, []);

  const ui = getUIStrings(targetLanguage);

  const currentLessonIndex = useMemo(() => {
    if (!topic?.lessons) return 0;
    const targetId = activeLessonId || topic.active_lesson_id;
    if (!targetId || targetId === 'all') return 0;
    const idx = topic.lessons.findIndex((l) => l.id === targetId);
    return idx >= 0 ? idx : 0;
  }, [topic?.lessons, topic?.active_lesson_id, activeLessonId]);

  const prevLesson = topic?.lessons && currentLessonIndex > 0 ? topic.lessons[currentLessonIndex - 1] : null;
  const nextLesson = topic?.lessons && currentLessonIndex < topic.lessons.length - 1 ? topic.lessons[currentLessonIndex + 1] : null;
  const currentLesson = topic?.lessons && topic.lessons.length > 0 ? topic.lessons[currentLessonIndex] : null;

  useEffect(() => {
    stopSpeaking();
    setIsSpeakingVoice(false);
  }, [topic?.path, activeTab, currentLevel, activeLessonId]);

  const rawMarkdown = useMemo(() => {
    if (!topic) return '';
    if (activeTab === 'study') {
      if (activeLessonId === 'all') {
        return topic.full_content || topic.lesson || topic.foundation || '';
      }
      return topic.lesson || topic.full_content || topic.foundation || '';
    }
    if (activeTab === 'labs') return topic.labs;
    return '';
  }, [topic, activeTab, activeLessonId]);

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

  const isMathDomain = topic?.domain === 'formal_sciences' || topic?.domain === 'natural_sciences';

  const htmlContent = useMemo(() => {
    if (!activeMarkdown) return '';
    return renderMarkdownWithMathAndMermaid(activeMarkdown, isMathDomain);
  }, [activeMarkdown, isMathDomain]);

  const originalHtmlContent = useMemo(() => {
    if (!rawMarkdown) return '';
    return renderMarkdownWithMathAndMermaid(rawMarkdown, isMathDomain);
  }, [rawMarkdown, isMathDomain]);

  const translatedHtmlContent = useMemo(() => {
    const md = translatedMarkdown || rawMarkdown;
    if (!md) return '';
    return renderMarkdownWithMathAndMermaid(md, isMathDomain);
  }, [translatedMarkdown, rawMarkdown, isMathDomain]);

  useEffect(() => {
    if (contentRef.current) {
      renderMermaidDiagramsInElement(contentRef.current);
    }
  }, [htmlContent, originalHtmlContent, translatedHtmlContent, activeTab, bilingualSplit]);

  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;

    // Clipboard Copy code button runner with animated confirmation
    const copyBtn = target.closest('.btn-copy-code') as HTMLElement | null;
    if (copyBtn && copyBtn.dataset.code) {
      navigator.clipboard.writeText(copyBtn.dataset.code).then(() => {
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span class="btn-icon">✔</span> Copied!';
        copyBtn.classList.add('copied');
        setTimeout(() => {
          copyBtn.innerHTML = originalHtml;
          copyBtn.classList.remove('copied');
        }, 1800);
      }).catch((err) => {
        console.warn('Clipboard write failed:', err);
      });
      return;
    }

    // Context-aware Smart Terminal runner
    const runBtn = target.closest('.btn-run-code') as HTMLElement | null;
    if (runBtn && runBtn.dataset.code) {
      const lang = runBtn.dataset.lang || '';
      const synth = synthesizeTerminalCommand(runBtn.dataset.code, lang);
      onRunInTerminal(synth.command);
      return;
    }

    // Intercept clicks on Mermaid diagrams or images for interactive Zoom Lightbox
    const mermaidEl = target.closest('.mermaid-container, .mermaid') as HTMLElement | null;
    if (mermaidEl) {
      const svg = mermaidEl.querySelector('svg');
      if (svg) {
        const clone = svg.cloneNode(true) as SVGSVGElement;
        clone.removeAttribute('style');
        clone.setAttribute('width', '100%');
        clone.setAttribute('height', '100%');
        setZoomedMedia({
          type: 'svg',
          content: clone.outerHTML,
          title: 'Diagram Inspection'
        });
        setZoomScale(1);
        setTranslate({ x: 0, y: 0 });
        return;
      }
    }

    const img = target.closest('img') as HTMLImageElement | null;
    if (img && !img.closest('.zoom-lightbox-modal')) {
      setZoomedMedia({
        type: 'image',
        content: img.src,
        title: img.alt || 'Image Inspection'
      });
      setZoomScale(1);
      setTranslate({ x: 0, y: 0 });
      return;
    }

    // Handle relative markdown links and in-page anchor jumps
    const anchor = target.closest('a') as HTMLAnchorElement | null;
    if (anchor) {
      const href = anchor.getAttribute('href') || '';
      if (href.startsWith('#')) {
        e.preventDefault();
        const targetId = href.slice(1);
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth' });
        }
        return;
      }

      if (href.endsWith('.md') || href.includes('lesson_')) {
        e.preventDefault();
        const cleanFile = href.replace(/^\.\//, '').split('#')[0];
        if (cleanFile.startsWith('lesson_')) {
          const lessonId = cleanFile.replace(/\.md$/, '');
          setActiveTab('study');
          onSelectLesson?.(lessonId);
        } else if (cleanFile === 'LABS.md') {
          setActiveTab('labs');
        } else if (cleanFile === 'FOUNDATION.md' || cleanFile === 'SUMMARY.md') {
          setActiveTab('study');
          onSelectLesson?.('all');
        }
        return;
      }
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
        <h2>Select a Topic to Begin</h2>
        <p>Choose a subject from the curriculum tree on the left to explore in-depth lessons, practice with hands-on terminal labs, or consult the Socratic mentor.</p>
      </div>
    );
  }

  const hasAnyContent = Boolean(topic.summary || topic.foundation || topic.lesson || topic.labs);
  const masteryState = topic.mastery || 'not_started';

  return (
    <main className="lesson-viewer">
      <header className="viewer-header">
        <div className="breadcrumbs">
          <span className="crumb-domain">{toTitleCase(topic.domain_title || topic.domain)}</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-discipline">{toTitleCase(topic.discipline_title || (topic.category.includes('/') ? topic.category.split('/')[0] : topic.category))}</span>
          {topic.course_title && topic.course_title !== (topic.display_title || topic.subtopic.replace(/_/g, ' ')) && (
            <>
              <span className="crumb-sep">/</span>
              <span className="crumb-category">{toTitleCase(topic.course_title)}</span>
            </>
          )}
          <span className="crumb-sep">/</span>
          <span className="crumb-subtopic">{toTitleCase(topic.display_title || topic.subtopic)}</span>
        </div>

        {/* Top Right: Difficulty Tier Selector + Mastery Selector */}
        <div className="viewer-header-right">
          {topic.available_levels && topic.available_levels.length > 0 ? (
            <div className="header-tier-pills" title="Difficulty Tier">
              {['beginner', 'intermediate', 'advanced']
                .filter((lvl) => topic.available_levels?.includes(lvl))
                .map((lvl) => (
                  <button
                    key={lvl}
                    className={`header-tier-btn ${currentLevel === lvl ? 'active' : ''}`}
                    onClick={() => onSelectLevel(lvl)}
                    title={`Switch difficulty tier to ${lvl}`}
                  >
                    {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                  </button>
                ))}
            </div>
          ) : (
            <div className="header-curriculum-badge" title="Comprehensive Unified Curriculum">
              <span className="badge-pill-unified">Unified Masterclass</span>
            </div>
          )}

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
            className={`tab-btn ${activeTab === 'study' ? 'active' : ''}`}
            onClick={() => setActiveTab('study')}
            title="Read curriculum lessons and course guide"
          >
            <BookOpen size={14} />
            <span>{ui.study || 'Study'}</span>
            {Boolean(topic.has_content || topic.lesson || topic.foundation) && <span className="tab-dot" />}
          </button>

          <button
            className={`tab-btn ${activeTab === 'labs' ? 'active' : ''}`}
            onClick={() => setActiveTab('labs')}
            title="Hands-on operational lab exercises and terminal verification"
          >
            <FlaskConical size={14} />
            <span>{ui.labs}</span>
            {topic.labs && <span className="tab-dot" />}
          </button>

          <button
            className={`tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
            onClick={() => setActiveTab('quiz')}
            title="Socratic multiple-choice comprehension check"
          >
            <HelpCircle size={14} />
            <span>{ui.quiz}</span>
          </button>
        </div>

        <div className="tabs-actions-group">
          {targetLanguage && targetLanguage !== 'en' && (
            <span className={`nav-lang-badge ${isTranslating ? 'translating' : ''}`} title="AI translation active">
              🌐 {targetLanguage.toUpperCase()}{isTranslating ? '...' : ''}
            </span>
          )}

          {/* 1. Audio Reader */}
          <button
            className={`nav-action-btn ${isSpeakingVoice ? 'active-voice' : ''}`}
            onClick={handleToggleVoice}
            disabled={!rawMarkdown}
            title={isSpeakingVoice ? 'Stop audio playback' : 'Listen to this section (Speech Synthesis)'}
          >
            {isSpeakingVoice ? <VolumeX size={12} className="voice-pulse" /> : <Volume2 size={12} />}
            <span>{isSpeakingVoice ? 'Stop' : 'Listen'}</span>
          </button>

          {/* 2. Interactive Study Flashcards */}
          <button
            className="nav-action-btn"
            onClick={onOpenFlashcards}
            title="Interactive in-app spaced repetition flashcards"
          >
            <Layers size={12} />
            <span>Flashcards</span>
          </button>

          {/* 3. Consolidated Export Menu */}
          <div className="dropdown-container">
            <button
              className={`nav-action-btn ${exportMenuOpen ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                setExportMenuOpen((prev) => !prev);
                setOptionsMenuOpen(false);
              }}
              title="Export curriculum documents and flashcards"
            >
              <Download size={12} />
              <span>Export ▾</span>
            </button>
            {exportMenuOpen && (
              <div className="nav-dropdown-menu">
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setExportMenuOpen(false);
                    onDownloadHandbook();
                  }}
                  title={`Export complete ${topic.domain} handbook (.md)`}
                >
                  <BookOpen size={13} />
                  <span>Curriculum Handbook (.md)</span>
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setExportMenuOpen(false);
                    onCompileGuide();
                  }}
                  disabled={isCompiling}
                  title="Compile mastered summary guide to artifacts/"
                >
                  <FileCheck2 size={13} />
                  <span>{isCompiling ? 'Compiling Guide...' : 'Mastered Field Guide (.md)'}</span>
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setExportMenuOpen(false);
                    onDownloadFlashcards();
                  }}
                  title="Download Anki flashcards (.csv)"
                >
                  <Layers size={13} />
                  <span>Anki Flashcard Deck (.csv)</span>
                </button>
              </div>
            )}
          </div>

          {/* 4. More Options Menu */}
          <div className="dropdown-container">
            <button
              className={`nav-action-btn icon-only ${optionsMenuOpen ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                setOptionsMenuOpen((prev) => !prev);
                setExportMenuOpen(false);
              }}
              title="More options and maintenance"
            >
              <MoreHorizontal size={13} />
            </button>
            {optionsMenuOpen && (
              <div className="nav-dropdown-menu right-aligned">
                {targetLanguage && targetLanguage !== 'en' && (
                  <button
                    className="dropdown-item"
                    onClick={() => {
                      setOptionsMenuOpen(false);
                      const next = !bilingualSplit;
                      setBilingualSplit(next);
                      localStorage.setItem('synapse_bilingual_split', String(next));
                    }}
                  >
                    <Columns size={13} />
                    <span>{bilingualSplit ? 'Single Column View' : 'Side-by-Side Dual View'}</span>
                  </button>
                )}
                {topic.summary && (
                  <button
                    className="dropdown-item"
                    onClick={() => {
                      setOptionsMenuOpen(false);
                      onRegenerateSummary();
                    }}
                    disabled={isRegeneratingSummary}
                    title="Regenerate curriculum summary with latest session insights"
                  >
                    <RefreshCw size={13} className={isRegeneratingSummary ? 'spin' : ''} />
                    <span>Update Curriculum Summary</span>
                  </button>
                )}
                <button
                  className="dropdown-item danger"
                  onClick={() => {
                    setOptionsMenuOpen(false);
                    if (window.confirm(`Are you sure you want to regenerate '${topic.subtopic}' with AI? This will re-synthesize content.`)) {
                      onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, true, currentLevel);
                    }
                  }}
                  disabled={isGenerating}
                  title="Re-synthesize curriculum unit using LLM"
                >
                  <RefreshCw size={13} className={isGenerating ? 'spin' : ''} />
                  <span>Regenerate with AI...</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Permanent, Non-Shifting Lesson Switcher Bar on Study Tab */}
      {activeTab === 'study' && topic.lessons && topic.lessons.length > 1 && (
        <div className="study-lesson-selector-bar">
          <div className="selector-dropdown-box">
            <span className="selector-label">Lesson:</span>
            <select
              value={activeLessonId || topic.active_lesson_id || 'all'}
              onChange={(e) => onSelectLesson?.(e.target.value)}
              className="study-lesson-dropdown"
              title="Select lesson to view"
            >
              <option value="all">📖 Complete Guide (All Lessons in full)</option>
              {topic.lessons.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.title}
                </option>
              ))}
            </select>
          </div>

          <div className="selector-pills-box">
            <button
              className={`selector-pill-btn ${activeLessonId === 'all' ? 'active' : ''}`}
              onClick={() => onSelectLesson?.('all')}
              title="Complete Guide (All Lessons in full)"
            >
              All
            </button>
            {topic.lessons.map((l, idx) => {
              const isActive = (activeLessonId === l.id) || (!activeLessonId && idx === currentLessonIndex && activeLessonId !== 'all');
              return (
                <button
                  key={l.id}
                  className={`selector-pill-btn number-pill ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectLesson?.(l.id)}
                  title={l.title}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </div>
      )}

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
            <h3>{activeTab === 'labs' ? 'Labs not yet generated' : `Content not yet generated`}</h3>
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

        {/* Sequential Study Progression Navigation Footer */}
        {activeTab === 'study' && (
          <div className="lesson-bottom-nav">
            {topic.lessons && topic.lessons.length > 1 && activeLessonId !== 'all' ? (
              <>
                <button
                  className="btn-secondary-sm"
                  disabled={!prevLesson}
                  onClick={() => prevLesson && onSelectLesson?.(prevLesson.id)}
                  title={prevLesson ? prevLesson.title : ''}
                >
                  <ChevronLeft size={14} />
                  <span>{ui.previousLesson}</span>
                </button>
                <div className="bottom-nav-center">
                  <span className="lesson-progress-count">
                    Lesson {currentLessonIndex + 1} of {topic.lessons.length}
                  </span>
                  {onToggleLessonCompletion && currentLesson && (
                    <button
                      className={`btn-toggle-complete ${topic.completed_lessons?.includes(currentLesson.id) ? 'completed' : ''}`}
                      onClick={() => onToggleLessonCompletion(topic.path, currentLesson.id, !topic.completed_lessons?.includes(currentLesson.id))}
                      title={topic.completed_lessons?.includes(currentLesson.id) ? "Mark lesson incomplete" : "Mark lesson complete"}
                    >
                      <Check size={13} />
                      <span>{topic.completed_lessons?.includes(currentLesson.id) ? 'Completed ✓' : 'Mark Complete'}</span>
                    </button>
                  )}
                </div>
                {nextLesson ? (
                  <button
                    className="btn-secondary-sm"
                    onClick={() => onSelectLesson?.(nextLesson.id)}
                    title={nextLesson.title}
                  >
                    <span>{ui.nextLesson}</span>
                    <ChevronRight size={14} />
                  </button>
                ) : topic.labs ? (
                  <button
                    className="btn-secondary-sm primary-accent"
                    onClick={() => setActiveTab('labs')}
                    title="Continue to Hands-on Labs"
                  >
                    <span>Continue to Labs 🧪</span>
                    <ChevronRight size={14} />
                  </button>
                ) : (
                  <button
                    className="btn-secondary-sm primary-accent"
                    onClick={() => setActiveTab('quiz')}
                    title="Take Quiz"
                  >
                    <span>Take Quiz ❓</span>
                    <ChevronRight size={14} />
                  </button>
                )}
              </>
            ) : topic.labs ? (
              <button
                className="btn-secondary-sm primary-accent"
                onClick={() => setActiveTab('labs')}
                title="Continue to Hands-on Labs"
              >
                <span>Continue to Operational Labs 🧪</span>
                <ChevronRight size={14} />
              </button>
            ) : (
              <button
                className="btn-secondary-sm primary-accent"
                onClick={() => setActiveTab('quiz')}
                title="Test Comprehension"
              >
                <span>Test Comprehension with Quiz ❓</span>
                <ChevronRight size={14} />
              </button>
            )}
          </div>
        )}

        {/* Labs Bottom Navigation */}
        {activeTab === 'labs' && (
          <div className="lesson-bottom-nav">
            <button
              className="btn-secondary-sm"
              onClick={() => setActiveTab('study')}
            >
              <ChevronLeft size={14} />
              <span>Back to Study</span>
            </button>
            <button
              className="btn-secondary-sm primary-accent"
              onClick={() => setActiveTab('quiz')}
            >
              <span>Test Knowledge: Take Quiz ❓</span>
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Interactive Diagram & Image Zoom Lightbox Modal */}
      {zoomedMedia && (
        <div className="zoom-lightbox-backdrop" onClick={() => setZoomedMedia(null)}>
          <div className="zoom-lightbox-modal" onClick={(e) => e.stopPropagation()}>
            <div className="zoom-lightbox-header">
              <span className="zoom-lightbox-title">{zoomedMedia.title || 'Inspection View'}</span>
              <div className="zoom-controls">
                <button
                  className="zoom-btn"
                  onClick={() => setZoomScale((prev) => Math.max(prev - 0.25, 0.4))}
                  title="Zoom Out (-)"
                >
                  <ZoomOut size={14} />
                </button>
                <span className="zoom-scale-badge">{Math.round(zoomScale * 100)}%</span>
                <button
                  className="zoom-btn"
                  onClick={() => setZoomScale((prev) => Math.min(prev + 0.25, 4))}
                  title="Zoom In (+)"
                >
                  <ZoomIn size={14} />
                </button>
                <button
                  className="zoom-btn"
                  onClick={() => {
                    setZoomScale(1);
                    setTranslate({ x: 0, y: 0 });
                  }}
                  title="Reset Zoom (0)"
                >
                  <Maximize2 size={14} />
                </button>
                <button
                  className="zoom-btn close-btn"
                  onClick={() => setZoomedMedia(null)}
                  title="Close (Esc)"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            <div
              className={`zoom-lightbox-viewport ${isDragging ? 'grabbing' : 'grab'}`}
              onMouseDown={(e) => {
                setIsDragging(true);
                setDragStart({ x: e.clientX - translate.x, y: e.clientY - translate.y });
              }}
              onMouseMove={(e) => {
                if (!isDragging) return;
                setTranslate({
                  x: e.clientX - dragStart.x,
                  y: e.clientY - dragStart.y
                });
              }}
              onMouseUp={() => setIsDragging(false)}
              onMouseLeave={() => setIsDragging(false)}
              onWheel={(e) => {
                e.preventDefault();
                const delta = e.deltaY < 0 ? 0.15 : -0.15;
                setZoomScale((prev) => Math.min(Math.max(prev + delta, 0.4), 4));
              }}
            >
              {zoomedMedia.type === 'svg' ? (
                <div
                  className="zoomed-svg-wrapper"
                  style={{
                    transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoomScale})`
                  }}
                  dangerouslySetInnerHTML={{ __html: zoomedMedia.content }}
                />
              ) : (
                <img
                  src={zoomedMedia.content}
                  alt={zoomedMedia.title}
                  className="zoomed-image-wrapper"
                  style={{
                    transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoomScale})`
                  }}
                  draggable={false}
                />
              )}
            </div>

            <div className="zoom-lightbox-footer">
              <span>Drag to pan • Mouse wheel or +/- to zoom • Esc to close</span>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

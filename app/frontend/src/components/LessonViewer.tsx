import React, { useMemo } from 'react';
import { marked } from 'marked';
import {
  BookOpen,
  FlaskConical,
  GraduationCap,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import type { TopicDetails } from '../types';

interface LessonViewerProps {
  topic: TopicDetails | null;
  isLoading: boolean;
  isGenerating: boolean;
  onGenerate: (query: string, force?: boolean) => void;
  onRunInTerminal: (command: string) => void;
  activeTab: 'foundation' | 'lesson' | 'labs';
  setActiveTab: (tab: 'foundation' | 'lesson' | 'labs') => void;
}

export const LessonViewer: React.FC<LessonViewerProps> = ({
  topic,
  isLoading,
  isGenerating,
  onGenerate,
  onRunInTerminal,
  activeTab,
  setActiveTab,
}) => {
  const rawMarkdown = useMemo(() => {
    if (!topic) return '';
    if (activeTab === 'foundation') return topic.foundation;
    if (activeTab === 'lesson') return topic.lesson;
    if (activeTab === 'labs') return topic.labs;
    return '';
  }, [topic, activeTab]);

  const htmlContent = useMemo(() => {
    if (!rawMarkdown) return '';
    return marked.parse(rawMarkdown) as string;
  }, [rawMarkdown]);

  // Attach event listener to rendered markdown for interactive code block execution
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
        <p>Explore over 250 structured subtopics across Computing, Math, Sciences, and Arts.</p>
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
            onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`, true)}
            disabled={isGenerating}
            title="Regenerate all 3 units"
          >
            <RefreshCw size={13} className={isGenerating ? 'spin' : ''} />
            <span>{isGenerating ? 'Generating...' : 'Regenerate'}</span>
          </button>
        </div>
      </header>

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
      </div>

      <div className="viewer-scroll-body" onClick={handleContentClick}>
        {!hasAnyContent ? (
          <div className="viewer-missing-card">
            <Sparkles size={36} className="missing-icon" />
            <h3>No Content Generated Yet</h3>
            <p>
              This topic is structured in the curriculum but needs Foundation, Technical Lesson, and Lab guides.
            </p>
            <button
              className="btn-primary"
              onClick={() => onGenerate(`${topic.domain}/${topic.category}/${topic.subtopic}`)}
              disabled={isGenerating}
            >
              <Sparkles size={16} />
              <span>{isGenerating ? 'Synthesizing Units with AI...' : 'Generate Learning Units Now'}</span>
            </button>
          </div>
        ) : !rawMarkdown ? (
          <div className="viewer-missing-card">
            <h3>This unit is missing</h3>
            <p>You can generate or regenerate this topic module using the button in the top right.</p>
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

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { TopicTree } from './components/TopicTree';
import { LessonViewer } from './components/LessonViewer';
import { TutorChat } from './components/TutorChat';
import { TerminalDrawer } from './components/TerminalDrawer';
import { SearchModal } from './components/SearchModal';
import { GraphModal } from './components/GraphModal';
import { SettingsModal, DEFAULT_SETTINGS, type AppSettings } from './components/SettingsModal';
import { FlashcardStudyModal } from './components/FlashcardStudyModal';
import type { TerminalDrawerHandle } from './components/TerminalDrawer';
import type { TopicTreeData, TopicDetails, ChatMessage, WorkspaceStatus, QuizQuestion } from './types';
import './App.css';

export function App() {
  const [tree, setTree] = useState<TopicTreeData>({});
  const [mentorConnected, setMentorConnected] = useState<'checking' | 'connected' | 'error'>('checking');
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [topicDetails, setTopicDetails] = useState<TopicDetails | null>(null);
  const [currentLevel, setCurrentLevel] = useState<string>('beginner');
  const [activeTab, setActiveTab] = useState<'study' | 'labs' | 'quiz'>('study');
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
  const [isLoadingTopic, setIsLoadingTopic] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [isCompilingGuide, setIsCompilingGuide] = useState(false);
  const [isRegeneratingSummary, setIsRegeneratingSummary] = useState(false);
  const [unifiedChatHistory, setUnifiedChatHistory] = useState<ChatMessage[]>([]);
  const [quizQuestions, setQuizQuestions] = useState<{ [key: string]: QuizQuestion[] }>({});
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState<'appearance' | 'cluster' | 'models' | 'store'>('appearance');
  const [flashcardModalOpen, setFlashcardModalOpen] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(() => {
    try {
      const saved = localStorage.getItem('synapse_app_settings');
      return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const checkConnectivity = useCallback(async () => {
    setMentorConnected('checking');
    try {
      const res = await fetch('/api/check-mentor-connectivity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: settings.ollamaHost,
          model: settings.mentorModel
        }),
      });
      const data = await res.json();
      setMentorConnected(data.connected ? 'connected' : 'error');
    } catch {
      setMentorConnected('error');
    }
  }, [settings.ollamaHost, settings.mentorModel]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.theme);
    document.documentElement.setAttribute('data-fontsize', settings.fontSize);
    document.documentElement.setAttribute('data-readerwidth', settings.readerWidth);
    document.documentElement.setAttribute('data-fontfamily', settings.fontFamily || 'sans');
    document.documentElement.setAttribute('data-accent', settings.accentColor || 'gold');
    document.documentElement.setAttribute('data-lineheight', settings.lineHeight || 'balanced');
    
    checkConnectivity();
  }, [settings, checkConnectivity]);

  const handleSaveSettings = (newSettings: AppSettings) => {
    setSettings(newSettings);
    localStorage.setItem('synapse_app_settings', JSON.stringify(newSettings));
  };

  const terminalRef = useRef<TerminalDrawerHandle>(null);
  const [terminalConnected, setTerminalConnected] = useState(false);

  const fetchTree = async () => {
    try {
      const res = await fetch('/api/tree');
      if (res.ok) {
        const data = await res.json();
        setTree(data);
      }
    } catch (err) {
      console.error('Failed to load topic tree:', err);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        setWorkspaceStatus(data);
      }
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  const loadTopic = async (query: string, level = currentLevel, preserveTab = false, lessonId?: string) => {
    setIsLoadingTopic(true);
    try {
      let url = `/api/topic?query=${encodeURIComponent(query)}&level=${level}`;
      if (lessonId && lessonId !== 'all' && lessonId !== 'labs') {
        url += `&lesson_id=${encodeURIComponent(lessonId)}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setTopicDetails(data);
        setSelectedPath(query);
        setCurrentLevel(level);
        setUnifiedChatHistory(data.chat_history || []);

        if (lessonId === 'labs') {
          setActiveTab('labs');
          setActiveLessonId('labs');
        } else if (lessonId === 'all') {
          setActiveLessonId('all');
          if (!preserveTab) setActiveTab('study');
        } else if (lessonId) {
          setActiveLessonId(lessonId);
          if (!preserveTab) setActiveTab('study');
        } else {
          setActiveLessonId(data.active_lesson_id || null);
          if (!preserveTab) {
            setActiveTab('study');
          }
        }
      }
    } catch (err) {
      console.error('Failed to load topic details:', err);
    } finally {
      setIsLoadingTopic(false);
    }
  };

  useEffect(() => {
    fetchTree();
    fetchStatus();
  }, []);

  const handleGenerate = async (query: string, force = false, level = currentLevel) => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, force, level }),
      });
      if (res.ok) {
        await loadTopic(query, level);
        await fetchTree();
        await fetchStatus();
      }
    } catch (err) {
      console.error('Failed to generate topic content:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAddSubtopic = async (domain: string, category: string, subtopic: string, title?: string) => {
    const res = await fetch('/api/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, category, subtopic, title, generate: true }),
    });
    if (res.ok) {
      await fetchTree();
      await fetchStatus();
      const newRel = `${domain}/${category}/${subtopic}`;
      await loadTopic(newRel, 'beginner');
    }
  };

  const handleDeleteTopic = async (path: string) => {
    if (!window.confirm(`Are you sure you want to delete '${path}'? This will remove all files and update the syllabus.`)) {
      return;
    }
    try {
      const res = await fetch(`/api/topic?path=${encodeURIComponent(path)}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        if (selectedPath === path || selectedPath?.startsWith(path)) {
          setSelectedPath(null);
          setTopicDetails(null);
        }
        await fetchTree();
        await fetchStatus();
      }
    } catch (err) {
      console.error('Failed to delete topic:', err);
    }
  };

  const handleRenameTopic = async (path: string, newTitle: string) => {
    try {
      const res = await fetch('/api/topic/rename', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, new_title: newTitle }),
      });
      if (res.ok) {
        await fetchTree();
      }
    } catch (err) {
      console.error('Failed to rename topic:', err);
    }
  };

  const handleSelectLevel = (level: string) => {
    setCurrentLevel(level);
    if (selectedPath) {
      loadTopic(selectedPath, level, true);
    }
  };

  const handleSelectSubtopic = (query: string, lessonId?: string) => {
    loadTopic(query, currentLevel, false, lessonId);
  };

  const handleSelectLesson = (lessonId: string) => {
    if (selectedPath) {
      setActiveLessonId(lessonId);
      if (lessonId === 'labs') {
        setActiveTab('labs');
      } else {
        setActiveTab('study');
        loadTopic(selectedPath, currentLevel, true, lessonId);
      }
    }
  };

  const handleToggleLessonCompletion = async (path: string, lessonId: string, completed?: boolean) => {
    try {
      const res = await fetch('/api/mastery/lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, lesson_id: lessonId, completed }),
      });
      if (res.ok) {
        const data = await res.json();
        setTopicDetails((prev) => prev ? {
          ...prev,
          completed_lessons: data.completed_lessons,
          mastery: data.state
        } : null);
        await fetchTree();
      }
    } catch (err) {
      console.error('Failed to toggle lesson completion:', err);
    }
  };

  const contentRef = useRef<HTMLDivElement>(null);

  // Global Ergonomic Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

      // Cmd/Ctrl + K: Open Search anywhere
      if (isMod && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen(true);
        return;
      }

      // Cmd/Ctrl + B or Cmd/Ctrl + \: Toggle Sandbox Terminal Drawer
      if (isMod && (e.key.toLowerCase() === 'b' || e.key === '\\')) {
        e.preventDefault();
        setTerminalOpen((prev: boolean) => !prev);
        return;
      }

      // Do not trigger single-key or navigation shortcuts while actively typing in input/textarea
      if (isTyping) return;

      // Cmd/Ctrl + 1 / 2 / 3: Switch Tabs
      if (isMod && e.key === '1') {
        e.preventDefault();
        setActiveTab('study');
        return;
      }
      if (isMod && e.key === '2') {
        e.preventDefault();
        setActiveTab('labs');
        return;
      }
      if (isMod && e.key === '3') {
        e.preventDefault();
        setActiveTab('quiz');
        return;
      }

      // [ or Cmd+[: Previous Lesson
      if (e.key === '[' || (isMod && e.key === 'ArrowLeft')) {
        const lessons = topicDetails?.lessons || [];
        if (lessons.length > 1 && activeLessonId) {
          const idx = lessons.findIndex((l) => l.id === activeLessonId);
          if (idx > 0) {
            e.preventDefault();
            handleSelectLesson(lessons[idx - 1].id);
          }
        }
        return;
      }

      // ] or Cmd+J or Cmd+Right: Next Lesson
      if (e.key === ']' || (isMod && (e.key.toLowerCase() === 'j' || e.key === 'ArrowRight'))) {
        const lessons = topicDetails?.lessons || [];
        if (lessons.length > 1 && activeLessonId) {
          const idx = lessons.findIndex((l) => l.id === activeLessonId);
          if (idx >= 0 && idx < lessons.length - 1) {
            e.preventDefault();
            handleSelectLesson(lessons[idx + 1].id);
          }
        }
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [topicDetails, activeLessonId]);

  const handleSendMessage = async (msg: string) => {
    const newStudentMsg: ChatMessage = { role: 'student', content: msg };
    const updatedHistory = [...unifiedChatHistory, newStudentMsg];
    setUnifiedChatHistory(updatedHistory);

    // Initial placeholder tutor message for real-time token streaming
    const placeholderTutorMsg: ChatMessage = { role: 'tutor', content: '' };
    setUnifiedChatHistory([...updatedHistory, placeholderTutorMsg]);

    setIsChatting(true);
    try {
      let terminalOutput = terminalRef.current?.getRecentOutput?.(40) || '';
      let lastTerminalCommand = '';
      try {
        const termRes = await fetch('/api/terminal/buffer?lines=40');
        if (termRes.ok) {
          const termData = await termRes.json();
          if (!terminalOutput.trim()) {
            terminalOutput = termData.text || '';
          }
          lastTerminalCommand = termData.last_command || '';
        }
      } catch {
        // ignore
      }

      // Extract clean lesson markdown content and title from topicDetails
      let lessonContent = '';
      let lessonTitle = '';

      if (activeTab === 'labs') {
        lessonTitle = 'Operational Labs';
        lessonContent = topicDetails?.labs || '';
      } else if (activeLessonId && activeLessonId !== 'all' && topicDetails?.lessons) {
        const current = topicDetails.lessons.find((l) => l.id === activeLessonId);
        lessonTitle = current?.title || '';
        lessonContent = current?.content || topicDetails?.lesson || '';
      } else {
        lessonTitle = topicDetails?.active_lesson_title || (topicDetails?.subtopic ? topicDetails.subtopic.replace(/_/g, ' ') : 'Curriculum Guide');
        lessonContent = topicDetails?.lesson || topicDetails?.full_content || topicDetails?.foundation || '';
      }

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: selectedPath || '',
          lesson_id: activeLessonId,
          lesson_title: lessonTitle,
          message: msg,
          history: unifiedChatHistory,
          terminal_context: terminalOutput,
          last_terminal_command: lastTerminalCommand,
          lesson_content: lessonContent,
          language: settings.language,
          stream: true,
          model: settings.mentorModel || undefined,
          host: settings.ollamaHost || undefined,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned ${res.status}`);
      }

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedReply = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const textChunk = decoder.decode(value, { stream: true });
          const lines = textChunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.slice(6));
                if (parsed.chunk) {
                  accumulatedReply += parsed.chunk;
                  setUnifiedChatHistory([
                    ...updatedHistory,
                    { role: 'tutor', content: accumulatedReply }
                  ]);
                }
                if (parsed.done && parsed.full_reply) {
                  accumulatedReply = parsed.full_reply;
                  setUnifiedChatHistory([
                    ...updatedHistory,
                    { role: 'tutor', content: accumulatedReply }
                  ]);
                }
              } catch {
                // Ignore partial JSON chunks
              }
            }
          }
        }
      } else {
        const data = await res.json();
        setUnifiedChatHistory([
          ...updatedHistory,
          { role: 'tutor', content: data.reply }
        ]);
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      const detail = err.message || 'Connection failed';
      setUnifiedChatHistory([
        ...updatedHistory,
        {
          role: 'tutor',
          content: `⚠️ **Unable to connect to AI Mentor** (${detail}).\n\n**To resolve:**\n1. Verify active cluster nodes in **Settings ⚙ → AI Models & Cloud API**.\n2. Ensure your Ollama or LocalAI node is online with a loaded model.\n3. Or enter an Anthropic or Gemini API key for instant cloud mentoring.`
        }
      ]);
    } finally {
      setIsChatting(false);
    }
  };

  const handleCompileGuide = async () => {
    if (!selectedPath) return;

    setIsCompilingGuide(true);
    try {
      const res = await fetch('/api/artifacts/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: selectedPath }),
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Mastered Field Guide compiled to ${data.path} and committed to Git!`);
      }
    } catch (err) {
      console.error('Failed to compile guide:', err);
    } finally {
      setIsCompilingGuide(false);
    }
  };

  const handleNavigateBreadcrumb = (type: 'domain' | 'category' | 'subtopic', path: string) => {
    if (type === 'subtopic') {
      loadTopic(path, currentLevel);
      return;
    }

    for (const [domain, ddata] of Object.entries(tree)) {
      if (type === 'domain' && domain === path) {
        for (const discData of Object.values(ddata.disciplines || {})) {
          for (const cData of Object.values((discData as any).courses || {})) {
            const units = Object.values((cData as any).units || {});
            if (units.length > 0) {
              loadTopic((units[0] as any).rel_path, currentLevel);
              return;
            }
          }
        }
      }
      if (type === 'category') {
        for (const [disc, discData] of Object.entries(ddata.disciplines || {})) {
          for (const [courseSlug, cData] of Object.entries((discData as any).courses || {})) {
            const courseKey = `${domain}/${disc}/${courseSlug}`;
            const discKey = `${domain}/${disc}`;
            if (path === courseKey || path === discKey) {
              const units = Object.values((cData as any).units || {});
              if (units.length > 0) {
                loadTopic((units[0] as any).rel_path, currentLevel);
                return;
              }
            }
          }
        }
      }
    }
  };

  const handleRefreshQuiz = async () => {
    if (!selectedPath) return;

    const quizKey = `${selectedPath}/${currentLevel}`;
    setIsLoadingQuiz(true);
    try {
      const res = await fetch('/api/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: selectedPath }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuizQuestions((prev) => ({
          ...prev,
          [quizKey]: data.questions || [],
        }));
      }
    } catch (err) {
      console.error('Failed to fetch quiz:', err);
    } finally {
      setIsLoadingQuiz(false);
    }
  };

  const handleRunInTerminal = (cmd: string) => {
    if (terminalRef.current) {
      terminalRef.current.runCommand(cmd);
      setTerminalOpen(true);
    }
  };

  const handleUpdateMastery = async (state: string) => {
    if (!selectedPath) return;
    try {
      const res = await fetch('/api/mastery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selectedPath, state }),
      });
      if (res.ok) {
        if (topicDetails) {
          setTopicDetails({ ...topicDetails, mastery: state });
        }
      }
    } catch (err) {
      console.error('Failed to update mastery:', err);
    }
  };

  const handleDownloadFlashcards = () => {
    if (!selectedPath) return;
    window.open(`/api/flashcards?query=${encodeURIComponent(selectedPath)}`, '_blank');
  };

  const handleDownloadHandbook = () => {
    if (!topicDetails) return;
    window.open(`/api/export?domain=${encodeURIComponent(topicDetails.domain)}&level=${currentLevel}`, '_blank');
  };

  const handleRegenerateSummary = async () => {
    if (!selectedPath) return;
    setIsRegeneratingSummary(true);
    try {
      const res = await fetch('/api/summary/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: selectedPath }),
      });
      if (res.ok) {
        const data = await res.json();
        if (topicDetails) {
          setTopicDetails({ ...topicDetails, summary: data.summary });
        }
      }
    } catch (err) {
      console.error('Failed to regenerate summary:', err);
    } finally {
      setIsRegeneratingSummary(false);
    }
  };

  const currentQuiz = selectedPath ? quizQuestions[`${selectedPath}/${currentLevel}`] || [] : [];

  const activeLessonTitle = useMemo(() => {
    if (!topicDetails) return null;
    if (activeTab === 'labs') return 'Operational Labs';
    if (activeLessonId && activeLessonId !== 'all' && topicDetails.lessons) {
      const cur = topicDetails.lessons.find((l) => l.id === activeLessonId);
      return cur?.title || topicDetails.active_lesson_title || 'Active Lesson';
    }
    return topicDetails.active_lesson_title || (topicDetails.subtopic ? topicDetails.subtopic.replace(/_/g, ' ') : 'Complete Masterclass');
  }, [topicDetails, activeTab, activeLessonId]);

  return (
    <div className="workbench-layout">
      <TopicTree
        tree={tree}
        selectedSubtopic={selectedPath}
        activeLessonId={activeLessonId}
        activeTab={activeTab}
        status={workspaceStatus}
        completedLessons={topicDetails?.completed_lessons}
        onSelectSubtopic={handleSelectSubtopic}
        onAddSubtopic={handleAddSubtopic}
        onOpenSearch={() => setSearchOpen(true)}
        onOpenGraph={() => setGraphOpen(true)}
        onOpenSettings={() => {
          setSettingsTab('appearance');
          setSettingsOpen(true);
        }}
        onOpenStore={() => {
          setSettingsTab('store');
          setSettingsOpen(true);
        }}
        onDeleteTopic={handleDeleteTopic}
        onRenameTopic={handleRenameTopic}
        onToggleLessonCompletion={handleToggleLessonCompletion}
        targetLanguage={settings.language}
      />

      <div className="center-workspace-column">
        <LessonViewer
          topic={topicDetails}
          contentRef={contentRef as React.RefObject<HTMLDivElement>}
          isLoading={isLoadingTopic}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
          onRunInTerminal={handleRunInTerminal}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          activeLessonId={activeLessonId}
          currentLevel={currentLevel}
          onSelectLevel={handleSelectLevel}
          quizQuestions={currentQuiz}
          isLoadingQuiz={isLoadingQuiz}
          onRefreshQuiz={handleRefreshQuiz}
          onCompileGuide={handleCompileGuide}
          isCompiling={isCompilingGuide}
          onUpdateMastery={handleUpdateMastery}
          onDownloadFlashcards={handleDownloadFlashcards}
          onDownloadHandbook={handleDownloadHandbook}
          onRegenerateSummary={handleRegenerateSummary}
          isRegeneratingSummary={isRegeneratingSummary}
          onOpenFlashcards={() => setFlashcardModalOpen(true)}
          targetLanguage={settings.language}
          onNavigateBreadcrumb={handleNavigateBreadcrumb}
          onSelectLesson={handleSelectLesson}
          onToggleLessonCompletion={handleToggleLessonCompletion}
        />

        <TerminalDrawer
          ref={terminalRef}
          isOpen={terminalOpen}
          onToggle={() => setTerminalOpen((prev: boolean) => !prev)}
          onConnectionChange={setTerminalConnected}
        />
      </div>

      <TutorChat
        topic={topicDetails}
        activeLessonTitle={activeLessonTitle}
        history={unifiedChatHistory}
        isChatting={isChatting}
        onSendMessage={handleSendMessage}
        onClearChat={() => setUnifiedChatHistory([])}
        isTerminalConnected={terminalConnected}
        mentorConnected={mentorConnected}
        onToggleTerminal={() => setTerminalOpen((prev: boolean) => !prev)}
        targetLanguage={settings.language}
      />

      <SearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectTopic={(path, lvl) => loadTopic(path, lvl || currentLevel)}
      />

      <GraphModal
        isOpen={graphOpen}
        onClose={() => setGraphOpen(false)}
        onSelectTopic={(path) => loadTopic(path, currentLevel)}
      />

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onSaveSettings={handleSaveSettings}
        initialTab={settingsTab}
      />

      <FlashcardStudyModal
        isOpen={flashcardModalOpen}
        onClose={() => setFlashcardModalOpen(false)}
        topicPath={selectedPath || ''}
        topicTitle={topicDetails?.subtopic.replace(/_/g, ' ') || 'Flashcard Deck'}
      />
    </div>
  );
}

export default App;

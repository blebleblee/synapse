import { useState, useEffect, useRef } from 'react';
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
  const [, setStatus] = useState<WorkspaceStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [topicDetails, setTopicDetails] = useState<TopicDetails | null>(null);
  const [currentLevel, setCurrentLevel] = useState<string>('beginner');
  const [activeTab, setActiveTab] = useState<'summary' | 'foundation' | 'lesson' | 'labs' | 'quiz'>('summary');
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
  const [flashcardModalOpen, setFlashcardModalOpen] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(() => {
    try {
      const saved = localStorage.getItem('synapse_app_settings');
      return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.theme);
    document.documentElement.setAttribute('data-fontsize', settings.fontSize);
    document.documentElement.setAttribute('data-readerwidth', settings.readerWidth);
  }, [settings]);

  const handleSaveSettings = (newSettings: AppSettings) => {
    setSettings(newSettings);
    localStorage.setItem('synapse_app_settings', JSON.stringify(newSettings));
  };

  const terminalRef = useRef<TerminalDrawerHandle>(null);

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
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  const loadTopic = async (query: string, level = currentLevel, preserveTab = false) => {
    setIsLoadingTopic(true);
    try {
      const res = await fetch(`/api/topic?query=${encodeURIComponent(query)}&level=${level}`);
      if (res.ok) {
        const data = await res.json();
        setTopicDetails(data);
        setSelectedPath(query);
        setCurrentLevel(level);

        // Only override tab when opening a new topic, NOT when switching levels
        if (!preserveTab) {
          if (data.summary) {
            setActiveTab('summary');
          } else if (data.foundation) {
            setActiveTab('foundation');
          } else if (data.lesson) {
            setActiveTab('lesson');
          } else if (data.labs) {
            setActiveTab('labs');
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

  const handleSendMessage = async (msg: string) => {
    const newStudentMsg: ChatMessage = { role: 'student', content: msg };
    const updatedHistory = [...unifiedChatHistory, newStudentMsg];
    setUnifiedChatHistory(updatedHistory);

    setIsChatting(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: selectedPath || 'computing/infrastructure/kubernetes/01_control_plane_and_etcd',
          message: msg,
          history: updatedHistory,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const newTutorMsg: ChatMessage = { role: 'tutor', content: data.reply };
        setUnifiedChatHistory([...updatedHistory, newTutorMsg]);
      }
    } catch (err) {
      console.error('Chat error:', err);
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
        alert(`Mastered Field Guide compiled to ${data.path} and committed to Gitea!`);
      }
    } catch (err) {
      console.error('Failed to compile guide:', err);
    } finally {
      setIsCompilingGuide(false);
    }
  };

  const handleNavigateBreadcrumb = (type: 'domain' | 'category' | 'subtopic', path: string) => {
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

  return (
    <div className="workbench-layout">
      <div className="workbench-main-row">
        <TopicTree
          tree={tree}
          selectedSubtopic={selectedPath}
          onSelectSubtopic={(q) => loadTopic(q, currentLevel)}
          onAddSubtopic={handleAddSubtopic}
          onOpenSearch={() => setSearchOpen(true)}
          onOpenGraph={() => setGraphOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
          onDeleteTopic={handleDeleteTopic}
          onRenameTopic={handleRenameTopic}
        />

        <LessonViewer
          topic={topicDetails}
          isLoading={isLoadingTopic}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
          onRunInTerminal={handleRunInTerminal}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
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
        />

        <TutorChat
          topic={topicDetails}
          history={unifiedChatHistory}
          isChatting={isChatting}
          onSendMessage={handleSendMessage}
          onClearChat={() => setUnifiedChatHistory([])}
        />
      </div>

      <TerminalDrawer
        ref={terminalRef}
        isOpen={terminalOpen}
        onToggle={() => setTerminalOpen((prev) => !prev)}
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

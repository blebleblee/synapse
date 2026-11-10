import { useState, useEffect, useRef } from 'react';
import { TopicTree } from './components/TopicTree';
import { LessonViewer } from './components/LessonViewer';
import { TutorChat } from './components/TutorChat';
import { TerminalDrawer } from './components/TerminalDrawer';
import type { TerminalDrawerHandle } from './components/TerminalDrawer';
import type { TopicTreeData, TopicDetails, ChatMessage, WorkspaceStatus, QuizQuestion } from './types';
import './App.css';

export function App() {
  const [tree, setTree] = useState<TopicTreeData>({});
  const [, setStatus] = useState<WorkspaceStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [topicDetails, setTopicDetails] = useState<TopicDetails | null>(null);
  const [activeTab, setActiveTab] = useState<'foundation' | 'lesson' | 'labs' | 'quiz'>('foundation');
  const [isLoadingTopic, setIsLoadingTopic] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [isSavingSession, setIsSavingSession] = useState(false);
  const [isCompilingGuide, setIsCompilingGuide] = useState(false);
  const [chatHistory, setChatHistory] = useState<{ [key: string]: ChatMessage[] }>({});
  const [quizQuestions, setQuizQuestions] = useState<{ [key: string]: QuizQuestion[] }>({});
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [terminalOpen, setTerminalOpen] = useState(true);

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

  const loadTopic = async (query: string) => {
    setIsLoadingTopic(true);
    try {
      const res = await fetch(`/api/topic?query=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        setTopicDetails(data);
        setSelectedPath(query);

        // Pick initial active tab based on what exists
        if (data.foundation) {
          setActiveTab('foundation');
        } else if (data.lesson) {
          setActiveTab('lesson');
        } else if (data.labs) {
          setActiveTab('labs');
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

    // Auto-select ebpf as initial showcase topic
    loadTopic('computing_and_engineering/infrastructure_and_ops/ebpf');
  }, []);

  const handleGenerate = async (query: string, force = false) => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, force }),
      });
      if (res.ok) {
        await loadTopic(query);
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
      await loadTopic(newRel);
    }
  };

  const handleSendMessage = async (msg: string) => {
    if (!selectedPath || !topicDetails) return;

    const currentHistory = chatHistory[selectedPath] || [];
    const newStudentMsg: ChatMessage = { role: 'student', content: msg };
    const updatedHistory = [...currentHistory, newStudentMsg];

    setChatHistory((prev) => ({
      ...prev,
      [selectedPath]: updatedHistory,
    }));

    setIsChatting(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: selectedPath,
          message: msg,
          history: updatedHistory,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const newTutorMsg: ChatMessage = { role: 'tutor', content: data.reply };
        setChatHistory((prev) => ({
          ...prev,
          [selectedPath]: [...updatedHistory, newTutorMsg],
        }));
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsChatting(false);
    }
  };

  const handleSaveSession = async () => {
    if (!selectedPath) return;
    const history = chatHistory[selectedPath] || [];
    if (history.length === 0) return;

    setIsSavingSession(true);
    try {
      const res = await fetch('/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: selectedPath, history }),
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Session debrief saved to ${data.path} and committed to Gitea!`);
      }
    } catch (err) {
      console.error('Failed to save session:', err);
    } finally {
      setIsSavingSession(false);
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

  const handleRefreshQuiz = async () => {
    if (!selectedPath) return;

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
          [selectedPath]: data.questions || [],
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

  const currentQuiz = selectedPath ? quizQuestions[selectedPath] || [] : [];

  return (
    <div className="workbench-layout">
      <div className="workbench-main-row">
        <TopicTree
          tree={tree}
          selectedSubtopic={selectedPath}
          onSelectSubtopic={loadTopic}
          onAddSubtopic={handleAddSubtopic}
        />

        <LessonViewer
          topic={topicDetails}
          isLoading={isLoadingTopic}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
          onRunInTerminal={handleRunInTerminal}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          quizQuestions={currentQuiz}
          isLoadingQuiz={isLoadingQuiz}
          onRefreshQuiz={handleRefreshQuiz}
          onCompileGuide={handleCompileGuide}
          isCompiling={isCompilingGuide}
        />

        <TutorChat
          topic={topicDetails}
          history={selectedPath ? chatHistory[selectedPath] || [] : []}
          isChatting={isChatting}
          onSendMessage={handleSendMessage}
          onSaveSession={handleSaveSession}
          isSavingSession={isSavingSession}
        />
      </div>

      <TerminalDrawer
        ref={terminalRef}
        isOpen={terminalOpen}
        onToggle={() => setTerminalOpen((prev) => !prev)}
      />
    </div>
  );
}

export default App;

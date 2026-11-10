import { useState, useEffect, useRef } from 'react';
import { TopicTree } from './components/TopicTree';
import { LessonViewer } from './components/LessonViewer';
import { TutorChat } from './components/TutorChat';
import { TerminalDrawer } from './components/TerminalDrawer';
import type { TerminalDrawerHandle } from './components/TerminalDrawer';
import type { TopicTreeData, TopicDetails, ChatMessage, WorkspaceStatus } from './types';
import './App.css';

export function App() {
  const [tree, setTree] = useState<TopicTreeData>({});
  const [, setStatus] = useState<WorkspaceStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [topicDetails, setTopicDetails] = useState<TopicDetails | null>(null);
  const [activeTab, setActiveTab] = useState<'foundation' | 'lesson' | 'labs'>('foundation');
  const [isLoadingTopic, setIsLoadingTopic] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [chatHistory, setChatHistory] = useState<{ [key: string]: ChatMessage[] }>({});
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

  const handleRunInTerminal = (cmd: string) => {
    if (terminalRef.current) {
      terminalRef.current.runCommand(cmd);
      setTerminalOpen(true);
    }
  };

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
        />

        <TutorChat
          topic={topicDetails}
          history={selectedPath ? chatHistory[selectedPath] || [] : []}
          isChatting={isChatting}
          onSendMessage={handleSendMessage}
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

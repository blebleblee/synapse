import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Loader2, Square } from 'lucide-react';
import { TopicTree } from './components/TopicTree';
import { LessonViewer } from './components/LessonViewer';
import { TutorChat } from './components/TutorChat';
import { TerminalDrawer } from './components/TerminalDrawer';
import { SearchModal } from './components/SearchModal';
import { GraphModal } from './components/GraphModal';
import { SettingsModal } from './components/SettingsModal';
import { DEFAULT_SETTINGS, type AppSettings } from './components/settingsDefaults';
import { SetupWizardModal } from './components/SetupWizardModal';
import { FlashcardStudyModal } from './components/FlashcardStudyModal';
import { LoginModal } from './components/LoginModal';
import type { TerminalDrawerHandle } from './components/TerminalDrawer';
import type { TopicTreeData, TopicDetails, ChatMessage, WorkspaceStatus, QuizQuestion } from './types';
import { getStoredSelection, saveStoredSelection, clearStoredSelection } from './utils/selectionStorage';
import { NoticeStack, type Notice, type NoticeKind } from './components/NoticeStack';
import { summarizeGeneration } from './utils/generation';
import { useCourseTranslationStatus, useReadingLang } from './utils/translationStatus';
import { TranslationQueueIndicator } from './components/TranslationQueueIndicator';
import { failureMessage, networkFailure } from './utils/failureMessage';
import { toTitleCase } from './utils/text';
import './App.css';

// The page can load before the server answers (desktop start-up, a server
// restart). Wait for it, up to about a minute, before loading anything.
async function waitForBackend(attempts = 40, delayMs = 1500): Promise<void> {
  for (let i = 0; i < attempts; i++) {
    try {
      await fetch('/api/health');
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
}

type MentorCheck = { status: 'connected' | 'error'; model?: string };

// `model` is the model the mentor will actually answer with, which can be a
// fallback when the configured one is not installed.
async function mentorStatus(host: string, model?: string): Promise<MentorCheck> {
  try {
    const res = await fetch('/api/check-mentor-connectivity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host, model }),
    });
    const data = await res.json();
    return data.connected
      ? { status: 'connected', model: typeof data.model === 'string' ? data.model : undefined }
      : { status: 'error' };
  } catch {
    return { status: 'error' };
  }
}

function App() {
  const [tree, setTree] = useState<TopicTreeData>({});
  const [treeLoaded, setTreeLoaded] = useState(false);
  const [mentorConnected, setMentorConnected] = useState<'checking' | 'connected' | 'error'>('checking');
  const [mentorActiveModel, setMentorActiveModel] = useState<string | undefined>(undefined);
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [topicDetails, setTopicDetails] = useState<TopicDetails | null>(null);
  const [activeTab, setActiveTab] = useState<'study' | 'labs' | 'quiz'>('study');
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
  const [targetSection, setTargetSection] = useState<string | null>(null);
  const [isLoadingTopic, setIsLoadingTopic] = useState(false);
  const loadRequestIdRef = useRef<number>(0);
  const userInteractedRef = useRef<boolean>(false);
  const chatRequestIdRef = useRef<number>(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [unifiedChatHistory, setUnifiedChatHistory] = useState<ChatMessage[]>([]);
  const [quizQuestions, setQuizQuestions] = useState<{ [key: string]: QuizQuestion[] }>({});
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const activeCancelHandler = useRef<(() => void) | null>(null);
  const serverCancelRef = useRef<(() => void) | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const noticeIdRef = useRef(0);
  const dismissNotice = useCallback((id: number) => {
    setNotices((prev) => prev.filter((n) => n.id !== id));
  }, []);
  // Every user action ends visibly: a result, or a reason it failed.
  const notify = useCallback((kind: NoticeKind, text: string) => {
    const id = ++noticeIdRef.current;
    setNotices((prev) => [...prev.slice(-3), { id, kind, text }]);
    window.setTimeout(() => dismissNotice(id), kind === 'error' ? 12000 : 5000);
  }, [dismissNotice]);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [setupWizardOpen, setSetupWizardOpen] = useState<boolean>(() => {
    return localStorage.getItem('synapse_onboarding_completed') !== 'true' && !localStorage.getItem('synapse_app_settings');
  });
  const [settingsTab, setSettingsTab] = useState<'appearance' | 'cluster' | 'models' | 'store'>('appearance');
  const [flashcardModalOpen, setFlashcardModalOpen] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  // False until the first /api/auth/status answer: until then we don't know
  // whether protected endpoints would only answer 401.
  const [authChecked, setAuthChecked] = useState(false);

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch('/api/auth/status');
      if (res.ok) {
        const data = await res.json();
        setAuthRequired(Boolean(data.auth_required));
        setIsAuthenticated(Boolean(data.authenticated));
        return !data.auth_required || Boolean(data.authenticated);
      }
    } catch {
      // ignore
    } finally {
      setAuthChecked(true);
    }
    return true;
  }, []);
  const apiUnlocked = authChecked && !(authRequired && !isAuthenticated);
  // Reading language and the open course's translations (sidebar markers, reader).
  const readingLang = useReadingLang();
  const courseTranslations = useCourseTranslationStatus(selectedPath, readingLang, apiUnlocked);
  const [settings, setSettings] = useState<AppSettings>(() => {
    try {
      const saved = localStorage.getItem('synapse_app_settings');
      return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  // Keeps the current status until the answer arrives; callers that want
  // "checking" shown (saving a new host or model) set it themselves.
  const checkConnectivity = useCallback(async () => {
    if (!apiUnlocked) return;
    const check = await mentorStatus(settings.ollamaHost, settings.mentorModel);
    setMentorConnected(check.status);
    setMentorActiveModel(check.model);
  }, [settings.ollamaHost, settings.mentorModel, apiUnlocked]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.theme);
    document.documentElement.setAttribute('data-fontsize', settings.fontSize);
    document.documentElement.setAttribute('data-readerwidth', settings.readerWidth);
    document.documentElement.setAttribute('data-fontfamily', settings.fontFamily || 'sans');
    document.documentElement.setAttribute('data-accent', settings.accentColor || 'gold');
    document.documentElement.setAttribute('data-lineheight', settings.lineHeight || 'balanced');
  }, [settings]);

  // Re-check the mentor when its host or model changes (not on theme changes).
  // Quiet: the status starts as 'checking', and saving new settings sets it.
  useEffect(() => {
    if (!apiUnlocked) return;
    let live = true;
    mentorStatus(settings.ollamaHost, settings.mentorModel).then((check) => {
      if (!live) return;
      setMentorConnected(check.status);
      setMentorActiveModel(check.model);
    });
    return () => { live = false; };
  }, [settings.ollamaHost, settings.mentorModel, apiUnlocked]);

  // The startup check can miss a local model that is still starting or busy.
  // While offline, re-check quietly every 15 s and when the window regains focus.
  useEffect(() => {
    if (mentorConnected !== 'error') return;
    const recheck = () => { void checkConnectivity(); };
    const timer = window.setInterval(recheck, 15000);
    window.addEventListener('focus', recheck);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', recheck);
    };
  }, [mentorConnected, checkConnectivity]);

  const handleSaveSettings = (newSettings: AppSettings) => {
    if (newSettings.ollamaHost !== settings.ollamaHost || newSettings.mentorModel !== settings.mentorModel) {
      setMentorConnected('checking');
    }
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
        setTreeLoaded(true);
      } else if (res.status !== 401) {
        notify('error', await failureMessage(res, 'Loading the curriculum'));
      }
    } catch (err) {
      console.error('Failed to load topic tree:', err);
      notify('error', networkFailure('Loading the curriculum', err));
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

  const loadTopic = async (query: string, preserveTab = false, lessonId?: string, isRestore = false) => {
    const currentRequestId = ++loadRequestIdRef.current;
    if (!isRestore) {
      userInteractedRef.current = true;
      activeCancelHandler.current?.();
      chatRequestIdRef.current += 1;
    } else if (userInteractedRef.current) {
      return;
    }

    setIsLoadingTopic(true);
    try {
      let url = `/api/topic?query=${encodeURIComponent(query)}`;
      if (lessonId && lessonId !== 'all' && lessonId !== 'labs') {
        url += `&lesson_id=${encodeURIComponent(lessonId)}`;
      }
      const res = await fetch(url);
      if (currentRequestId !== loadRequestIdRef.current) return;
      if (isRestore && userInteractedRef.current) return;

      if (res.ok) {
        const data: TopicDetails = await res.json();
        if (currentRequestId !== loadRequestIdRef.current) return;
        if (isRestore && userInteractedRef.current) return;

        setTopicDetails(data);
        setSelectedPath(query);
        setUnifiedChatHistory(data.chat_history || []);

        let effectiveLessonId = 'all';
        if (lessonId === 'labs') {
          setActiveTab('labs');
          setActiveLessonId('labs');
          effectiveLessonId = 'labs';
        } else if (lessonId === 'all') {
          setActiveLessonId('all');
          if (!preserveTab) setActiveTab('study');
          effectiveLessonId = 'all';
        } else if (lessonId) {
          const matched = Boolean(data.lessons && data.lessons.some((l) => l.id === lessonId));
          effectiveLessonId = matched ? lessonId : (data.active_lesson_id || 'all');
          setActiveLessonId(effectiveLessonId);
          if (!preserveTab) setActiveTab('study');
        } else {
          effectiveLessonId = data.active_lesson_id || 'all';
          setActiveLessonId(effectiveLessonId);
          if (!preserveTab) {
            setActiveTab('study');
          }
        }

        saveStoredSelection(query, effectiveLessonId);
      } else if (res.status !== 404 && currentRequestId === loadRequestIdRef.current) {
        notify('error', await failureMessage(res, 'Opening the topic'));
      }
      if (res.status === 404) {
        clearStoredSelection();
        if (currentRequestId === loadRequestIdRef.current) {
          setSelectedPath(null);
          setTopicDetails(null);
          setActiveLessonId(null);
        }
      }
    } catch (err) {
      console.error('Failed to load topic details:', err);
      if (currentRequestId === loadRequestIdRef.current) notify('error', networkFailure('Opening the topic', err));
    } finally {
      if (currentRequestId === loadRequestIdRef.current) {
        setIsLoadingTopic(false);
      }
    }
  };


  const handleLoginSuccess = async () => {
    setIsAuthenticated(true);
    window.dispatchEvent(new CustomEvent('synapse:authenticated'));
    await fetchTree();
    fetchStatus();

    if (!userInteractedRef.current) {
      const saved = getStoredSelection();
      if (saved && saved.path) {
        await loadTopic(saved.path, false, saved.lessonId, true);
      }
    }
  };

  const handleLogout = () => {
    loadRequestIdRef.current += 1;
    chatRequestIdRef.current += 1;
    activeCancelHandler.current?.();
    clearStoredSelection();
    localStorage.removeItem('synapse_auth_token');
    setIsAuthenticated(false);
    setSelectedPath(null);
    setTopicDetails(null);
    setActiveLessonId(null);
    userInteractedRef.current = false;
  };

  const handleCancelAI = () => {
    serverCancelRef.current?.();
    serverCancelRef.current = null;
    if (activeCancelHandler.current) {
      try {
        activeCancelHandler.current();
      } catch (e) {
        console.error('Error canceling AI task:', e);
      }
      activeCancelHandler.current = null;
    }
    setIsGenerating(false);
    setIsChatting(false);
    setIsLoadingQuiz(false);
  };

  const handleGenerate = async (query: string, force = false) => {
    const abortCtrl = new AbortController();
    // Opening another course only stops waiting here; the server finishes
    // the course in the background. Stop (handleCancelAI) also stops the server.
    const cancelThis = () => abortCtrl.abort();
    activeCancelHandler.current = cancelThis;
    serverCancelRef.current = () => {
      fetch('/api/generate/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      }).catch(() => {});
      notify('info', 'Generation stopped. The course was not changed.');
    };
    setIsGenerating(true);
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortCtrl.signal,
        body: JSON.stringify({ query, force }),
      });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        const summary = summarizeGeneration(data.results, data.skipped, force);
        notify(summary.kind, summary.text);
        activeCancelHandler.current = null;
        serverCancelRef.current = null;
        await loadTopic(query);
        await fetchTree();
        await fetchStatus();
      } else {
        notify('error', await failureMessage(res, 'Generating content'));
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Failed to generate topic content:', err);
        notify('error', networkFailure('Generating content', err));
      }
    } finally {
      if (activeCancelHandler.current === cancelThis) activeCancelHandler.current = null;
      serverCancelRef.current = null;
      setIsGenerating(false);
    }
  };

  const handleAddSubtopic = async (domain: string, category: string, subtopic: string, title?: string) => {
    try {
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
        return true;
      }
      notify('error', await failureMessage(res, 'Adding the topic'));
    } catch (err) {
      notify('error', networkFailure('Adding the topic', err));
    }
    return false;
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
          setActiveLessonId(null);
          clearStoredSelection();
        }
        await fetchTree();
        await fetchStatus();
      } else {
        notify('error', await failureMessage(res, 'Deleting the topic'));
      }
    } catch (err) {
      console.error('Failed to delete topic:', err);
      notify('error', networkFailure('Deleting the topic', err));
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
        return true;
      }
      notify('error', await failureMessage(res, 'Renaming the topic'));
    } catch (err) {
      console.error('Failed to rename topic:', err);
      notify('error', networkFailure('Renaming the topic', err));
    }
    return false;
  };

  const handleSelectSubtopic = (query: string, lessonId?: string, sectionTitle?: string) => {
    setTargetSection(sectionTitle || null);
    loadTopic(query, false, lessonId);
  };

  const handleSelectLesson = (lessonId: string) => {
    setTargetSection(null);
    if (selectedPath) {
      setActiveLessonId(lessonId);
      if (lessonId === 'labs') {
        setActiveTab('labs');
        saveStoredSelection(selectedPath, 'labs');
      } else {
        setActiveTab('study');
        loadTopic(selectedPath, true, lessonId);
      }
    }
  };

  // Latest handlers for effects that subscribe once (start-up, keyboard), so
  // they never call a stale copy. Refreshed after every render, before them.
  const latestActions = useRef({ fetchTree, loadTopic, handleSelectLesson });
  useEffect(() => {
    latestActions.current = { fetchTree, loadTopic, handleSelectLesson };
  });

  useEffect(() => {
    const initApp = async () => {
      await waitForBackend();
      const ok = await checkAuth();
      if (ok) {
        await latestActions.current.fetchTree();
        fetchStatus();

        if (!userInteractedRef.current) {
          const saved = getStoredSelection();
          if (saved && saved.path) {
            await latestActions.current.loadTopic(saved.path, false, saved.lessonId, true);
          }
        }
      }
    };
    initApp();

    const handleUnauthorized = () => {
      loadRequestIdRef.current += 1;
      setIsAuthenticated(false);
      setAuthRequired(true);
      setSelectedPath(null);
      setTopicDetails(null);
      setActiveLessonId(null);
      userInteractedRef.current = false;
    };
    window.addEventListener('synapse:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('synapse:unauthorized', handleUnauthorized);
  }, [checkAuth]);


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
      } else {
        notify('error', await failureMessage(res, 'Marking the lesson'));
      }
    } catch (err) {
      console.error('Failed to toggle lesson completion:', err);
      notify('error', networkFailure('Marking the lesson', err));
    }
  };

  const contentRef = useRef<HTMLDivElement>(null);

  // Global Ergonomic Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

      // A blocking dialog (first-run setup, login) owns the keyboard: don't
      // open search or other panels behind it.
      if (setupWizardOpen || (authRequired && !isAuthenticated)) return;

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

      // Do not trigger single-key or navigation shortcuts while actively typing in input/textarea or terminal
      const isTerminal = Boolean(target.closest('.terminal-drawer') || target.closest('.xterm') || target.closest('.terminal-body'));
      if (isTyping || isTerminal) return;

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

      // Lesson Navigation Shortcuts: [ and ]
      if (e.key === '[' || e.key === ']') {
        // Ignore if any modifier key (Ctrl, Cmd, Alt, Shift) is held
        if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;

        // In "labs", neither shortcut changes the view
        if (activeTab === 'labs') return;

        const lessons = topicDetails?.lessons || [];
        if (lessons.length === 0) return;

        // In "all lessons", ] opens the first lesson; [ does nothing
        if (!activeLessonId || activeLessonId === 'all') {
          if (e.key === ']') {
            e.preventDefault();
            latestActions.current.handleSelectLesson(lessons[0].id);
          }
          return;
        }

        // In an individual lesson, [ goes to previous and ] to next (without wrapping)
        const idx = lessons.findIndex((l) => l.id === activeLessonId);
        if (e.key === '[') {
          if (idx > 0) {
            e.preventDefault();
            latestActions.current.handleSelectLesson(lessons[idx - 1].id);
          }
          return;
        }
        if (e.key === ']') {
          if (idx >= 0 && idx < lessons.length - 1) {
            e.preventDefault();
            latestActions.current.handleSelectLesson(lessons[idx + 1].id);
          }
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [topicDetails, activeLessonId, activeTab, setupWizardOpen, authRequired, isAuthenticated]);

  const handleSendMessage = async (msg: string) => {
    const currentChatId = ++chatRequestIdRef.current;
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

      const abortCtrl = new AbortController();
      activeCancelHandler.current = () => abortCtrl.abort();

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortCtrl.signal,
        body: JSON.stringify({
          query: selectedPath || '',
          lesson_id: activeLessonId,
          lesson_title: lessonTitle,
          section_title: targetSection || undefined,
          message: msg,
          history: unifiedChatHistory,
          terminal_context: terminalOutput,
          last_terminal_command: lastTerminalCommand,
          lesson_content: lessonContent,
          language: settings.language,
          stream: true,
          model: settings.mentorModel || settings.primaryModel || undefined,
          host: settings.ollamaHost || undefined,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned ${res.status}`);
      }

      const answeringModel = res.headers.get('X-Synapse-Model');
      if (answeringModel && currentChatId === chatRequestIdRef.current) setMentorActiveModel(answeringModel);

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedReply = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done || currentChatId !== chatRequestIdRef.current) break;

          const textChunk = decoder.decode(value, { stream: true });
          const lines = textChunk.split('\n');

          for (const line of lines) {
            if (currentChatId !== chatRequestIdRef.current) break;
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
        if (currentChatId !== chatRequestIdRef.current) return;
        const data = await res.json();
        setUnifiedChatHistory([
          ...updatedHistory,
          { role: 'tutor', content: data.reply }
        ]);
      }
    } catch (err: any) {
      if (err.name === 'AbortError' || currentChatId !== chatRequestIdRef.current) {
        return;
      }
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
      if (currentChatId === chatRequestIdRef.current) {
        setIsChatting(false);
      }
    }
  };

  const handleNavigateBreadcrumb = (type: 'domain' | 'category' | 'subtopic', path: string) => {
    if (type === 'subtopic') {
      loadTopic(path);
      return;
    }

    for (const [domain, ddata] of Object.entries(tree)) {
      if (type === 'domain' && domain === path) {
        for (const discData of Object.values(ddata.disciplines || {})) {
          for (const cData of Object.values((discData as any).courses || {})) {
            const units = Object.values((cData as any).units || {});
            if (units.length > 0) {
              loadTopic((units[0] as any).rel_path);
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
                loadTopic((units[0] as any).rel_path);
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

    const abortCtrl = new AbortController();
    activeCancelHandler.current = () => abortCtrl.abort();

    const quizKey = selectedPath;
    setIsLoadingQuiz(true);
    try {
      const res = await fetch('/api/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortCtrl.signal,
        body: JSON.stringify({
          query: selectedPath,
          model: settings.mentorModel || settings.primaryModel || undefined,
          host: settings.ollamaHost || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuizQuestions((prev) => ({
          ...prev,
          [quizKey]: data.questions || [],
        }));
        if (!data.questions?.length) {
          notify('error', 'The AI model returned no quiz questions. Try again or pick another model in Settings.');
        }
      } else {
        notify('error', await failureMessage(res, 'Generating the quiz'));
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Failed to fetch quiz:', err);
        notify('error', networkFailure('Generating the quiz', err));
      }
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
        await fetchTree();
        await fetchStatus();
      } else {
        notify('error', await failureMessage(res, 'Updating mastery'));
      }
    } catch (err) {
      console.error('Failed to update mastery:', err);
      notify('error', networkFailure('Updating mastery', err));
    }
  };

  const saveBlob = (blob: Blob, filename: string) => {
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  };

  // Downloads go through fetch (which carries the Authorization header) rather
  // than window.open, so they work on password-protected instances.
  const downloadFile = async (url: string, fallbackName: string) => {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        notify('error', await failureMessage(res, 'Download'));
        return;
      }
      const disposition = res.headers.get('Content-Disposition') || '';
      const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
      const filename = match ? decodeURIComponent(match[1]) : fallbackName;
      saveBlob(await res.blob(), filename);
    } catch (err) {
      console.error('Download failed:', err);
      notify('error', networkFailure('Download', err));
    }
  };

  const handleDownloadFlashcards = () => {
    if (!selectedPath) return;
    void downloadFile(`/api/flashcards?query=${encodeURIComponent(selectedPath)}`, 'flashcards.csv');
  };

  const handleDownloadHandbook = () => {
    if (!topicDetails) return;
    void downloadFile(`/api/export?domain=${encodeURIComponent(topicDetails.domain)}`, `${topicDetails.domain}.md`);
  };

  const currentQuiz = selectedPath ? quizQuestions[selectedPath] || [] : [];

  const activeLessonTitle = useMemo(() => {
    if (!topicDetails) return null;
    if (activeTab === 'labs') return 'Operational Labs';
    if (activeLessonId && activeLessonId !== 'all' && topicDetails.lessons) {
      const cur = topicDetails.lessons.find((l) => l.id === activeLessonId);
      return cur?.title || topicDetails.active_lesson_title || 'Active Lesson';
    }
    return topicDetails.active_lesson_title || toTitleCase(topicDetails.display_title || topicDetails.subtopic || 'Complete Masterclass');
  }, [topicDetails, activeTab, activeLessonId]);

  const globalAITask = useMemo(() => {
    if (isGenerating) return 'Synthesizing Masterclass Curriculum Units';
    if (isChatting) return 'Socratic Mentor Generating Response';
    if (isLoadingQuiz) return 'Generating Socratic Scenario Quiz';
    return null;
  }, [isGenerating, isChatting, isLoadingQuiz]);

  const configuredMentorModel = settings.mentorModel || settings.primaryModel;
  // While connected, show the model that actually answers.
  const shownMentorModel = (mentorConnected === 'connected' && mentorActiveModel) || configuredMentorModel;
  const mentorFallback = Boolean(
    mentorConnected === 'connected' && mentorActiveModel && configuredMentorModel && mentorActiveModel !== configuredMentorModel
  );

  return (
    <div className="workbench-layout">
      <TopicTree
        tree={tree}
        treeLoaded={treeLoaded}
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
        onLogout={authRequired ? handleLogout : undefined}
        targetLanguage={settings.language}
        translationStatus={courseTranslations}
      />

      <div className="center-workspace-column">
        <LessonViewer
          topic={authRequired && !isAuthenticated ? null : topicDetails}
          contentRef={contentRef as React.RefObject<HTMLDivElement>}
          isLoading={isLoadingTopic}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
          onRunInTerminal={handleRunInTerminal}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          activeLessonId={activeLessonId}
          quizQuestions={currentQuiz}
          isLoadingQuiz={isLoadingQuiz}
          onRefreshQuiz={handleRefreshQuiz}
          onUpdateMastery={handleUpdateMastery}
          onDownloadFlashcards={handleDownloadFlashcards}
          onDownloadHandbook={handleDownloadHandbook}
          onOpenFlashcards={() => setFlashcardModalOpen(true)}
          targetLanguage={settings.language}
          preferredModel={settings.mentorModel || settings.primaryModel}
          ollamaHost={settings.ollamaHost}
          onNavigateBreadcrumb={handleNavigateBreadcrumb}
          onSelectLesson={handleSelectLesson}
          onToggleLessonCompletion={handleToggleLessonCompletion}
          targetSection={targetSection}
          preferredLang={readingLang}
          translationStatus={courseTranslations}
        />

        <div className="workbench-bottom-bar">
          <div className="bottom-bar-left">
            {globalAITask ? (
              <div className="ai-active-status">
                <Loader2 size={12} className="animate-spin text-accent" />
                <span className="ai-status-text">{globalAITask}...</span>
                <button
                  type="button"
                  className="ai-stop-btn"
                  onClick={handleCancelAI}
                  title="Stop AI inference and restore idle state"
                >
                  <Square size={9} className="fill-current" />
                  <span>Stop</span>
                </button>
              </div>
            ) : (
              <div className="ai-idle-status">
                <span className="idle-indicator-dot" />
                <span>Synapse Ready</span>
              </div>
            )}
            <TranslationQueueIndicator enabled={apiUnlocked} />
          </div>
        </div>

        <TerminalDrawer
          ref={terminalRef}
          isOpen={terminalOpen}
          onToggle={() => setTerminalOpen((prev: boolean) => !prev)}
        />
      </div>

      <TutorChat
        topic={topicDetails}
        activeLessonTitle={activeLessonTitle}
        history={unifiedChatHistory}
        isChatting={isChatting}
        onSendMessage={handleSendMessage}
        onClearChat={() => setUnifiedChatHistory([])}
        mentorConnected={mentorConnected}
        mentorModel={shownMentorModel}
        mentorFallback={mentorFallback}
        configuredMentorModel={configuredMentorModel}
        targetLanguage={settings.language}
        onDismissMessage={(idx) => setUnifiedChatHistory((prev) => prev.filter((_, i) => i !== idx))}
      />

      <SearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectTopic={handleSelectSubtopic}
      />

      <GraphModal
        isOpen={graphOpen}
        onClose={() => setGraphOpen(false)}
        onSelectTopic={(path) => loadTopic(path)}
      />

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => {
          setSettingsOpen(false);
          fetchTree();
          fetchStatus();
        }}
        settings={settings}
        onSaveSettings={handleSaveSettings}
        initialTab={settingsTab}
        onTreeChange={() => {
          fetchTree();
          fetchStatus();
        }}
        onLaunchSetupWizard={() => setSetupWizardOpen(true)}
        onChatsCleared={() => setUnifiedChatHistory([])}
      />

      <SetupWizardModal
        isOpen={setupWizardOpen && apiUnlocked}
        onClose={() => setSetupWizardOpen(false)}
        currentSettings={settings}
        onSaveSettings={handleSaveSettings}
      />

      <FlashcardStudyModal
        isOpen={flashcardModalOpen}
        onClose={() => setFlashcardModalOpen(false)}
        topicPath={selectedPath || ''}
        topicTitle={topicDetails ? toTitleCase(topicDetails.display_title || topicDetails.subtopic) : 'Flashcard Deck'}
      />

      <LoginModal
        isOpen={authRequired && !isAuthenticated}
        onLoginSuccess={handleLoginSuccess}
      />

      <NoticeStack notices={notices} onDismiss={dismissNotice} />
    </div>
  );
}

export default App;

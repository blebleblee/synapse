export interface SubtopicStatus {
  has_foundation?: boolean;
  has_lesson: boolean;
  has_labs: boolean;
  complete: boolean;
  file_count: number;
  files: string[];
}

export interface UnitNode {
  display_name: string;
  domain: string;
  discipline: string;
  course: string;
  course_title?: string;
  unit: string;
  rel_path: string;
  full_path: string;
  status: SubtopicStatus;
  lessons?: LessonItem[];
  completed_lessons?: string[];
  has_summary?: boolean;
}

export interface CourseNode {
  display_name?: string;
  units: { [unitSlug: string]: UnitNode };
}

export interface DisciplineNode {
  courses: { [courseSlug: string]: CourseNode };
}

export interface CategoryMap {
  [category: string]: {
    [subtopic: string]: UnitNode;
  };
}

export interface DomainNode {
  path: string;
  disciplines: { [discSlug: string]: DisciplineNode };
  categories: CategoryMap;
}

export interface TopicTreeData {
  [domain: string]: DomainNode;
}

export interface LessonItem {
  id: string;
  title: string;
  filename: string;
  content: string;
}

export interface TopicDetails {
  domain: string;
  domain_title?: string;
  category: string;
  discipline_title?: string;
  course_title?: string;
  subtopic: string;
  display_title?: string;
  path: string;
  persona: string;
  mastery?: string;
  completed_lessons?: string[];
  summary?: string;
  chat_history?: ChatMessage[];
  foundation?: string;
  lesson: string;
  lessons?: LessonItem[];
  active_lesson_id?: string;
  active_lesson_title?: string;
  labs: string;
  full_content?: string;
  has_content: boolean;
}

export interface ChatMessage {
  role: 'student' | 'tutor';
  content: string;
  timestamp?: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface ClusterHostStatus {
  online: boolean;
  models: string[];
  preferred_model?: string;
  error?: string;
}

export interface WorkspaceStatus {
  domains: number;
  disciplines?: number;
  courses?: number;
  categories: number;
  subtopics: number;
  with_foundation?: number;
  with_lesson?: number;
  with_labs?: number;
  complete?: number;
  complete_count?: number;
  ollama_available: boolean;
  available_models?: string[];
  ollama_models?: string[];
  cluster?: { [host: string]: ClusterHostStatus };
}

/** A lesson translation in the server's background queue (/api/translate/jobs). */
export interface TranslationJobInfo {
  id: string;
  status: 'queued' | 'running' | 'done' | 'failed' | 'stopped';
  target_lang: string;
  title: string;
  path?: string | null;
  lesson_id?: string | null;
  done: number;
  total: number;
  position?: number;
  model?: string | null;
  error?: string | null;
  fallback?: boolean;
  stopping?: boolean;
  cached?: boolean;
  translated?: string;
}

export interface SubtopicStatus {
  has_foundation: boolean;
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
  unit: string;
  rel_path: string;
  full_path: string;
  status: SubtopicStatus;
}

export interface CourseNode {
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
  category: string;
  subtopic: string;
  display_title?: string;
  path: string;
  persona: string;
  level: string;
  available_levels: string[];
  mastery?: string;
  summary?: string;
  chat_history?: ChatMessage[];
  foundation: string;
  lesson: string;
  lessons?: LessonItem[];
  active_lesson_id?: string;
  labs: string;
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

export interface WorkspaceStatus {
  domains: number;
  categories: number;
  subtopics: number;
  foundation_count: number;
  lesson_count: number;
  labs_count: number;
  complete_count: number;
  ollama_available: boolean;
  ollama_models: string[];
}

export interface SubtopicStatus {
  has_foundation: boolean;
  has_lesson: boolean;
  has_labs: boolean;
  complete: boolean;
  file_count: number;
  files: string[];
}

export interface SubtopicNode {
  display_name: string;
  rel_path: string;
  full_path: string;
  status: SubtopicStatus;
}

export interface CategoryMap {
  [category: string]: {
    [subtopic: string]: SubtopicNode;
  };
}

export interface DomainNode {
  path: string;
  categories: CategoryMap;
}

export interface TopicTreeData {
  [domain: string]: DomainNode;
}

export interface TopicDetails {
  domain: string;
  category: string;
  subtopic: string;
  path: string;
  persona: string;
  level: string;
  available_levels: string[];
  mastery?: string;
  summary?: string;
  chat_history?: ChatMessage[];
  foundation: string;
  lesson: string;
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

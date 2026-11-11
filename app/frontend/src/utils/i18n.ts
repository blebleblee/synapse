/**
 * Synapse Polyglot Internationalization (i18n) Engine
 * Fast instant local translation dictionary for UI chrome (tabs, buttons, tooltips).
 */

export type SupportedLanguage = 'en' | 'cs' | 'de' | 'es' | 'ru';

export interface UIStrings {
  summary: string;
  foundation: string;
  lesson: string;
  labs: string;
  quiz: string;
  guide: string;
  compiling: string;
  regen: string;
  search: string;
  settings: string;
  graph: string;
  newChat: string;
  send: string;
  askMentor: string;
  curriculumOrder: string;
  alphabetical: string;
  progress: string;
  filterTopics: string;
  expandAll: string;
  collapseAll: string;
  addTopic: string;
  reorderDomains: string;
  resetOrder: string;
  previousLesson: string;
  nextLesson: string;
  lessons: string;
  themeStudio: string;
  themeTitanium: string;
  themeMonokai: string;
  themeNordic: string;
  notStarted: string;
  inProgress: string;
  mastered: string;
}

export const TRANSLATIONS: Record<SupportedLanguage, UIStrings> = {
  en: {
    summary: 'Summary',
    foundation: 'Foundation',
    lesson: 'Lesson',
    labs: 'Labs',
    quiz: 'Quiz',
    guide: 'Guide',
    compiling: 'Compiling...',
    regen: 'Regen',
    search: 'Search Curriculum',
    settings: 'Settings',
    graph: 'Knowledge Graph',
    newChat: 'New Chat',
    send: 'Send',
    askMentor: 'Ask your Socratic Mentor...',
    curriculumOrder: 'Curriculum Order',
    alphabetical: 'Alphabetical',
    progress: 'Mastery Progress',
    filterTopics: 'Filter topics or disciplines...',
    expandAll: 'Expand All',
    collapseAll: 'Collapse All',
    addTopic: 'Add Topic',
    reorderDomains: 'Reorder Domains',
    resetOrder: 'Reset Order',
    previousLesson: 'Previous Lesson',
    nextLesson: 'Next Lesson',
    lessons: 'Lessons',
    themeStudio: 'Studio Dark',
    themeTitanium: 'Titanium Obsidian',
    themeMonokai: 'Monokai Pro',
    themeNordic: 'Nordic Slate',
    notStarted: 'Not Started',
    inProgress: 'In Progress',
    mastered: 'Mastered',
  },
  cs: {
    summary: 'Přehled',
    foundation: 'Základy',
    lesson: 'Lekce',
    labs: 'Laboratoř',
    quiz: 'Kvíz',
    guide: 'Průvodce',
    compiling: 'Generuji...',
    regen: 'Obnovit',
    search: 'Hledat v kurikulu',
    settings: 'Nastavení',
    graph: 'Znalostní graf',
    newChat: 'Nový chat',
    send: 'Odeslat',
    askMentor: 'Zeptejte se sokratovského mentora...',
    curriculumOrder: 'Výchozí pořadí',
    alphabetical: 'Podle abecedy',
    progress: 'Podle pokroku',
    filterTopics: 'Filtrovat témata či disciplíny...',
    expandAll: 'Rozbalit vše',
    collapseAll: 'Sbalit vše',
    addTopic: 'Přidat téma',
    reorderDomains: 'Změnit pořadí domén',
    resetOrder: 'Výchozí pořadí',
    previousLesson: 'Předchozí lekce',
    nextLesson: 'Následující lekce',
    lessons: 'Lekce',
    themeStudio: 'Studio Tmavý',
    themeTitanium: 'Titanový Obsidian',
    themeMonokai: 'Monokai Pro',
    themeNordic: 'Severská břidlice',
    notStarted: 'Nezahájeno',
    inProgress: 'Rozpracováno',
    mastered: 'Zvládnuto',
  },
  de: {
    summary: 'Übersicht',
    foundation: 'Grundlagen',
    lesson: 'Lektion',
    labs: 'Labor',
    quiz: 'Quiz',
    guide: 'Leitfaden',
    compiling: 'Kompilieren...',
    regen: 'Neu generieren',
    search: 'Lehrplan durchsuchen',
    settings: 'Einstellungen',
    graph: 'Wissensgraph',
    newChat: 'Neuer Chat',
    send: 'Senden',
    askMentor: 'Fragen Sie Ihren Mentor...',
    curriculumOrder: 'Lehrplan-Reihenfolge',
    alphabetical: 'Alphabetisch',
    progress: 'Fortschritt',
    filterTopics: 'Themen filtern...',
    expandAll: 'Alle erweitern',
    collapseAll: 'Alle reduzieren',
    addTopic: 'Thema hinzufügen',
    reorderDomains: 'Bereiche anordnen',
    resetOrder: 'Zurücksetzen',
    previousLesson: 'Vorherige Lektion',
    nextLesson: 'Nächste Lektion',
    lessons: 'Lektionen',
    themeStudio: 'Studio Dunkel',
    themeTitanium: 'Titan Obsidian',
    themeMonokai: 'Monokai Pro',
    themeNordic: 'Nordisches Schiefer',
    notStarted: 'Nicht begonnen',
    inProgress: 'In Bearbeitung',
    mastered: 'Gemeistert',
  },
  es: {
    summary: 'Resumen',
    foundation: 'Fundamentos',
    lesson: 'Lección',
    labs: 'Laboratorio',
    quiz: 'Cuestionario',
    guide: 'Guía',
    compiling: 'Compilando...',
    regen: 'Regenerar',
    search: 'Buscar en currículo',
    settings: 'Ajustes',
    graph: 'Grafo de conocimiento',
    newChat: 'Nuevo chat',
    send: 'Enviar',
    askMentor: 'Pregunta a tu mentor...',
    curriculumOrder: 'Orden curricular',
    alphabetical: 'Alfabético',
    progress: 'Progreso',
    filterTopics: 'Filtrar temas...',
    expandAll: 'Expandir todo',
    collapseAll: 'Contraer todo',
    addTopic: 'Añadir tema',
    reorderDomains: 'Reordenar dominios',
    resetOrder: 'Restablecer orden',
    previousLesson: 'Lección anterior',
    nextLesson: 'Siguiente lección',
    lessons: 'Lecciones',
    themeStudio: 'Estudio Oscuro',
    themeTitanium: 'Obsidiana Titanio',
    themeMonokai: 'Monokai Pro',
    themeNordic: 'Pizarra Nórdica',
    notStarted: 'No iniciado',
    inProgress: 'En progreso',
    mastered: 'Dominado',
  },
  ru: {
    summary: 'Обзор',
    foundation: 'Основы',
    lesson: 'Урок',
    labs: 'Практикум',
    quiz: 'Тест',
    guide: 'Руководство',
    compiling: 'Компиляция...',
    regen: 'Обновить',
    search: 'Поиск по программе',
    settings: 'Настройки',
    graph: 'Граф знаний',
    newChat: 'Новый диалог',
    send: 'Отправить',
    askMentor: 'Задайте вопрос наставнику...',
    curriculumOrder: 'Порядок программы',
    alphabetical: 'По алфавиту',
    progress: 'По прогрессу',
    filterTopics: 'Фильтр по темам...',
    expandAll: 'Развернуть все',
    collapseAll: 'Свернуть все',
    addTopic: 'Добавить тему',
    reorderDomains: 'Изменить порядок',
    resetOrder: 'Сбросить порядок',
    previousLesson: 'Предыдущий урок',
    nextLesson: 'Следующий урок',
    lessons: 'Уроки',
    themeStudio: 'Студия Тёмная',
    themeTitanium: 'Титановый Обсидиан',
    themeMonokai: 'Монокай Про',
    themeNordic: 'Скандинавский сланец',
    notStarted: 'Не начато',
    inProgress: 'В процессе',
    mastered: 'Освоено',
  },
};

export function getUIStrings(lang?: string): UIStrings {
  const code = (lang || 'en').toLowerCase() as SupportedLanguage;
  return TRANSLATIONS[code] || TRANSLATIONS.en;
}

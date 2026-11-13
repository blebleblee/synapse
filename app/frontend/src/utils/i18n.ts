/**
 * Synapse Polyglot Internationalization (i18n) Engine
 * Fast instant local translation dictionary for UI chrome (tabs, buttons, tooltips).
 */

export type SupportedLanguage = 'en' | 'cs' | 'de' | 'es' | 'ru';

export interface UIStrings {
  study: string;
  completeGuide: string;
  fullCourse: string;
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
  // Extended UI Keys
  mentorTitle: string;
  mentorDirectives: string;
  mentorPlaceholder: string;
  clearChat: string;
  chipExplain: string;
  chipExample: string;
  chipPitfall: string;
  terminal: string;
  terminalConnected: string;
  mentorOnline: string;
  mentorConnecting: string;
  mentorOffline: string;
  emptyTitle: string;
  emptyDesc: string;
  searchPlaceholder: string;
  noResults: string;
  audio: string;
  export: string;
  regenerate: string;
  mastery: string;
  terminalTitle: string;
  terminalClose: string;
  allModules: string;
  searchTopics: string;
  knowledgeGraph: string;
}

export const TRANSLATIONS: Record<SupportedLanguage, UIStrings> = {
  en: {
    study: 'Study',
    completeGuide: 'Complete Guide',
    fullCourse: 'Full Course',
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
    mentorTitle: 'AI Socratic Mentor',
    mentorDirectives: 'Socratic Directives',
    mentorPlaceholder: 'Ask a question about this lesson or troubleshooting...',
    clearChat: 'Clear conversation',
    chipExplain: 'Explain',
    chipExample: 'Example',
    chipPitfall: 'Pitfall',
    terminal: 'Terminal',
    terminalConnected: 'Terminal Connected',
    mentorOnline: 'Mentor Online',
    mentorConnecting: 'Connecting...',
    mentorOffline: 'Mentor Offline',
    emptyTitle: 'Select a Topic to Begin',
    emptyDesc: 'Choose a subject from the curriculum tree on the left to explore in-depth lessons, practice with hands-on terminal labs, or consult the Socratic mentor.',
    searchPlaceholder: 'Search all topics, lessons, code & formulas (⌘K)...',
    noResults: 'No topics or lessons match your search',
    audio: 'Listen',
    export: 'Export',
    regenerate: 'Regenerate',
    mastery: 'Mastery',
    terminalTitle: 'Terminal Console',
    terminalClose: 'Close Terminal',
    allModules: 'Complete Guide',
    searchTopics: 'Search topics (⌘K)...',
    knowledgeGraph: 'Knowledge Graph',
  },
  cs: {
    study: 'Studium',
    completeGuide: 'Kompletní průvodce',
    fullCourse: 'Kompletní kurz',
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
    mentorTitle: 'AI Sokratovský Mentor',
    mentorDirectives: 'Direktivy mentora',
    mentorPlaceholder: 'Zeptejte se na tuto lekci nebo řešení problému...',
    clearChat: 'Vymazat konverzaci',
    chipExplain: 'Vysvětlit',
    chipExample: 'Příklad',
    chipPitfall: 'Úskalí',
    terminal: 'Terminál',
    terminalConnected: 'Terminál připojen',
    mentorOnline: 'Mentor online',
    mentorConnecting: 'Připojování...',
    mentorOffline: 'Mentor offline',
    emptyTitle: 'Vyberte téma pro zahájení',
    emptyDesc: 'Vyberte předmět ze stromu kurikula vlevo pro studium podrobných lekcí, procvičování v terminálu nebo konzultaci se sokratovským mentorem.',
    searchPlaceholder: 'Hledat témata, lekce, kód a vzorce (⌘K)...',
    noResults: 'Žádná témata ani lekce neodpovídají dotazu',
    audio: 'Poslech',
    export: 'Export',
    regenerate: 'Přegenerovat',
    mastery: 'Osvojení',
    terminalTitle: 'Terminálová konzole',
    terminalClose: 'Zavřít terminál',
    allModules: 'Kompletní průvodce',
    searchTopics: 'Hledat témata (⌘K)...',
    knowledgeGraph: 'Znalostní graf',
  },
  de: {
    study: 'Lernen',
    completeGuide: 'Gesamtübersicht',
    fullCourse: 'Gesamtkurs',
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
    mentorTitle: 'KI Sokrates-Mentor',
    mentorDirectives: 'Sokratische Richtlinien',
    mentorPlaceholder: 'Stellen Sie eine Frage zu dieser Lektion oder Fehlerbehebung...',
    clearChat: 'Gespräch löschen',
    chipExplain: 'Erklären',
    chipExample: 'Beispiel',
    chipPitfall: 'Fallstricke',
    terminal: 'Terminal',
    terminalConnected: 'Terminal verbunden',
    mentorOnline: 'Mentor online',
    mentorConnecting: 'Verbinde...',
    mentorOffline: 'Mentor offline',
    emptyTitle: 'Wählen Sie ein Thema',
    emptyDesc: 'Wählen Sie links ein Thema aus dem Lehrplanbaum, um Lektionen zu studieren, im Terminal zu üben oder den Mentor zu befragen.',
    searchPlaceholder: 'Themen, Lektionen, Code & Formeln durchsuchen (⌘K)...',
    noResults: 'Keine passenden Themen gefunden',
    audio: 'Anhören',
    export: 'Exportieren',
    regenerate: 'Neu generieren',
    mastery: 'Beherrschung',
    terminalTitle: 'Terminal-Konsole',
    terminalClose: 'Terminal schließen',
    allModules: 'Vollständiger Leitfaden',
    searchTopics: 'Themen suchen (⌘K)...',
    knowledgeGraph: 'Wissensgraph',
  },
  es: {
    study: 'Estudio',
    completeGuide: 'Guía Completa',
    fullCourse: 'Curso Completo',
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
    mentorTitle: 'Mentor Socrático IA',
    mentorDirectives: 'Directivas Socráticas',
    mentorPlaceholder: 'Haga una pregunta sobre esta lección o resolución de problemas...',
    clearChat: 'Borrar conversación',
    chipExplain: 'Explicar',
    chipExample: 'Ejemplo',
    chipPitfall: 'Dificultades',
    terminal: 'Terminal',
    terminalConnected: 'Terminal conectado',
    mentorOnline: 'Mentor conectado',
    mentorConnecting: 'Conectando...',
    mentorOffline: 'Mentor desconectado',
    emptyTitle: 'Seleccione un tema para comenzar',
    emptyDesc: 'Elija un tema del árbol curricular a la izquierda para explorar lecciones en profundidad, practicar en el terminal o consultar con el mentor.',
    searchPlaceholder: 'Buscar temas, lecciones, código y fórmulas (⌘K)...',
    noResults: 'No se encontraron temas coincidentes',
    audio: 'Escuchar',
    export: 'Exportar',
    regenerate: 'Regenerar',
    mastery: 'Dominio',
    terminalTitle: 'Consola de terminal',
    terminalClose: 'Cerrar terminal',
    allModules: 'Guía completa',
    searchTopics: 'Buscar temas (⌘K)...',
    knowledgeGraph: 'Grafo de conocimiento',
  },
  ru: {
    study: 'Обучение',
    completeGuide: 'Полное руководство',
    fullCourse: 'Полный курс',
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
    mentorTitle: 'ИИ Сократический Ментор',
    mentorDirectives: 'Сократические директивы',
    mentorPlaceholder: 'Задайте вопрос по этому уроку или устранению неполадок...',
    clearChat: 'Очистить беседу',
    chipExplain: 'Объяснить',
    chipExample: 'Пример',
    chipPitfall: 'Подводные камни',
    terminal: 'Терминал',
    terminalConnected: 'Терминал подключен',
    mentorOnline: 'Ментор онлайн',
    mentorConnecting: 'Подключение...',
    mentorOffline: 'Ментор офлайн',
    emptyTitle: 'Выберите тему для начала',
    emptyDesc: 'Выберите предмет из дерева программы слева, чтобы изучить подробные уроки, попрактиковаться в терминале или проконсультироваться с наставником.',
    searchPlaceholder: 'Поиск тем, уроков, кода и формул (⌘K)...',
    noResults: 'Совпадений не найдено',
    audio: 'Аудио',
    export: 'Экспорт',
    regenerate: 'Перегенерировать',
    mastery: 'Мастерство',
    terminalTitle: 'Консоль терминала',
    terminalClose: 'Закрыть терминал',
    allModules: 'Полное руководство',
    searchTopics: 'Поиск тем (⌘K)...',
    knowledgeGraph: 'Граф знаний',
  },
};

export function getUIStrings(lang?: string): UIStrings {
  const code = (lang || 'en').toLowerCase() as SupportedLanguage;
  return TRANSLATIONS[code] || TRANSLATIONS.en;
}

import React, { useState, useMemo } from 'react';
import { toTitleCase, cleanLessonTitle } from '../utils/text';
import {
  Folder,
  FolderOpen,
  Search,
  Plus,
  GitBranch,
  BookOpen,
  Terminal,
  Wrench,
  Gauge,
  Hammer,
  Binary,
  FlaskConical,
  Palette,
  Languages,
  Briefcase,
  TrendingUp,
  ArrowDownAZ,
  Settings,
  Package,
  ChevronsDownUp,
  ChevronsUpDown,
  Edit2,
  Trash2,
  X,
  Activity,
  Check,
  Zap,
  LogOut
} from 'lucide-react';
import type { TopicTreeData, UnitNode, WorkspaceStatus } from '../types';

interface TopicTreeProps {
  tree: TopicTreeData;
  /** False until the first tree response; an empty tree before then is not "nothing installed". */
  treeLoaded?: boolean;
  selectedSubtopic: string | null;
  activeLessonId?: string | null;
  activeTab?: string;
  status?: WorkspaceStatus | null;
  completedLessons?: string[];
  onSelectSubtopic: (query: string, lessonId?: string) => void;
  /** Resolves false when adding failed (the app has already shown why). */
  onAddSubtopic: (domain: string, category: string, subtopic: string, title?: string) => Promise<boolean | void>;
  onOpenSearch: () => void;
  onOpenGraph: () => void;
  onOpenSettings: () => void;
  onOpenStore?: () => void;
  onLogout?: () => void;
  onDeleteTopic?: (path: string) => Promise<void>;
  onRenameTopic?: (path: string, newTitle: string) => Promise<boolean | void>;
  onToggleLessonCompletion?: (path: string, lessonId: string, completed?: boolean) => Promise<void>;
  targetLanguage?: string;
}

import { getUIStrings } from '../utils/i18n';

export const TopicTree: React.FC<TopicTreeProps> = ({
  tree,
  treeLoaded = true,
  selectedSubtopic,
  activeLessonId,
  activeTab,
  status,
  completedLessons,
  onSelectSubtopic,
  onAddSubtopic,
  onOpenSearch,
  onOpenGraph,
  onOpenSettings,
  onOpenStore,
  onLogout,
  onDeleteTopic,
  onRenameTopic,
  onToggleLessonCompletion,
  targetLanguage,
}) => {
  const ui = getUIStrings(targetLanguage);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortMode, setSortMode] = useState<'az' | 'progress'>('az');
  const [openUnits, setOpenUnits] = useState<{ [key: string]: boolean }>({});

  const toggleUnit = (unitPath: string) => {
    setOpenUnits((prev) => ({ ...prev, [unitPath]: !prev[unitPath] }));
  };

  const [openDomains, setOpenDomains] = useState<{ [key: string]: boolean }>({});
  const [openDisciplines, setOpenDisciplines] = useState<{ [key: string]: boolean }>({});
  const [openCourses, setOpenCourses] = useState<{ [key: string]: boolean }>({});
  const [allExpanded, setAllExpanded] = useState(false);

  // Add Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [addDomain, setAddDomain] = useState('computing');
  const [addDiscipline, setAddDiscipline] = useState('infrastructure');
  const [addCourse, setAddCourse] = useState('');
  const [addUnitSlug, setAddUnitSlug] = useState('');
  const [addTitle, setAddTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Rename Modal State
  const [renameTarget, setRenameTarget] = useState<{ path: string; currentTitle: string } | null>(null);
  const [renameInput, setRenameInput] = useState('');

  const toggleAll = () => {
    if (allExpanded) {
      setOpenDomains({});
      setOpenDisciplines({});
      setOpenCourses({});
      setAllExpanded(false);
    } else {
      const nextDomains: { [k: string]: boolean } = {};
      const nextDiscs: { [k: string]: boolean } = {};
      const nextCourses: { [k: string]: boolean } = {};
      for (const [d, ddata] of Object.entries(tree)) {
        nextDomains[d] = true;
        for (const [disc, discData] of Object.entries(ddata.disciplines || {})) {
          const discKey = `${d}/${disc}`;
          nextDiscs[discKey] = true;
          for (const courseSlug of Object.keys(discData.courses || {})) {
            nextCourses[`${discKey}/${courseSlug}`] = true;
          }
        }
      }
      setOpenDomains(nextDomains);
      setOpenDisciplines(nextDiscs);
      setOpenCourses(nextCourses);
      setAllExpanded(true);
    }
  };

  const toggleDomain = (domain: string) => {
    setOpenDomains((prev) => ({ ...prev, [domain]: !prev[domain] }));
  };

  const toggleDiscipline = (discKey: string) => {
    setOpenDisciplines((prev) => ({ ...prev, [discKey]: !prev[discKey] }));
  };

  const toggleCourse = (courseKey: string) => {
    setOpenCourses((prev) => ({ ...prev, [courseKey]: !prev[courseKey] }));
  };

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'computing':
        return <Terminal size={16} className="domain-icon" />;
      case 'engineering':
        return <Wrench size={16} className="domain-icon" />;
      case 'motorsports':
        return <Gauge size={16} className="domain-icon" />;
      case 'crafts':
        return <Hammer size={16} className="domain-icon" />;
      case 'formal_sciences':
        return <Binary size={16} className="domain-icon" />;
      case 'natural_sciences':
        return <FlaskConical size={16} className="domain-icon" />;
      case 'health_sciences':
        return <Activity size={16} className="domain-icon" />;
      case 'arts':
        return <Palette size={16} className="domain-icon" />;
      case 'languages':
        return <Languages size={16} className="domain-icon" />;
      case 'humanities':
        return <BookOpen size={16} className="domain-icon" />;
      case 'business':
        return <Briefcase size={16} className="domain-icon" />;
      case 'economics':
        return <TrendingUp size={16} className="domain-icon" />;
      default:
        return <Folder size={16} className="domain-icon" />;
    }
  };

  const handleCreateTopic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addCourse.trim() || !addDiscipline.trim()) return;

    setIsSubmitting(true);
    try {
      const disc = addDiscipline.trim();
      const course = addCourse.trim().replace(/\s+/g, '_');
      const unit = addUnitSlug.trim() ? addUnitSlug.trim().replace(/\s+/g, '_') : '01_fundamentals';
      const categoryPath = `${disc}/${course}`;
      const title = addTitle.trim() || undefined;

      const added = await onAddSubtopic(addDomain, categoryPath, unit, title);
      if (added === false) return; // keep the dialog open so nothing typed is lost
      setShowAddModal(false);
      setAddCourse('');
      setAddUnitSlug('');
      setAddTitle('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameTarget || !renameInput.trim() || !onRenameTopic) return;
    try {
      const renamed = await onRenameTopic(renameTarget.path, renameInput.trim());
      if (renamed === false) return;
      setRenameTarget(null);
      setRenameInput('');
    } catch (err) {
      console.error(err);
    }
  };

  // Helper to count completed units in a domain
  const getDomainCompletion = (ddata: any) => {
    let completed = 0;
    let total = 0;
    const discs = ddata.disciplines || {};
    for (const discData of Object.values(discs) as any[]) {
      for (const cData of Object.values(discData.courses || {}) as any[]) {
        for (const uData of Object.values(cData.units || {}) as any[]) {
          total += 1;
          if (uData.status?.complete) completed += 1;
        }
      }
    }
    return { completed, total, rate: total > 0 ? completed / total : 0 };
  };

  const sortedDomainEntries = useMemo(() => {
    return Object.entries(tree).sort(([a, ddataA], [b, ddataB]) => {
      if (sortMode === 'progress') {
        const rateA = getDomainCompletion(ddataA).rate;
        const rateB = getDomainCompletion(ddataB).rate;
        return rateB - rateA;
      }
      return a.localeCompare(b);
    });
  }, [tree, sortMode]);

  const toggleSortMode = () => {
    setSortMode((prev) => (prev === 'az' ? 'progress' : 'az'));
  };

  const cleanTerm = searchTerm.trim().toLowerCase();

  return (
    <aside className="tree-sidebar">
      {/* 1. Industry-Standard Workspace Brand Bar (52px height) */}
      <div className="sidebar-header">
        <div className="brand">
          <svg className="brand-logo-svg" viewBox="0 0 48 48" width="24" height="24" fill="none">
            <circle cx="24" cy="24" r="20" stroke="#4f8fff" strokeWidth="2" strokeDasharray="4 2" opacity="0.6"/>
            <polygon points="24,8 38,16 38,32 24,40 10,32 10,16" stroke="#fbbf24" strokeWidth="2.5" fill="#15181f" />
            <line x1="24" y1="8" x2="24" y2="24" stroke="#4f8fff" strokeWidth="2" />
            <line x1="38" y1="16" x2="24" y2="24" stroke="#fbbf24" strokeWidth="2" />
            <line x1="38" y1="32" x2="24" y2="24" stroke="#10b981" strokeWidth="2" />
            <line x1="24" y1="40" x2="24" y2="24" stroke="#10b981" strokeWidth="2" />
            <line x1="10" y1="32" x2="24" y2="24" stroke="#4f8fff" strokeWidth="2" />
            <line x1="10" y1="16" x2="24" y2="24" stroke="#fbbf24" strokeWidth="2" />
            <circle cx="24" cy="24" r="5" fill="#10b981" />
            <circle cx="24" cy="24" r="2.5" fill="#ffffff"/>
          </svg>
          <span className="brand-title">Synapse</span>
        </div>

        <div className="sidebar-header-actions">
          {onLogout && (
            <button className="icon-btn" onClick={onLogout} title="Lock / Logout">
              <LogOut size={14} />
            </button>
          )}
          <button className="icon-btn" onClick={onOpenStore || onOpenSettings} title="Curriculum Store & Addons">
            <Package size={14} />
          </button>
          <button className="icon-btn" onClick={onOpenSettings} title={ui.settings}>
            <Settings size={14} />
          </button>
          <button
            className="btn-primary-sm"
            onClick={() => setShowAddModal(true)}
            title={ui.addTopic}
          >
            <Plus size={14} />
          </button>
        </div>
      </div>

      {/* 2. Unified Search & View Controls Bar */}
      <div className="search-filter-row">
        <div className="search-box">
          <Search size={13} className="search-icon" />
          <input
            type="text"
            placeholder={ui.filterTopics}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm.length > 0 ? (
            <button
              type="button"
              className="search-clear-btn"
              onClick={() => setSearchTerm('')}
              title="Clear filter text"
            >
              <X size={12} />
            </button>
          ) : null}
        </div>

        <button
          type="button"
          className="icon-btn-sm"
          onClick={onOpenSearch}
          title={`${ui.search} (Cmd+K)`}
        >
          <Search size={13} />
        </button>

        <button
          type="button"
          className="icon-btn-sm"
          onClick={onOpenGraph}
          title={ui.graph}
        >
          <GitBranch size={13} />
        </button>

        <button
          type="button"
          className="icon-btn-sm"
          onClick={toggleAll}
          title={allExpanded ? ui.collapseAll : ui.expandAll}
        >
          {allExpanded ? <ChevronsDownUp size={13} /> : <ChevronsUpDown size={13} />}
        </button>

        <button
          type="button"
          className={`icon-btn-sm sort-toggle-btn ${sortMode === 'progress' ? 'active' : ''}`}
          onClick={toggleSortMode}
          title={sortMode === 'az' ? 'Sort: Alphabetical (Click to sort by % Completion)' : 'Sort: % Completion (Click to sort A-Z)'}
          aria-label="Toggle domain sort mode"
        >
          {sortMode === 'az' ? <ArrowDownAZ size={13} /> : <TrendingUp size={13} />}
        </button>
      </div>

      <div className="tree-content">
        {!treeLoaded && sortedDomainEntries.length === 0 ? (
          <div className="empty-tree-state" style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            Loading curriculum…
          </div>
        ) : sortedDomainEntries.length === 0 ? (
          <div className="empty-tree-state" style={{ padding: '32px 16px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Package size={32} style={{ opacity: 0.4, color: 'var(--text-muted)' }} />
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>No Curriculum Installed Yet</div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5', margin: 0 }}>
              Synapse runs as a modular app shell. Sideload a <code>.synpack</code> addon or install topics from the Store.
            </p>
            <button
              className="btn-primary"
              style={{ fontSize: '11px', padding: '6px 12px', display: 'inline-flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}
              onClick={onOpenStore || onOpenSettings}
            >
              <Package size={13} />
              Open Curriculum Store
            </button>
          </div>
        ) : (
          sortedDomainEntries.map(([domain, ddata]) => {
          const disciplines = ddata.disciplines || {};

          let sortedDisciplines = Object.entries(disciplines);
          if (sortMode === 'az') {
            sortedDisciplines.sort(([a], [b]) => a.localeCompare(b));
          }

          const domainMatches = cleanTerm === '' || domain.toLowerCase().includes(cleanTerm);

          const matchingDisciplines = sortedDisciplines.filter(([disc, discData]) => {
            if (cleanTerm === '' || domainMatches || disc.toLowerCase().includes(cleanTerm)) return true;
            const courses = discData.courses || {};
            return Object.entries(courses).some(([courseSlug, cData]: [string, any]) => {
              if (courseSlug.toLowerCase().includes(cleanTerm)) return true;
              const units = Object.values(cData.units || {}) as UnitNode[];
              return units.some((u) =>
                u.display_name.toLowerCase().includes(cleanTerm) ||
                u.rel_path.toLowerCase().includes(cleanTerm)
              );
            });
          });

          if (cleanTerm !== '' && matchingDisciplines.length === 0) {
            return null;
          }

          const isDomainOpen = openDomains[domain] || cleanTerm.length > 0;

          return (
            <div key={domain} className="domain-group">
              <div
                className="domain-header"
                onClick={() => toggleDomain(domain)}
              >
                {getDomainIcon(domain)}
                <span className="domain-label">
                  {toTitleCase(domain)}
                </span>
              </div>

              {isDomainOpen && (
                <div className="domain-categories">
                  {matchingDisciplines.map(([disc, discData]) => {
                    const discKey = `${domain}/${disc}`;
                    const courses = discData.courses || {};

                    let sortedCourses = Object.entries(courses);
                    if (sortMode === 'az') {
                      sortedCourses.sort(([a], [b]) => a.localeCompare(b));
                    } else if (sortMode === 'progress') {
                      sortedCourses.sort(([, cDataA], [, cDataB]) => {
                        const unitsA = Object.values(cDataA.units || {});
                        const unitsB = Object.values(cDataB.units || {});
                        const compA = unitsA.filter((u: any) => u.status?.complete).length;
                        const compB = unitsB.filter((u: any) => u.status?.complete).length;
                        return compB - compA;
                      });
                    }

                    const discMatches = cleanTerm === '' || domainMatches || disc.toLowerCase().includes(cleanTerm);

                    const matchingCourses = sortedCourses.filter(([courseSlug, cData]) => {
                      if (cleanTerm === '' || discMatches || courseSlug.toLowerCase().includes(cleanTerm)) return true;
                      const units = Object.values(cData.units || {}) as UnitNode[];
                      return units.some((u) =>
                        u.display_name.toLowerCase().includes(cleanTerm) ||
                        u.rel_path.toLowerCase().includes(cleanTerm)
                      );
                    });

                    if (cleanTerm !== '' && matchingCourses.length === 0) {
                      return null;
                    }

                    const isDiscOpen = openDisciplines[discKey] || cleanTerm.length > 0;

                    return (
                      <div key={discKey} className="category-group">
                        <div
                          className="category-header"
                          onClick={() => toggleDiscipline(discKey)}
                        >
                          <FolderOpen size={14} className="category-icon" />
                          <span className="category-label">
                            {toTitleCase(disc)}
                          </span>
                          <span className="category-count">{Object.keys(courses).length}</span>
                        </div>

                        {isDiscOpen && (
                          <div className="subtopic-list">
                            {matchingCourses.map(([courseSlug, cData]) => {
                              const courseKey = `${discKey}/${courseSlug}`;
                              let units = Object.values(cData.units || {}) as UnitNode[];

                              if (sortMode === 'az') {
                                units = [...units].sort((a, b) => a.display_name.localeCompare(b.display_name));
                              }

                              const courseMatches = cleanTerm === '' || discMatches || courseSlug.toLowerCase().includes(cleanTerm);

                              const matchingUnits = units.filter((u) =>
                                courseMatches ||
                                u.display_name.toLowerCase().includes(cleanTerm) ||
                                u.rel_path.toLowerCase().includes(cleanTerm)
                              );

                              if (cleanTerm !== '' && matchingUnits.length === 0) {
                                return null;
                              }

                              if (units.length === 1 && units[0].unit === 'core') {
                                const singleUnit = units[0];
                                const isSelected = selectedSubtopic === singleUnit.rel_path;
                                const hasMultiLessons = Boolean(singleUnit.lessons && singleUnit.lessons.length >= 1);
                                const isUnitOpen = openUnits[singleUnit.rel_path] ?? isSelected;
                                const unitTitle = toTitleCase(singleUnit.display_name);

                                const unitCompletedLessons = isSelected && completedLessons ? completedLessons : (singleUnit.completed_lessons || []);
                                const validLessonIds = new Set((singleUnit.lessons || []).map((l: any) => l.id));
                                const completedCount = unitCompletedLessons.filter((id: string) => validLessonIds.has(id)).length;
                                const totalLessons = singleUnit.lessons ? singleUnit.lessons.length : 0;
                                const isAllCompleted = totalLessons > 0 && completedCount >= totalLessons;

                                return (
                                  <div key={courseKey} className="course-group">
                                    <div className="unit-container">
                                      <div
                                        className={`${hasMultiLessons ? 'course-header has-subsections' : 'subtopic-item'} ${isSelected ? 'selected' : ''}`}
                                        onClick={() => {
                                          if (hasMultiLessons) {
                                            toggleUnit(singleUnit.rel_path);
                                          }
                                          onSelectSubtopic(singleUnit.rel_path, hasMultiLessons ? 'all' : undefined);
                                        }}
                                      >
                                        {hasMultiLessons && <BookOpen size={13} className="course-icon" />}
                                        <span className={hasMultiLessons ? "course-title" : "subtopic-title"} title={unitTitle}>
                                          {unitTitle}
                                        </span>
                                        <div className={hasMultiLessons ? "course-meta" : "item-meta"}>
                                          {hasMultiLessons && (
                                            <span
                                              className={`course-progress ${isAllCompleted ? 'all-completed' : completedCount > 0 ? 'has-progress' : ''}`}
                                              title={`${completedCount} of ${totalLessons} lessons completed`}
                                            >
                                              {completedCount > 0 ? `${completedCount}/${totalLessons}` : `${totalLessons}L`}
                                              {isAllCompleted && ' ✓'}
                                            </span>
                                          )}
                                          <div className="item-actions" onClick={(e) => e.stopPropagation()}>
                                            {onRenameTopic && (
                                              <button
                                                className="action-mini-btn"
                                                onClick={() => {
                                                  setRenameTarget({ path: singleUnit.rel_path, currentTitle: unitTitle });
                                                  setRenameInput(unitTitle);
                                                }}
                                                title="Rename unit"
                                              >
                                                <Edit2 size={11} />
                                              </button>
                                            )}
                                            {onDeleteTopic && (
                                              <button
                                                className="action-mini-btn delete"
                                                onClick={() => onDeleteTopic(singleUnit.rel_path)}
                                                title="Delete unit"
                                              >
                                                <Trash2 size={11} />
                                              </button>
                                            )}
                                          </div>
                                        </div>
                                      </div>

                                      {/* Sub-lessons list nested directly under the topic */}
                                      {isUnitOpen && hasMultiLessons && singleUnit.lessons && (
                                        <div className="unit-lessons-sublist">
                                          <div
                                            className={`unit-lesson-subitem ${isSelected && (!activeLessonId || activeLessonId === 'all') ? 'active' : ''}`}
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              onSelectSubtopic(singleUnit.rel_path, 'all');
                                            }}
                                            title="Complete Guide (All modules in full)"
                                          >
                                            <BookOpen size={11} className="sublesson-icon" />
                                            <span className="sublesson-title">Complete Guide</span>
                                          </div>

                                          {singleUnit.lessons.map((lesson, lIdx) => {
                                            const isLessonActive = isSelected && activeLessonId === lesson.id;
                                            const isCompleted = unitCompletedLessons.includes(lesson.id);
                                            const displayTitle = cleanLessonTitle(lesson.title);
                                            return (
                                              <div
                                                key={lesson.id}
                                                className={`unit-lesson-subitem ${isLessonActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  onSelectSubtopic(singleUnit.rel_path, lesson.id);
                                                }}
                                                title={lesson.title}
                                              >
                                                <span className={`sublesson-num ${isCompleted ? 'completed' : ''}`}>
                                                  {isCompleted ? '✓' : lIdx + 1}
                                                </span>
                                                <span className="sublesson-title">{displayTitle}</span>
                                                {onToggleLessonCompletion && (
                                                  <button
                                                    className={`sublesson-check-btn ${isCompleted ? 'checked' : ''}`}
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      onToggleLessonCompletion(singleUnit.rel_path, lesson.id, !isCompleted);
                                                    }}
                                                    title={isCompleted ? "Mark incomplete" : "Mark as completed"}
                                                  >
                                                    <Check size={11} />
                                                  </button>
                                                )}
                                              </div>
                                            );
                                          })}

                                          {singleUnit.status.has_labs && (
                                            <div
                                              className={`unit-lesson-subitem ${isSelected && (activeLessonId === 'labs' || activeTab === 'labs') ? 'active' : ''}`}
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                onSelectSubtopic(singleUnit.rel_path, 'labs');
                                              }}
                                              title="Operational Labs"
                                            >
                                              <FlaskConical size={11} className="sublesson-icon" />
                                              <span className="sublesson-title">Operational Labs</span>
                                            </div>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              }

                              const isCourseOpen = openCourses[courseKey] || cleanTerm.length > 0;
                              const completedUnits = units.filter((u) => u.status.complete).length;
                              const courseTitle = toTitleCase((cData as any).display_name || courseSlug);

                              return (
                                <div key={courseKey} className="course-group">
                                  <div
                                    className="course-header"
                                    onClick={() => {
                                      toggleCourse(courseKey);
                                      if (!isCourseOpen && matchingUnits.length > 0 && selectedSubtopic !== matchingUnits[0].rel_path) {
                                        onSelectSubtopic(matchingUnits[0].rel_path);
                                      }
                                    }}
                                    title={courseTitle}
                                  >
                                    <BookOpen size={13} className="course-icon" />
                                    <span className="course-title">
                                      {courseTitle}
                                    </span>
                                    <div className="course-meta">
                                      <span className="course-progress">
                                        {completedUnits}/{units.length}
                                      </span>
                                      {onDeleteTopic && (
                                        <button
                                          className="action-mini-btn delete"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteTopic(`${discKey}/${courseSlug}`);
                                          }}
                                          title={`Delete course ${courseTitle}`}
                                        >
                                          <Trash2 size={11} />
                                        </button>
                                      )}
                                    </div>
                                  </div>

                                  {isCourseOpen && (
                                    <div className="course-units-list">
                                      {matchingUnits.map((unitNode) => {
                                        const isSelected = selectedSubtopic === unitNode.rel_path;
                                        const hasMultiLessons = Boolean(unitNode.lessons && unitNode.lessons.length > 1);
                                        const isUnitOpen = openUnits[unitNode.rel_path] ?? isSelected;
                                        const unitTitle = toTitleCase(unitNode.display_name);

                                        const unitCompletedLessons = isSelected && completedLessons ? completedLessons : (unitNode.completed_lessons || []);
                                        const completedCount = unitCompletedLessons.length;
                                        const totalLessons = unitNode.lessons ? unitNode.lessons.length : 0;
                                        const isAllCompleted = totalLessons > 0 && completedCount >= totalLessons;

                                        return (
                                          <div key={unitNode.rel_path} className="unit-container">
                                            <div
                                              className={`${hasMultiLessons ? 'course-header has-subsections' : 'subtopic-item unit-item'} ${isSelected ? 'selected' : ''}`}
                                              onClick={() => {
                                                if (hasMultiLessons) {
                                                  toggleUnit(unitNode.rel_path);
                                                }
                                                onSelectSubtopic(unitNode.rel_path, hasMultiLessons ? 'all' : undefined);
                                              }}
                                            >
                                              {hasMultiLessons && <BookOpen size={13} className="course-icon" />}
                                              <span className={hasMultiLessons ? "course-title" : "subtopic-title"} title={unitTitle}>
                                                {unitTitle}
                                              </span>
                                              <div className={hasMultiLessons ? "course-meta" : "item-meta"}>
                                                {hasMultiLessons && (
                                                  <span
                                                    className={`course-progress ${isAllCompleted ? 'all-completed' : completedCount > 0 ? 'has-progress' : ''}`}
                                                    title={`${completedCount} of ${totalLessons} lessons completed`}
                                                  >
                                                    {completedCount > 0 ? `${completedCount}/${totalLessons}` : `${totalLessons}L`}
                                                    {isAllCompleted && ' ✓'}
                                                  </span>
                                                )}
                                                <div className="item-actions" onClick={(e) => e.stopPropagation()}>
                                                  {onRenameTopic && (
                                                    <button
                                                      className="action-mini-btn"
                                                      onClick={() => {
                                                        setRenameTarget({ path: unitNode.rel_path, currentTitle: unitNode.display_name });
                                                        setRenameInput(unitNode.display_name);
                                                      }}
                                                      title="Rename unit"
                                                    >
                                                      <Edit2 size={11} />
                                                    </button>
                                                  )}
                                                  {onDeleteTopic && (
                                                    <button
                                                      className="action-mini-btn delete"
                                                      onClick={() => onDeleteTopic(unitNode.rel_path)}
                                                      title="Delete unit"
                                                    >
                                                      <Trash2 size={11} />
                                                    </button>
                                                  )}
                                                </div>
                                              </div>
                                            </div>

                                            {/* Sub-lessons list nested directly under the unit */}
                                            {isUnitOpen && hasMultiLessons && unitNode.lessons && (
                                              <div className="unit-lessons-sublist">
                                                <div
                                                  className={`unit-lesson-subitem ${isSelected && (!activeLessonId || activeLessonId === 'all') ? 'active' : ''}`}
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    onSelectSubtopic(unitNode.rel_path, 'all');
                                                  }}
                                                  title="Complete Guide (All modules in full)"
                                                >
                                                  <BookOpen size={11} className="sublesson-icon" />
                                                  <span className="sublesson-title">Complete Guide</span>
                                                </div>

                                                {unitNode.lessons.map((lesson, lIdx) => {
                                                  const isLessonActive = isSelected && activeLessonId === lesson.id;
                                                  const isCompleted = unitCompletedLessons.includes(lesson.id);
                                                  const displayTitle = cleanLessonTitle(lesson.title);
                                                  return (
                                                    <div
                                                      key={lesson.id}
                                                      className={`unit-lesson-subitem ${isLessonActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                                                      onClick={(e) => {
                                                        e.stopPropagation();
                                                        onSelectSubtopic(unitNode.rel_path, lesson.id);
                                                      }}
                                                      title={lesson.title}
                                                    >
                                                      <span className={`sublesson-num ${isCompleted ? 'completed' : ''}`}>
                                                        {isCompleted ? '✓' : lIdx + 1}
                                                      </span>
                                                      <span className="sublesson-title">{displayTitle}</span>
                                                      {onToggleLessonCompletion && (
                                                        <button
                                                          className={`sublesson-check-btn ${isCompleted ? 'checked' : ''}`}
                                                          onClick={(e) => {
                                                            e.stopPropagation();
                                                            onToggleLessonCompletion(unitNode.rel_path, lesson.id, !isCompleted);
                                                          }}
                                                          title={isCompleted ? "Mark incomplete" : "Mark as completed"}
                                                        >
                                                          <Check size={11} />
                                                        </button>
                                                      )}
                                                    </div>
                                                  );
                                                })}

                                                {unitNode.status.has_labs && (
                                                  <div
                                                    className={`unit-lesson-subitem ${isSelected && (activeLessonId === 'labs' || activeTab === 'labs') ? 'active' : ''}`}
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      onSelectSubtopic(unitNode.rel_path, 'labs');
                                                    }}
                                                    title="Operational Labs"
                                                  >
                                                    <FlaskConical size={11} className="sublesson-icon" />
                                                    <span className="sublesson-title">Operational Labs</span>
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })
      )}
      </div>

      {/* Clean 4-Level Add Topic Modal */}
      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Course or Study Unit</h3>
              <button className="icon-btn" onClick={() => setShowAddModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateTopic}>
              <div className="form-group">
                <label>1. Target Domain</label>
                <select value={addDomain} onChange={(e) => setAddDomain(e.target.value)}>
                  {Object.keys(tree).map((d) => (
                    <option key={d} value={d}>
                      {d.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>2. Discipline / Category</label>
                <input
                  type="text"
                  placeholder="e.g. ai, infrastructure, security"
                  value={addDiscipline}
                  onChange={(e) => setAddDiscipline(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>3. Course Slug</label>
                <input
                  type="text"
                  placeholder="e.g. vibe_coding, kubernetes, rust_internals"
                  value={addCourse}
                  onChange={(e) => setAddCourse(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>4. Unit Slug (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. 01_prompt_engineering (default: 01_fundamentals)"
                  value={addUnitSlug}
                  onChange={(e) => setAddUnitSlug(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>5. Display Title</label>
                <input
                  type="text"
                  placeholder="e.g. Prompt Engineering & Spec-Driven Development"
                  value={addTitle}
                  onChange={(e) => setAddTitle(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Creating...' : 'Create Unit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rename Dialog Modal */}
      {renameTarget && (
        <div className="modal-backdrop" onClick={() => setRenameTarget(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Rename Study Unit</h3>
              <button className="icon-btn" onClick={() => setRenameTarget(null)}><X size={16} /></button>
            </div>
            <form onSubmit={handleRenameSubmit}>
              <div className="form-group">
                <label>Topic Path</label>
                <input type="text" value={renameTarget.path} disabled />
              </div>
              <div className="form-group">
                <label>New Display Title</label>
                <input
                  type="text"
                  value={renameInput}
                  onChange={(e) => setRenameInput(e.target.value)}
                  autoFocus
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setRenameTarget(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Title
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4-Node Cluster Health Footer */}
      {status?.cluster && (
        <div className="sidebar-cluster-footer">
          <div className="cluster-status-row">
            <span className="cluster-label">
              <Zap size={12} className="cluster-icon" />
              <span>Ollama Cluster</span>
            </span>
            <span className="cluster-count">
              {Object.values(status.cluster).filter((c) => c.online).length}/{Object.keys(status.cluster).length} Online
            </span>
          </div>
          <div className="cluster-nodes-pills">
            {Object.entries(status.cluster).map(([host, info]) => (
              <span
                key={host}
                className={`node-pill ${info.online ? 'online' : 'offline'}`}
                title={`${host}: ${info.online ? (info.preferred_model || (info.models && info.models[0]) || 'active') : 'offline'}`}
              >
                <span className="node-dot" />
                {host}
              </span>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
};

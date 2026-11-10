import React, { useState, useMemo } from 'react';
import {
  Folder,
  FolderOpen,
  Search,
  Plus,
  GitBranch,
  BookOpen,
  Cpu,
  Coins,
  Binary,
  FlaskConical,
  Palette,
  Hammer,
  ArrowUpDown,
  Languages,
  Settings
} from 'lucide-react';
import type { TopicTreeData, UnitNode } from '../types';

interface TopicTreeProps {
  tree: TopicTreeData;
  selectedSubtopic: string | null;
  onSelectSubtopic: (query: string) => void;
  onAddSubtopic: (domain: string, category: string, subtopic: string, title?: string) => Promise<void>;
  onOpenSearch: () => void;
  onOpenGraph: () => void;
  onOpenSettings: () => void;
}

const DOMAIN_ORDER = [
  'computing',
  'engineering',
  'motorsports',
  'crafts',
  'formal_sciences',
  'natural_sciences',
  'arts',
  'languages',
  'humanities',
  'business',
  'economics',
];

export const TopicTree: React.FC<TopicTreeProps> = ({
  tree,
  selectedSubtopic,
  onSelectSubtopic,
  onAddSubtopic,
  onOpenSearch,
  onOpenGraph,
  onOpenSettings,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortMode, setSortMode] = useState<'default' | 'az' | 'progress'>('default');
  const [openDomains, setOpenDomains] = useState<{ [key: string]: boolean }>({
    computing: true,
  });
  const [openDisciplines, setOpenDisciplines] = useState<{ [key: string]: boolean }>({
    'computing/infrastructure': true,
  });
  const [openCourses, setOpenCourses] = useState<{ [key: string]: boolean }>({
    'computing/infrastructure/kubernetes': true,
  });
  const [showAddModal, setShowAddModal] = useState(false);
  const [addDomain, setAddDomain] = useState('computing');
  const [addCategory, setAddCategory] = useState('');
  const [addSubtopicId, setAddSubtopicId] = useState('');
  const [addTitle, setAddTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

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
        return <Cpu size={16} className="domain-icon" />;
      case 'engineering':
        return <Hammer size={16} className="domain-icon" />;
      case 'formal_sciences':
        return <Binary size={16} className="domain-icon" />;
      case 'natural_sciences':
        return <FlaskConical size={16} className="domain-icon" />;
      case 'business':
      case 'economics':
        return <Coins size={16} className="domain-icon" />;
      case 'arts':
        return <Palette size={16} className="domain-icon" />;
      case 'languages':
        return <Languages size={16} className="domain-icon" />;
      default:
        return <Folder size={16} className="domain-icon" />;
    }
  };

  const renderBadge = (node: UnitNode) => {
    const st = node.status;
    if (st.complete) {
      return <span className="badge badge-complete" title="All tiers complete">FLB</span>;
    }
    const f = st.has_foundation ? 'F' : '.';
    const l = st.has_lesson ? 'L' : '.';
    const b = st.has_labs ? 'B' : '.';
    const isPartial = st.has_foundation || st.has_lesson || st.has_labs;
    return (
      <span className={`badge ${isPartial ? 'badge-partial' : 'badge-empty'}`}>
        {f}{l}{b}
      </span>
    );
  };

  const handleCreateTopic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addSubtopicId.trim() || !addCategory.trim()) return;
    setIsSubmitting(true);
    try {
      await onAddSubtopic(addDomain, addCategory.trim(), addSubtopicId.trim(), addTitle.trim() || undefined);
      setShowAddModal(false);
      setAddSubtopicId('');
      setAddTitle('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
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
      if (sortMode === 'az') {
        return a.localeCompare(b);
      }
      if (sortMode === 'progress') {
        const rateA = getDomainCompletion(ddataA).rate;
        const rateB = getDomainCompletion(ddataB).rate;
        return rateB - rateA;
      }
      // default established order
      const idxA = DOMAIN_ORDER.indexOf(a);
      const idxB = DOMAIN_ORDER.indexOf(b);
      return (idxA !== -1 ? idxA : 999) - (idxB !== -1 ? idxB : 999);
    });
  }, [tree, sortMode]);

  const cleanTerm = searchTerm.trim().toLowerCase();

  return (
    <aside className="tree-sidebar">
      <div className="sidebar-header">
        <div className="brand">
          <svg className="brand-logo-svg" viewBox="0 0 48 48" width="32" height="32" fill="none">
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
          <button className="icon-btn" onClick={onOpenSearch} title="Full-Text Search (Cmd+K)">
            <Search size={14} />
          </button>
          <button className="icon-btn" onClick={onOpenGraph} title="Prerequisite Learning DAG">
            <GitBranch size={14} />
          </button>
          <button className="icon-btn" onClick={onOpenSettings} title="Workbench Settings">
            <Settings size={14} />
          </button>
          <button
            className="btn-primary-sm"
            onClick={() => setShowAddModal(true)}
            title="Add New Topic/Subtopic"
          >
            <Plus size={14} />
          </button>
        </div>
      </div>

      {/* Search & Sort Controls */}
      <div className="search-filter-row">
        <div className="search-box">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            placeholder="Filter topics..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="sort-box" title="Sort topics">
          <ArrowUpDown size={12} className="sort-icon" />
          <select
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as any)}
            className="sort-select"
          >
            <option value="default">Default</option>
            <option value="az">A to Z</option>
            <option value="progress">Progress</option>
          </select>
        </div>
      </div>

      <div className="tree-content">
        {sortedDomainEntries.map(([domain, ddata]) => {
          const disciplines = ddata.disciplines || {};

          let sortedDisciplines = Object.entries(disciplines);
          if (sortMode === 'az') {
            sortedDisciplines.sort(([a], [b]) => a.localeCompare(b));
          }

          // Filter check for domain
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
                  {domain.replace(/_/g, ' ')}
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
                            {disc.replace(/_/g, ' ')}
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
                                return (
                                  <div
                                    key={singleUnit.rel_path}
                                    className={`subtopic-item ${isSelected ? 'selected' : ''}`}
                                    onClick={() => onSelectSubtopic(singleUnit.rel_path)}
                                  >
                                    <span className="subtopic-title" title={singleUnit.rel_path}>
                                      {singleUnit.display_name}
                                    </span>
                                    {renderBadge(singleUnit)}
                                  </div>
                                );
                              }

                              const isCourseOpen = openCourses[courseKey] || cleanTerm.length > 0;
                              const completedUnits = units.filter((u) => u.status.complete).length;

                              return (
                                <div key={courseKey} className="course-group">
                                  <div
                                    className="course-header"
                                    onClick={() => toggleCourse(courseKey)}
                                  >
                                    <BookOpen size={13} className="course-icon" />
                                    <span className="course-title">
                                      {courseSlug.replace(/_/g, ' ')}
                                    </span>
                                    <span className="course-progress">
                                      {completedUnits}/{units.length}
                                    </span>
                                  </div>

                                  {isCourseOpen && (
                                    <div className="course-units-list">
                                      {matchingUnits.map((unitNode) => {
                                        const isSelected = selectedSubtopic === unitNode.rel_path;
                                        return (
                                          <div
                                            key={unitNode.rel_path}
                                            className={`subtopic-item unit-item ${isSelected ? 'selected' : ''}`}
                                            onClick={() => onSelectSubtopic(unitNode.rel_path)}
                                          >
                                            <span className="subtopic-title" title={unitNode.rel_path}>
                                              {unitNode.display_name}
                                            </span>
                                            {renderBadge(unitNode)}
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
        })}
      </div>

      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Topic</h3>
              <button className="icon-btn" onClick={() => setShowAddModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateTopic}>
              <div className="form-group">
                <label>Domain</label>
                <select value={addDomain} onChange={(e) => setAddDomain(e.target.value)}>
                  {Object.keys(tree).map((d) => (
                    <option key={d} value={d}>
                      {d.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Discipline / Course Path</label>
                <input
                  type="text"
                  placeholder="e.g. infrastructure/kubernetes"
                  value={addCategory}
                  onChange={(e) => setAddCategory(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Unit Slug</label>
                <input
                  type="text"
                  placeholder="e.g. 01_control_plane"
                  value={addSubtopicId}
                  onChange={(e) => setAddSubtopicId(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Display Title (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Control Plane Internals & etcd"
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
    </aside>
  );
};

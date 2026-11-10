import React, { useState } from 'react';
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
  Hammer
} from 'lucide-react';
import type { TopicTreeData, UnitNode } from '../types';

interface TopicTreeProps {
  tree: TopicTreeData;
  selectedSubtopic: string | null;
  onSelectSubtopic: (query: string) => void;
  onAddSubtopic: (domain: string, category: string, subtopic: string, title?: string) => Promise<void>;
  onOpenSearch: () => void;
  onOpenGraph: () => void;
}

const DOMAIN_ORDER = [
  'computing',
  'engineering',
  'motorsports',
  'crafts',
  'formal_sciences',
  'natural_sciences',
  'arts',
  'business',
  'economics',
  'humanities',
];

export const TopicTree: React.FC<TopicTreeProps> = ({
  tree,
  selectedSubtopic,
  onSelectSubtopic,
  onAddSubtopic,
  onOpenSearch,
  onOpenGraph,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
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

  return (
    <aside className="tree-sidebar">
      <div className="sidebar-header">
        <div className="brand">
          <svg className="brand-logo-svg" viewBox="0 0 48 48" width="22" height="22" fill="none">
            <circle cx="24" cy="24" r="20" stroke="#58a6ff" strokeWidth="2" strokeDasharray="4 2" opacity="0.6"/>
            <polygon points="24,8 38,16 38,32 24,40 10,32 10,16" stroke="#39c5cf" strokeWidth="2.5" fill="#161b22" />
            <line x1="24" y1="8" x2="24" y2="24" stroke="#58a6ff" strokeWidth="2" />
            <line x1="38" y1="16" x2="24" y2="24" stroke="#39c5cf" strokeWidth="2" />
            <line x1="38" y1="32" x2="24" y2="24" stroke="#3fb950" strokeWidth="2" />
            <line x1="24" y1="40" x2="24" y2="24" stroke="#3fb950" strokeWidth="2" />
            <line x1="10" y1="32" x2="24" y2="24" stroke="#58a6ff" strokeWidth="2" />
            <line x1="10" y1="16" x2="24" y2="24" stroke="#39c5cf" strokeWidth="2" />
            <circle cx="24" cy="24" r="4.5" fill="#3fb950" />
            <circle cx="24" cy="24" r="2.5" fill="#f0f6fc"/>
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
          <button
            className="btn-primary-sm"
            onClick={() => setShowAddModal(true)}
            title="Add New Topic/Subtopic"
          >
            <Plus size={14} />
          </button>
        </div>
      </div>

      <div className="search-box">
        <Search size={14} className="search-icon" />
        <input
          type="text"
          placeholder="Filter topics or paths..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="tree-content">
        {Object.entries(tree)
          .sort(([a], [b]) => {
            const idxA = DOMAIN_ORDER.indexOf(a);
            const idxB = DOMAIN_ORDER.indexOf(b);
            return (idxA !== -1 ? idxA : 999) - (idxB !== -1 ? idxB : 999);
          })
          .map(([domain, ddata]) => {
          const isDomainOpen = openDomains[domain] || searchTerm.length > 0;
          const disciplines = ddata.disciplines || {};

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
                  {Object.entries(disciplines).map(([disc, discData]) => {
                    const discKey = `${domain}/${disc}`;
                    const isDiscOpen = openDisciplines[discKey] || searchTerm.length > 0;
                    const courses = discData.courses || {};

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
                            {Object.entries(courses).map(([courseSlug, cData]) => {
                              const courseKey = `${discKey}/${courseSlug}`;
                              const isCourseOpen = openCourses[courseKey] || searchTerm.length > 0;
                              const units = Object.values(cData.units || {});

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

                              const completedUnits = units.filter((u) => u.status.complete).length;

                              return (
                                <div key={courseKey} className="course-group">
                                  <div
                                    className="course-header"
                                    onClick={() => toggleCourse(courseKey)}
                                  >
                                    <BookOpen size={12} className="course-icon" />
                                    <span className="course-title">
                                      {courseSlug.replace(/_/g, ' ')}
                                    </span>
                                    <span className="course-progress">
                                      {completedUnits}/{units.length}
                                    </span>
                                  </div>

                                  {isCourseOpen && (
                                    <div className="course-units-list">
                                      {units.map((unitNode) => {
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

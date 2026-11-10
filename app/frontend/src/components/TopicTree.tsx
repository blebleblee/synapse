import React, { useState } from 'react';
import {
  Folder,
  FolderOpen,
  Search,
  Plus,
  GitBranch,
  Cpu,
  Coins,
  Binary,
  FlaskConical,
  Palette,
  Hammer
} from 'lucide-react';
import type { TopicTreeData, SubtopicNode } from '../types';

interface TopicTreeProps {
  tree: TopicTreeData;
  selectedSubtopic: string | null;
  onSelectSubtopic: (query: string) => void;
  onAddSubtopic: (domain: string, category: string, subtopic: string, title?: string) => Promise<void>;
  onOpenSearch: () => void;
  onOpenGraph: () => void;
}

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
    computing_and_engineering: true,
  });
  const [openCategories, setOpenCategories] = useState<{ [key: string]: boolean }>({
    'computing_and_engineering/infrastructure_and_ops': true,
  });
  const [showAddModal, setShowAddModal] = useState(false);
  const [addDomain, setAddDomain] = useState('computing_and_engineering');
  const [addCategory, setAddCategory] = useState('');
  const [addSubtopicId, setAddSubtopicId] = useState('');
  const [addTitle, setAddTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleDomain = (domain: string) => {
    setOpenDomains((prev) => ({ ...prev, [domain]: !prev[domain] }));
  };

  const toggleCategory = (catKey: string) => {
    setOpenCategories((prev) => ({ ...prev, [catKey]: !prev[catKey] }));
  };

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case 'computing_and_engineering':
        return <Cpu size={16} className="domain-icon" />;
      case 'business_and_economics':
        return <Coins size={16} className="domain-icon" />;
      case 'formal_sciences':
        return <Binary size={16} className="domain-icon" />;
      case 'natural_sciences':
        return <FlaskConical size={16} className="domain-icon" />;
      case 'arts_and_humanities':
        return <Palette size={16} className="domain-icon" />;
      case 'hobbies_and_crafts':
        return <Hammer size={16} className="domain-icon" />;
      default:
        return <Folder size={16} className="domain-icon" />;
    }
  };

  const renderBadge = (node: SubtopicNode) => {
    const st = node.status;
    if (st.complete) {
      return <span className="badge badge-complete" title="Foundation, Lesson, and Labs Ready">FLB</span>;
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
          <div className="brand-dot" />
          <span className="brand-title">Learning Workbench</span>
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
        {Object.entries(tree).map(([domain, ddata]) => {
          const isDomainOpen = openDomains[domain] || searchTerm.length > 0;

          // Check if domain matches search
          const domainCategories = Object.entries(ddata.categories);
          const hasMatchingSubtopics = domainCategories.some(([_, subtopics]) =>
            Object.values(subtopics).some((s) =>
              s.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              s.rel_path.toLowerCase().includes(searchTerm.toLowerCase())
            )
          );

          if (searchTerm && !hasMatchingSubtopics && !domain.toLowerCase().includes(searchTerm.toLowerCase())) {
            return null;
          }

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
                  {domainCategories.map(([category, subtopics]) => {
                    const catKey = `${domain}/${category}`;
                    const isCatOpen = openCategories[catKey] || searchTerm.length > 0;

                    const filteredSubtopics = Object.entries(subtopics).filter(([_, s]) => {
                      if (!searchTerm) return true;
                      return (
                        s.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        s.rel_path.toLowerCase().includes(searchTerm.toLowerCase())
                      );
                    });

                    if (searchTerm && filteredSubtopics.length === 0) {
                      return null;
                    }

                    return (
                      <div key={catKey} className="category-group">
                        <div
                          className="category-header"
                          onClick={() => toggleCategory(catKey)}
                        >
                          <FolderOpen size={14} className="category-icon" />
                          <span className="category-label">
                            {category.replace(/_/g, ' ')}
                          </span>
                          <span className="category-count">{Object.keys(subtopics).length}</span>
                        </div>

                        {isCatOpen && (
                          <div className="subtopic-list">
                            {filteredSubtopics.map(([_, subNode]) => {
                              const isSelected = selectedSubtopic === subNode.rel_path;
                              return (
                                <div
                                  key={subNode.rel_path}
                                  className={`subtopic-item ${isSelected ? 'selected' : ''}`}
                                  onClick={() => onSelectSubtopic(subNode.rel_path)}
                                >
                                  <span className="subtopic-title" title={subNode.rel_path}>
                                    {subNode.display_name}
                                  </span>
                                  {renderBadge(subNode)}
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
                <label>Category (Folder Slug)</label>
                <input
                  type="text"
                  placeholder="e.g. infrastructure_and_ops, macro_and_policy"
                  value={addCategory}
                  onChange={(e) => setAddCategory(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Subtopic Slug</label>
                <input
                  type="text"
                  placeholder="e.g. wasm, vector_databases"
                  value={addSubtopicId}
                  onChange={(e) => setAddSubtopicId(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Display Title (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. WebAssembly & Edge Compute"
                  value={addTitle}
                  onChange={(e) => setAddTitle(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Creating...' : 'Create Subtopic'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
};

import React, { useState, useEffect } from 'react';
import { Search, X, BookOpen } from 'lucide-react';

interface SearchResult {
  domain: string;
  category: string;
  subtopic: string;
  level?: string;
  file: string;
  path: string;
  section: string;
  snippet: string;
  match_count: number;
}

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTopic: (path: string, lessonId?: string) => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({
  isOpen,
  onClose,
  onSelectTopic,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      if (query.trim().length >= 2) {
        setIsSearching(true);
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(query.trim())}`);
          if (res.ok) {
            const data = await res.json();
            setResults(data.results || []);
          }
        } catch (err) {
          console.error('Search error:', err);
        } finally {
          setIsSearching(false);
        }
      } else {
        setResults([]);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query, isOpen]);

  // Global Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="search-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="search-modal-header">
          <Search size={16} className="search-modal-icon" />
          <input
            type="text"
            placeholder="Search full curriculum content (e.g. Raft, cgroups, eBPF, ASLR, VCG)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <button className="icon-btn" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="search-modal-results">
          {isSearching && (
            <div className="search-loading">
              <div className="spinner" />
              <span>Searching curriculum units...</span>
            </div>
          )}

          {!isSearching && query.trim().length >= 2 && results.length === 0 && (
            <div className="search-empty">
              <p>No content matches found for "{query}".</p>
            </div>
          )}

          {!isSearching && results.map((r, idx) => (
            <div
              key={idx}
              className="search-result-item"
              onClick={() => {
                const lessonId = r.file ? r.file.replace(/\.md$/, '') : undefined;
                onSelectTopic(r.path, lessonId);
                onClose();
              }}
            >
              <div className="result-meta">
                <span className="result-domain">{r.domain}</span>
                <span className="result-sep">/</span>
                <span className="result-cat">{r.category}</span>
                <span className="result-sep">/</span>
                <span className="result-sub">{r.subtopic}</span>
                {r.level && r.level !== 'root' && (
                  <span className="result-level-tag">{r.level.toUpperCase()}</span>
                )}
              </div>

              <div className="result-section">
                <BookOpen size={13} />
                <span>{r.section}</span>
              </div>

              <p className="result-snippet">{r.snippet}</p>
            </div>
          ))}

          {!query && (
            <div className="search-hint">
              <span>Type keywords to search across all Foundation, Lesson, and Lab guides.</span>
              <kbd>ESC</kbd> to close
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

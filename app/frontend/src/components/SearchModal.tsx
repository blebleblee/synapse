import React, { useState, useEffect, useMemo } from 'react';
import { Search, X, BookOpen } from 'lucide-react';
import { splitHighlight } from '../utils/text';

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
  onSelectTopic: (path: string, lessonId?: string, sectionTitle?: string) => void;
}

function HighlightedText({ text, query }: { text: string; query: string }) {
  const parts = splitHighlight(text, query);
  return (
    <>
      {parts.map((p, idx) =>
        p.isMatch ? (
          <mark key={idx} className="search-highlight">
            {p.text}
          </mark>
        ) : (
          p.text
        )
      )}
    </>
  );
}

// Mounted only while open, so every opening starts with an empty query.
export const SearchModal: React.FC<SearchModalProps> = ({ isOpen, ...props }) =>
  isOpen ? <SearchPanel {...props} /> : null;

const SearchPanel: React.FC<Omit<SearchModalProps, 'isOpen'>> = ({
  onClose,
  onSelectTopic,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [isSearching, setIsSearching] = useState(false);

  const [prevQuery, setPrevQuery] = useState(query);
  if (query !== prevQuery) {
    setPrevQuery(query);
    setSelectedDomain('all');
  }

  const domainCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of results) {
      if (r.domain) {
        counts[r.domain] = (counts[r.domain] || 0) + 1;
      }
    }
    return counts;
  }, [results]);

  const availableDomains = useMemo(() => Object.keys(domainCounts).sort(), [domainCounts]);

  const filteredResults = useMemo(() => {
    if (selectedDomain === 'all') return results;
    return results.filter((r) => r.domain === selectedDomain);
  }, [results, selectedDomain]);

  useEffect(() => {
    // Each keystroke cancels the previous request, and a response that arrives
    // after the query changed is ignored, so older results never overwrite newer ones.
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      if (query.trim().length >= 2) {
        setIsSearching(true);
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(query.trim())}`, {
            signal: controller.signal,
          });
          if (res.ok && !controller.signal.aborted) {
            const data = await res.json();
            if (!controller.signal.aborted) setResults(data.results || []);
          }
        } catch (err) {
          if (!controller.signal.aborted) console.error('Search error:', err);
        } finally {
          if (!controller.signal.aborted) setIsSearching(false);
        }
      } else {
        setResults([]);
      }
    }, 400);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  // Global Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

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

        {availableDomains.length > 1 && (
          <div className="search-domain-filters">
            <button
              type="button"
              className={`search-filter-chip ${selectedDomain === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedDomain('all')}
            >
              All ({results.length})
            </button>
            {availableDomains.map((domain) => (
              <button
                key={domain}
                type="button"
                className={`search-filter-chip ${selectedDomain === domain ? 'active' : ''}`}
                onClick={() => setSelectedDomain(selectedDomain === domain ? 'all' : domain)}
              >
                {domain.replace(/_/g, ' ')} ({domainCounts[domain]})
              </button>
            ))}
          </div>
        )}

        <div className="search-modal-results">
          {isSearching && (
            <div className="search-loading">
              <div className="spinner" />
              <span>Searching curriculum units...</span>
            </div>
          )}

          {!isSearching && query.trim().length >= 2 && filteredResults.length === 0 && (
            <div className="search-empty">
              <p>
                {selectedDomain === 'all'
                  ? `No content matches found for "${query}".`
                  : `No matches in ${selectedDomain.replace(/_/g, ' ')} for "${query}".`}
              </p>
            </div>
          )}

          {!isSearching && filteredResults.map((r, idx) => (
            <div
              key={idx}
              className="search-result-item"
              onClick={() => {
                const lessonId = r.file ? r.file.replace(/\.md$/, '') : undefined;
                onSelectTopic(r.path, lessonId, r.section);
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
                <span><HighlightedText text={r.section} query={query} /></span>
              </div>

              <p className="result-snippet"><HighlightedText text={r.snippet} query={query} /></p>
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

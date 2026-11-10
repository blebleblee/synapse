import React, { useState, useEffect } from 'react';
import { GitBranch, X, CheckCircle2, Circle, ArrowRight } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  domain: string;
  category: string;
  subtopic: string;
  complete: boolean;
  color: string;
}

interface GraphEdge {
  source: string;
  target: string;
}

interface GraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTopic: (path: string) => void;
}

export const GraphModal: React.FC<GraphModalProps> = ({
  isOpen,
  onClose,
  onSelectTopic,
}) => {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const fetchGraph = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('/api/graph');
        if (res.ok) {
          const data = await res.json();
          setNodes(data.nodes || []);
          setEdges(data.edges || []);
        }
      } catch (err) {
        console.error('Failed to load graph:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGraph();
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredEdges = edges.filter((e) => {
    if (selectedDomain === 'all') return true;
    return e.source.startsWith(selectedDomain) || e.target.startsWith(selectedDomain);
  });

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="graph-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="graph-title-box">
            <GitBranch size={18} className="graph-icon" />
            <h3>Prerequisite Learning Dependency DAG</h3>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="graph-filter-bar">
          <span>Filter Domain:</span>
          <select value={selectedDomain} onChange={(e) => setSelectedDomain(e.target.value)}>
            <option value="all">All Domains</option>
            <option value="computing">Computing</option>
            <option value="engineering">Engineering</option>
            <option value="formal_sciences">Formal Sciences</option>
            <option value="natural_sciences">Natural Sciences</option>
            <option value="arts">Arts</option>
            <option value="crafts">Crafts</option>
            <option value="motorsports">Motorsports</option>
          </select>
        </div>

        <div className="graph-content">
          {isLoading ? (
            <div className="viewer-empty">
              <div className="spinner" />
              <p>Analyzing learning pathways...</p>
            </div>
          ) : (
            <div className="dag-chain-list">
              {filteredEdges.map((e, idx) => {
                const srcNode = nodeMap.get(e.source);
                const dstNode = nodeMap.get(e.target);

                return (
                  <div key={idx} className="dag-edge-card">
                    <div
                      className="dag-node-chip"
                      style={{ borderColor: srcNode?.color || '#58a6ff' }}
                      onClick={() => {
                        onSelectTopic(e.source);
                        onClose();
                      }}
                    >
                      {srcNode?.complete ? (
                        <CheckCircle2 size={13} className="dag-status-icon complete" />
                      ) : (
                        <Circle size={13} className="dag-status-icon pending" />
                      )}
                      <span className="dag-chip-title">{srcNode?.label || e.source}</span>
                      <span className="dag-chip-domain">{srcNode?.domain}</span>
                    </div>

                    <div className="dag-arrow-box">
                      <ArrowRight size={16} className="dag-arrow" />
                      <span className="dag-arrow-label">Prerequisite for</span>
                    </div>

                    <div
                      className="dag-node-chip"
                      style={{ borderColor: dstNode?.color || '#3fb950' }}
                      onClick={() => {
                        onSelectTopic(e.target);
                        onClose();
                      }}
                    >
                      {dstNode?.complete ? (
                        <CheckCircle2 size={13} className="dag-status-icon complete" />
                      ) : (
                        <Circle size={13} className="dag-status-icon pending" />
                      )}
                      <span className="dag-chip-title">{dstNode?.label || e.target}</span>
                      <span className="dag-chip-domain">{dstNode?.domain}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

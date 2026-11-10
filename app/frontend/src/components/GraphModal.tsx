import React, { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { GitBranch, X, CheckCircle2, Circle, ArrowRight, ZoomIn, ZoomOut, Maximize2, Search, Network, List } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  domain: string;
  category: string;
  subtopic: string;
  complete: boolean;
  color: string;
  degree?: number;
  prerequisites?: string[];
  unlocks?: string[];
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
  const [viewMode, setViewMode] = useState<'network' | 'list'>('network');
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const cyContainerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

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

  // Initialize or update Cytoscape network
  useEffect(() => {
    if (!isOpen || viewMode !== 'network' || !cyContainerRef.current || nodes.length === 0) return;

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // Filter nodes by domain / query
    const filteredNodes = nodes.filter((n) => {
      if (selectedDomain !== 'all' && n.domain !== selectedDomain) return false;
      if (filterQuery.trim()) {
        const q = filterQuery.toLowerCase();
        return n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q);
      }
      return true;
    });

    const activeNodeIds = new Set(filteredNodes.map((n) => n.id));

    // Filter edges that connect active nodes
    const filteredEdges = edges.filter(
      (e) => activeNodeIds.has(e.source) && activeNodeIds.has(e.target)
    );

    const elements: cytoscape.ElementDefinition[] = [
      ...filteredNodes.map((n) => ({
        data: {
          id: n.id,
          label: n.label.split(':')[1]?.trim() || n.subtopic.replace(/_/g, ' '),
          fullLabel: n.label,
          domain: n.domain,
          color: n.color,
          complete: n.complete,
        },
      })),
      ...filteredEdges.map((e) => ({
        data: {
          id: `${e.source}->${e.target}`,
          source: e.source,
          target: e.target,
        },
      })),
    ];

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: cyContainerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#cbd5e1',
            'font-size': '11px',
            'font-family': 'ui-sans-serif, system-ui, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'width': 18,
            'height': 18,
            'border-width': 2,
            'border-color': '#1e293b',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#fbbf24',
            'border-width': 4,
            'color': '#fbbf24',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.7,
            'arrow-scale': 0.8,
          },
        },
      ],
      layout: {
        name: filteredNodes.length > 100 ? 'concentric' : 'cose',
        animate: false,
        padding: 30,
      } as any,
    });

    cy.on('tap', 'node', (evt) => {
      const nodeId = evt.target.id();
      const nodeData = nodeMap.get(nodeId) || null;
      setSelectedNode(nodeData);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [isOpen, viewMode, nodes, edges, selectedDomain, filterQuery]);

  if (!isOpen) return null;

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const filteredEdges = edges.filter((e) => {
    if (selectedDomain === 'all') return true;
    return e.source.startsWith(selectedDomain) || e.target.startsWith(selectedDomain);
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="graph-modal-card visual-dag-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="graph-title-box">
            <GitBranch size={18} className="graph-icon" />
            <h3>Prerequisite Learning Knowledge Graph</h3>
            <span className="dag-stats-pill">{nodes.length} Units • {edges.length} Learning Bridges</span>
          </div>

          <div className="dag-header-actions">
            <div className="view-toggle-pills">
              <button
                className={`view-pill-btn ${viewMode === 'network' ? 'active' : ''}`}
                onClick={() => setViewMode('network')}
                title="Interactive 2D Network Graph Canvas"
              >
                <Network size={12} />
                <span>Canvas</span>
              </button>
              <button
                className={`view-pill-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="Linear Dependency Pathways"
              >
                <List size={12} />
                <span>List</span>
              </button>
            </div>
            <button className="icon-btn" onClick={onClose}><X size={16} /></button>
          </div>
        </div>

        <div className="graph-filter-bar">
          <div className="filter-group">
            <label>Domain:</label>
            <select value={selectedDomain} onChange={(e) => setSelectedDomain(e.target.value)}>
              <option value="all">All Domains (Polymath Graph)</option>
              <option value="computing">Computing</option>
              <option value="engineering">Engineering</option>
              <option value="formal_sciences">Formal Sciences</option>
              <option value="natural_sciences">Natural Sciences</option>
              <option value="health_sciences">Health Sciences</option>
              <option value="arts">Arts</option>
              <option value="crafts">Crafts</option>
              <option value="motorsports">Motorsports</option>
              <option value="languages">Languages</option>
              <option value="humanities">Humanities</option>
              <option value="business">Business</option>
              <option value="economics">Economics</option>
            </select>
          </div>

          <div className="search-filter-box">
            <Search size={13} className="search-icon" />
            <input
              type="text"
              placeholder="Search concepts e.g. 'eBPF', 'Calculus', 'Piano'..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="dag-search-input"
            />
            {filterQuery && (
              <button className="clear-btn" onClick={() => setFilterQuery('')}>
                <X size={12} />
              </button>
            )}
          </div>

          {viewMode === 'network' && (
            <div className="cy-zoom-controls">
              <button className="icon-btn" onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)} title="Zoom In">
                <ZoomIn size={14} />
              </button>
              <button className="icon-btn" onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)} title="Zoom Out">
                <ZoomOut size={14} />
              </button>
              <button className="icon-btn" onClick={() => cyRef.current?.fit()} title="Fit Network to Viewport">
                <Maximize2 size={14} />
              </button>
            </div>
          )}
        </div>

        <div className="graph-content visual-canvas-content">
          {isLoading ? (
            <div className="viewer-empty">
              <div className="spinner" />
              <p>Resolving multi-tier dependency pathways across 700+ units...</p>
            </div>
          ) : viewMode === 'network' ? (
            <div className="cytoscape-wrapper">
              <div className="cytoscape-container" ref={cyContainerRef} />

              {/* Floating Node Inspector Panel */}
              {selectedNode && (
                <div className="dag-node-inspector">
                  <div className="inspector-header">
                    <span className="inspector-domain" style={{ color: selectedNode.color }}>
                      {selectedNode.domain.replace(/_/g, ' ')}
                    </span>
                    <button className="icon-btn" onClick={() => setSelectedNode(null)}><X size={13} /></button>
                  </div>
                  <h4 className="inspector-title">{selectedNode.label}</h4>
                  <p className="inspector-path"><code>{selectedNode.id}</code></p>

                  <div className="inspector-stats">
                    <div className="stat-item">
                      <span className="stat-label">Prerequisites:</span>
                      <span className="stat-val">{selectedNode.prerequisites?.length || 0}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Unlocks:</span>
                      <span className="stat-val">{selectedNode.unlocks?.length || 0}</span>
                    </div>
                  </div>

                  <button
                    className="btn btn-primary inspector-nav-btn"
                    onClick={() => {
                      onSelectTopic(selectedNode.id);
                      onClose();
                    }}
                  >
                    <span>Study This Unit</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              )}
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

                    <div className="dag-arrow-connector">
                      <ArrowRight size={14} />
                      <span className="dag-edge-label">unlocks</span>
                    </div>

                    <div
                      className="dag-node-chip"
                      style={{ borderColor: dstNode?.color || '#58a6ff' }}
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

import React, { useState } from 'react';
import { Sparkles, X, Check, Loader2, BookOpen } from 'lucide-react';

interface AIUnitItem {
  title: string;
  slug: string;
  description?: string;
  selected?: boolean;
}

interface AIExpandPlan {
  domain: string;
  discipline: string;
  course: string;
  course_title: string;
  units: AIUnitItem[];
}

interface AIExpandModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialPath?: string;
  onSuccess: (firstUnitPath: string) => void;
}

export const AIExpandModal: React.FC<AIExpandModalProps> = ({
  isOpen,
  onClose,
  initialPath = '',
  onSuccess,
}) => {
  const [targetPath, setTargetPath] = useState(initialPath);
  const [userPrompt, setUserPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [plan, setPlan] = useState<AIExpandPlan | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync initialPath when opened
  React.useEffect(() => {
    if (isOpen && initialPath) {
      setTargetPath(initialPath);
    }
  }, [isOpen, initialPath]);

  if (!isOpen) return null;

  const handleGeneratePlan = async () => {
    if (!targetPath.trim()) {
      setErrorMsg('Please specify a target path e.g. motorsports/driving/formula_1');
      return;
    }

    setIsGenerating(true);
    setErrorMsg(null);
    setPlan(null);

    try {
      const res = await fetch('/api/topic/ai-expand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: targetPath.trim(),
          prompt: userPrompt.trim(),
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to generate expansion plan: ${res.statusText}`);
      }

      const data = await res.json();
      if (data.units && Array.isArray(data.units)) {
        // Default all units selected
        data.units = data.units.map((u: any) => ({ ...u, selected: true }));
        setPlan(data);
      } else {
        throw new Error('AI returned an unexpected format.');
      }
    } catch (err: any) {
      console.error('AI expand error:', err);
      setErrorMsg(err.message || 'Failed to generate curriculum plan.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleToggleUnit = (idx: number) => {
    if (!plan) return;
    const newUnits = [...plan.units];
    newUnits[idx].selected = !newUnits[idx].selected;
    setPlan({ ...plan, units: newUnits });
  };

  const handleTitleChange = (idx: number, newTitle: string) => {
    if (!plan) return;
    const newUnits = [...plan.units];
    newUnits[idx].title = newTitle;
    setPlan({ ...plan, units: newUnits });
  };

  const handleApplyPlan = async () => {
    if (!plan) return;

    const selectedUnits = plan.units.filter((u) => u.selected !== false);
    if (selectedUnits.length === 0) {
      setErrorMsg('Please select at least one unit to create.');
      return;
    }

    setIsApplying(true);
    setErrorMsg(null);

    try {
      const res = await fetch('/api/topic/ai-expand/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: plan.domain,
          discipline: plan.discipline,
          course: plan.course,
          course_title: plan.course_title,
          units: selectedUnits,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to apply and commit curriculum plan.');
      }

      const data = await res.json();
      onSuccess(data.first_unit_path);
      onClose();
    } catch (err: any) {
      console.error('Failed to apply plan:', err);
      setErrorMsg(err.message || 'Failed to save and commit plan.');
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="ai-expand-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="graph-title-box">
            <Sparkles size={18} className="ai-sparkle-icon" />
            <h3>AI Curriculum Auto-Expander</h3>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="modal-body">
          <p className="ai-expand-desc">
            Select any hierarchy level (Domain, Discipline, or Course) and AI will structure calibrated, 2–3 hour modular study units with progressive depth and automatic Git synchronization.
          </p>

          <div className="form-group">
            <label>Target Hierarchy Path (Level 1–3 or Broaden)</label>
            <input
              type="text"
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
              placeholder="e.g. motorsports/driving/formula_1 or computing/ai"
              className="text-input"
            />
            <span className="field-hint">
              Examples: <code>motorsports/driving/formula_1</code> (new course), <code>motorsports/driving</code> (scaffold discipline), or enter an existing unit to broaden it.
            </span>
          </div>

          <div className="form-group">
            <label>Custom Focus & Directives (Optional)</label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="e.g. Focus on ground effect aerodynamics, hybrid ERS energy deployment, and telemetry strategy..."
              className="textarea-input"
              rows={2}
            />
          </div>

          {errorMsg && <div className="error-banner">{errorMsg}</div>}

          {!plan && (
            <button
              className="btn btn-primary btn-expand-generate"
              onClick={handleGeneratePlan}
              disabled={isGenerating || !targetPath.trim()}
            >
              {isGenerating ? (
                <>
                  <Loader2 size={15} className="spinner-icon" />
                  <span>Synthesizing Curriculum Plan...</span>
                </>
              ) : (
                <>
                  <Sparkles size={15} />
                  <span>Generate Curriculum Plan (AI)</span>
                </>
              )}
            </button>
          )}

          {plan && (
            <div className="ai-plan-preview">
              <div className="plan-header">
                <div className="plan-title-group">
                  <BookOpen size={16} className="plan-icon" />
                  <h4>{plan.course_title}</h4>
                </div>
                <span className="plan-badge">
                  {plan.domain} / {plan.discipline} / {plan.course}
                </span>
              </div>

              <div className="plan-units-list">
                {plan.units.map((unit, idx) => (
                  <div key={idx} className={`plan-unit-row ${unit.selected ? 'selected' : 'unselected'}`}>
                    <input
                      type="checkbox"
                      checked={unit.selected !== false}
                      onChange={() => handleToggleUnit(idx)}
                      className="unit-checkbox"
                    />
                    <div className="unit-info">
                      <input
                        type="text"
                        value={unit.title}
                        onChange={(e) => handleTitleChange(idx, e.target.value)}
                        className="unit-title-edit"
                      />
                      {unit.description && <p className="unit-desc">{unit.description}</p>}
                    </div>
                  </div>
                ))}
              </div>

              <div className="plan-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => setPlan(null)}
                  disabled={isApplying}
                >
                  Regenerate
                </button>

                <button
                  className="btn btn-primary"
                  onClick={handleApplyPlan}
                  disabled={isApplying}
                >
                  {isApplying ? (
                    <>
                      <Loader2 size={15} className="spinner-icon" />
                      <span>Creating & Committing to Gitea...</span>
                    </>
                  ) : (
                    <>
                      <Check size={15} />
                      <span>Apply & Commit to Gitea</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

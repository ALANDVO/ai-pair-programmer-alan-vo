import React from 'react';
import { RefactorPlan } from '../types';

interface DiffViewerProps {
  plan: RefactorPlan | null;
  onApply: (planId: string, confirm: boolean) => void;
  isApplying: boolean;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ plan, onApply, isApplying }) => {
  if (!plan) {
    return (
      <div className="card">
        <h2 className="card-title">Diff & Impact Inspector</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          No active refactoring plan. Enter a task and click "Synthesize Refactor Plan" to inspect generated diffs and AST side-effect analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        <span>Plan: {plan.plan_id}</span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <span className={`badge ${plan.ast_valid ? 'badge-green' : 'badge-amber'}`}>
            {plan.ast_valid ? 'AST Valid' : 'Syntax Warning'}
          </span>
          <span className="badge badge-blue">Impact: {plan.estimated_impact}</span>
        </div>
      </div>

      <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>{plan.summary}</p>

      {plan.potential_risks.length > 0 && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
          <strong>Considerations & Risks:</strong>
          <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem' }}>
            {plan.potential_risks.map((risk, idx) => (
              <li key={idx}>{risk}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="diff-container">
        {plan.steps.map((step) => (
          <div key={step.step_id} className="diff-step-card">
            <div className="diff-step-header">
              <span>[{step.action.toUpperCase()}] {step.file_path}</span>
              <span style={{ color: 'var(--text-muted)' }}>Step {step.step_id}</span>
            </div>
            <div style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {step.reason}
            </div>
            {step.unified_diff ? (
              <div className="diff-box">
                {step.unified_diff.split('\n').map((line, lIdx) => {
                  let cls = '';
                  if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-line-add';
                  else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-line-del';
                  else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) cls = 'diff-line-header';
                  return (
                    <div key={lIdx} className={cls}>
                      {line || ' '}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ padding: '0.5rem 0.75rem', fontStyle: 'italic', fontSize: '0.85rem' }}>
                No textual modifications generated.
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onApply(plan.plan_id, false)}
          disabled={isApplying}
        >
          {isApplying ? 'Testing...' : 'Verify Dry-Run'}
        </button>
        <button
          type="button"
          className="btn btn-success"
          onClick={() => onApply(plan.plan_id, true)}
          disabled={isApplying || !plan.ast_valid}
        >
          {isApplying ? 'Applying...' : 'Apply Plan to Codebase'}
        </button>
      </div>
    </div>
  );
};

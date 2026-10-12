import React from 'react';
import { BenchmarkSummary } from '../types';

interface BenchmarkPanelProps {
  benchmark: BenchmarkSummary | null;
  onRun: () => void;
  isLoading: boolean;
}

export const BenchmarkPanel: React.FC<BenchmarkPanelProps> = ({ benchmark, onRun, isLoading }) => {
  return (
    <div className="card">
      <div className="card-title">
        <span>AI / Machine Learning Evaluation Baseline</span>
        <button className="btn btn-primary" onClick={onRun} disabled={isLoading}>
          {isLoading ? 'Running Benchmark...' : 'Run Benchmark Suite'}
        </button>
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
        Empirical evaluation comparing synthesized refactoring diffs against AST validity,
        syntax invariants, and dependency side-effect recall.
      </p>

      {benchmark && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-val">{(benchmark.valid_syntax_rate * 100).toFixed(0)}%</div>
              <div className="metric-lbl">Syntax Validity</div>
            </div>
            <div className="metric-card">
              <div className="metric-val">{(benchmark.ast_parse_rate * 100).toFixed(0)}%</div>
              <div className="metric-lbl">AST Parse Rate</div>
            </div>
            <div className="metric-card">
              <div className="metric-val">{(benchmark.dependency_recall_rate * 100).toFixed(0)}%</div>
              <div className="metric-lbl">Dependency Recall</div>
            </div>
            <div className="metric-card">
              <div className="metric-val">{benchmark.average_score.toFixed(2)}</div>
              <div className="metric-lbl">Mean Benchmark Score</div>
            </div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Task ID</th>
                <th>Benchmark Name</th>
                <th>Syntax Valid</th>
                <th>AST Parsed</th>
                <th>Impact Detected</th>
                <th>Time (ms)</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {benchmark.results.map((res) => (
                <tr key={res.task_id}>
                  <td><code>{res.task_id}</code></td>
                  <td>{res.name}</td>
                  <td>
                    <span className={`badge ${res.syntactically_valid ? 'badge-green' : 'badge-amber'}`}>
                      {res.syntactically_valid ? 'Pass' : 'Fail'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${res.ast_parse_success ? 'badge-green' : 'badge-amber'}`}>
                      {res.ast_parse_success ? 'Pass' : 'Fail'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${res.dependency_impact_detected ? 'badge-green' : 'badge-amber'}`}>
                      {res.dependency_impact_detected ? 'Detected' : 'Missed'}
                    </span>
                  </td>
                  <td>{res.execution_time_ms}</td>
                  <td><strong>{res.score.toFixed(2)}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};

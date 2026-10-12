import React, { useState, useEffect } from 'react';
import { TaskForm } from './TaskForm';
import { DiffViewer } from './DiffViewer';
import { ContextInspector } from './ContextInspector';
import { BenchmarkPanel } from './BenchmarkPanel';
import { apiClient } from '../api/client';
import {
  RefactorPlan,
  RefactorRequest,
  CodebaseIndex,
  BenchmarkSummary
} from '../types';

interface DashboardProps {
  activeTab: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ activeTab }) => {
  const [plan, setPlan] = useState<RefactorPlan | null>(null);
  const [index, setIndex] = useState<CodebaseIndex | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [idx, bench] = await Promise.all([
        apiClient.getIndex('.', 15),
        apiClient.getBenchmark()
      ]);
      setIndex(idx);
      setBenchmark(bench);
    } catch (err: any) {
      setMessage({ text: `Failed to load initial data: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSubmit = async (req: RefactorRequest) => {
    try {
      setLoading(true);
      setMessage(null);
      const newPlan = await apiClient.createPlan(req);
      setPlan(newPlan);
      setMessage({
        text: `Plan synthesized successfully (${newPlan.steps.length} step(s)). AST verified.`,
        type: 'success'
      });
    } catch (err: any) {
      setMessage({ text: `Plan synthesis failed: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPlan = async (planId: string, confirm: boolean) => {
    try {
      setLoading(true);
      setMessage(null);
      const result = await apiClient.applyPlan({ plan_id: planId, confirm });
      setMessage({ text: result.message, type: 'success' });
    } catch (err: any) {
      setMessage({ text: `Apply failed: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const res = await apiClient.evaluateBenchmark();
      setBenchmark(res);
      setMessage({
        text: `Benchmark completed. Score: ${(res.average_score * 100).toFixed(0)}% across ${res.total_tasks} tasks.`,
        type: 'success'
      });
    } catch (err: any) {
      setMessage({ text: `Benchmark error: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {message && (
        <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
          {message.text}
        </div>
      )}

      {activeTab === 'workspace' && (
        <div className="grid-workspace">
          <TaskForm onSubmit={handlePlanSubmit} isLoading={loading} />
          <DiffViewer plan={plan} onApply={handleApplyPlan} isApplying={loading} />
        </div>
      )}

      {activeTab === 'context' && (
        <ContextInspector
          index={index}
          onRefresh={loadInitialData}
          isLoading={loading}
        />
      )}

      {activeTab === 'benchmark' && (
        <BenchmarkPanel
          benchmark={benchmark}
          onRun={handleRunBenchmark}
          isLoading={loading}
        />
      )}
    </div>
  );
};

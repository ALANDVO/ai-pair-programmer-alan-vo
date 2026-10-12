import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { apiClient } from './api/client';
import { StatsResponse, AuthUser } from './types';
import './styles.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'workspace' | 'context' | 'benchmark'>('workspace');
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [profile, setProfile] = useState<AuthUser | null>(null);

  useEffect(() => {
    apiClient.getStats()
      .then(setStats)
      .catch((err) => console.error('Failed to fetch stats:', err));

    apiClient.getProfile()
      .then(setProfile)
      .catch((err) => console.error('Failed to fetch profile:', err));
  }, []);

  return (
    <div className="app-container">
      <Navbar
        version={stats?.version || '1.0.0'}
        offlineReady={stats?.offline_engine_available ?? true}
        demoUser={profile?.username || 'local_user'}
      />

      <nav className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'workspace' ? 'active' : ''}`}
          onClick={() => setActiveTab('workspace')}
        >
          Refactoring Workspace
        </button>
        <button
          className={`tab-btn ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          Codebase Context Tree
        </button>
        <button
          className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmark')}
        >
          AI/ML Evaluation Suite
        </button>
      </nav>

      <main className="main-content">
        <Dashboard activeTab={activeTab} />
      </main>

      <footer className="footer">
        Built by Alan Vo (alanvo@gmail.com) | AI, Machine Learning & AST Refactoring Engine
      </footer>
    </div>
  );
};

export default App;

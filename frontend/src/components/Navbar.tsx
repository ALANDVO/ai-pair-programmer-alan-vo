import React from 'react';

interface NavbarProps {
  version: string;
  offlineReady: boolean;
  demoUser: string;
}

export const Navbar: React.FC<NavbarProps> = ({ version, offlineReady, demoUser }) => {
  return (
    <header className="navbar">
      <div className="brand-section">
        <h1 className="brand-title">AI Pair Programmer</h1>
        <span className="author-pill">Alan Vo | AI & Machine Learning</span>
        <span className="badge badge-blue">v{version}</span>
      </div>
      <div className="nav-controls">
        {offlineReady && <span className="badge badge-green">Offline AST Engine Active</span>}
        <span className="badge badge-amber">Demo Auth: {demoUser}</span>
      </div>
    </header>
  );
};

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { CreateCase } from './pages/CreateCase';
import { CaseWorkspace } from './pages/CaseWorkspace';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-court-dark text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create" element={<CreateCase />} />
            <Route path="/cases/:caseId" element={<CaseWorkspace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

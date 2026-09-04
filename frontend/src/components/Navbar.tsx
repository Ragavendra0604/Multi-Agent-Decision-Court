import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Scale, PlusCircle, LayoutDashboard, Shield, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'New Decision Case', path: '/create', icon: PlusCircle },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Scale className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="font-bold text-lg text-white flex items-center gap-2">
              Multi-Agent Decision Court
              <span className="text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-500/30">
                MADC v0.1
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Decision Validation & Evidence Graph Platform</p>
          </div>
        </Link>

        <nav className="flex items-center gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}

          <div className="h-4 w-px bg-slate-800 mx-2" />

          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full text-xs font-mono text-emerald-400">
            <Activity className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
            Court Active
          </div>
        </nav>
      </div>
    </header>
  );
};

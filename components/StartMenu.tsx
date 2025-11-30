import React, { useState, useRef, useEffect } from 'react';

interface StartMenuProps {
  onSelect: (view: 'calculator' | 'theory' | 'settings' | 'about') => void;
  currentView: string;
}

const StartMenu: React.FC<StartMenuProps> = ({ onSelect, currentView }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (view: 'calculator' | 'theory' | 'settings' | 'about') => {
    onSelect(view);
    setIsOpen(false);
  };

  const MenuItem = ({ view, label, icon }: { view: any, label: string, icon: React.ReactNode }) => (
    <button
      onClick={() => handleSelect(view)}
      className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-slate-100 transition-colors ${currentView === view ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-700'}`}
    >
      <div className={`p-1.5 rounded-md ${currentView === view ? 'bg-blue-200' : 'bg-slate-200'} text-slate-600`}>
        {icon}
      </div>
      <span>{label}</span>
    </button>
  );

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all shadow-sm ${isOpen ? 'bg-slate-800 text-white shadow-inner' : 'bg-white text-slate-800 hover:bg-slate-50'}`}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
        <span>Menu</span>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-white/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-50 animate-fade-in-down origin-top-left">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Applications</span>
          </div>
          
          <div className="py-2">
            <MenuItem 
              view="calculator" 
              label="Calculator" 
              icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} 
            />
            <MenuItem 
              view="theory" 
              label="Hydrology Theory" 
              icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>} 
            />
          </div>

          <div className="px-4 py-2 bg-slate-50 border-y border-slate-100">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">System</span>
          </div>

          <div className="py-2">
            <MenuItem 
              view="settings" 
              label="Options & Settings" 
              icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>} 
            />
            <MenuItem 
              view="about" 
              label="About Us" 
              icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} 
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default StartMenu;
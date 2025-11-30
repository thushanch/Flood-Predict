import React from 'react';

const Settings: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto bg-white/95 backdrop-blur rounded-xl shadow-xl border border-white p-8 animate-fade-in-up mt-10">
      <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
        <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
        Options & Settings
      </h2>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
          <div>
             <h3 className="font-semibold text-slate-800">Unit System</h3>
             <p className="text-sm text-slate-500">Select the measurement system for discharge (Flow).</p>
          </div>
          <select className="bg-white border border-slate-300 text-slate-700 text-sm rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500">
             <option>Metric (m³/s)</option>
             <option>Imperial (ft³/s)</option>
          </select>
        </div>

        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
          <div>
             <h3 className="font-semibold text-slate-800">Default Confidence Interval</h3>
             <p className="text-sm text-slate-500">Confidence level for statistical bounds.</p>
          </div>
          <select className="bg-white border border-slate-300 text-slate-700 text-sm rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500">
             <option>95%</option>
             <option>90%</option>
             <option>99%</option>
          </select>
        </div>

        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 opacity-75">
          <div>
             <h3 className="font-semibold text-slate-800">Theme</h3>
             <p className="text-sm text-slate-500">Application visual appearance.</p>
          </div>
          <div className="flex items-center space-x-2 bg-white p-1 rounded-lg border border-slate-300">
             <button className="px-3 py-1 bg-slate-200 rounded text-xs font-bold text-slate-700">Light</button>
             <button className="px-3 py-1 text-xs font-bold text-slate-400 cursor-not-allowed">Dark</button>
          </div>
        </div>
      </div>
      
      <div className="mt-8 text-center">
         <button className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition">
           Save Changes
         </button>
      </div>
    </div>
  );
};

export default Settings;
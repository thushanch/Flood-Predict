import React from 'react';

const About: React.FC = () => {
  return (
    <div className="max-w-2xl mx-auto bg-white/95 backdrop-blur rounded-xl shadow-xl border border-white p-8 text-center animate-fade-in-up mt-10">
      <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-bold text-4xl shadow-lg mx-auto mb-6">
        H
      </div>
      
      <h2 className="text-3xl font-bold text-slate-900 mb-2">HydroStat</h2>
      <p className="text-slate-500 font-mono mb-8">Version 2.0.0</p>

      <p className="text-slate-700 leading-relaxed mb-8">
        HydroStat is a professional-grade Flood Frequency Analysis tool designed for hydrologists, civil engineers, and environmental scientists. It bridges the gap between raw data collection and statistical decision-making by automating Annual Maxima Series extraction and fitting complex probability distributions.
      </p>

      <div className="grid grid-cols-3 gap-4 text-sm border-t border-slate-100 pt-8">
        <div>
          <h4 className="font-bold text-slate-900">Developed By</h4>
          <p className="text-slate-500">HydroStat Team</p>
        </div>
        <div>
          <h4 className="font-bold text-slate-900">License</h4>
          <p className="text-slate-500">MIT Open Source</p>
        </div>
        <div>
          <h4 className="font-bold text-slate-900">Support</h4>
          <p className="text-slate-500">docs.hydrostat.io</p>
        </div>
      </div>

      <div className="mt-8 pt-8 border-t border-slate-100">
         <p className="text-xs text-slate-400">
           Powered by React, Recharts, and Google Gemini AI.
         </p>
      </div>
    </div>
  );
};

export default About;
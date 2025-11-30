import React, { useState, useEffect } from 'react';
import DataUploader from './components/DataUploader';
import ManualDataEntry from './components/ManualDataEntry';
import FloodFrequencyChart from './components/FloodFrequencyChart';
import GeminiReport from './components/GeminiReport';
import StartMenu from './components/StartMenu';
import Theory from './components/Theory';
import Settings from './components/Settings';
import About from './components/About';
import { convertToAMS } from './utils/dataProcessor';
import { performAnalysis } from './utils/statistics';
import { AnalysisResult, DistributionType, TimeGranularity } from './types';

type ViewType = 'calculator' | 'theory' | 'settings' | 'about';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('calculator');
  const [inputMethod, setInputMethod] = useState<'upload' | 'manual'>('upload');
  
  const [rawData, setRawData] = useState<any[] | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [fileName, setFileName] = useState<string>('');
  
  // Configuration State
  const [dateCol, setDateCol] = useState<string>('');
  const [valCol, setValCol] = useState<string>('');
  const [granularity, setGranularity] = useState<TimeGranularity>(TimeGranularity.ANNUAL);
  const [distribution, setDistribution] = useState<DistributionType>(DistributionType.GUMBEL);
  
  // Results
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleDataLoaded = (data: any[], name: string) => {
    setRawData(data);
    setFileName(name);
    if (data.length > 0) {
      const cols = Object.keys(data[0]);
      setHeaders(cols);
      // Auto-guess columns
      const dateGuess = cols.find(c => c.toLowerCase().includes('date') || c.toLowerCase().includes('year'));
      const valGuess = cols.find(c => c.toLowerCase().includes('val') || c.toLowerCase().includes('flow') || c.toLowerCase().includes('peak') || c.toLowerCase().includes('discharge'));
      if (dateGuess) setDateCol(dateGuess);
      if (valGuess) setValCol(valGuess);
    }
  };

  useEffect(() => {
    if (rawData && dateCol && valCol) {
      try {
        const ams = convertToAMS(rawData, dateCol, valCol, granularity);
        if (ams.length > 0) {
          const analysis = performAnalysis(ams, distribution);
          setResult(analysis);
        }
      } catch (e) {
        console.error("Analysis failed", e);
      }
    }
  }, [rawData, dateCol, valCol, granularity, distribution]);

  // Render the Calculator Content (The main app logic)
  const renderCalculator = () => (
    <div className="space-y-8 animate-fade-in-up">
      {/* Intro Section / Data Input */}
      {!rawData && (
        <div className="max-w-3xl mx-auto mt-10">
          <div className="bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl border border-white/50 text-center">
            <h2 className="text-4xl font-bold text-slate-900 mb-4 tracking-tight">Flood Frequency Analysis</h2>
            <p className="text-slate-600 mb-8 text-lg leading-relaxed">
              Advanced hydrological modeling for professionals. Upload streamflow data or enter manually to fit 
              <span className="font-semibold text-blue-700"> Gumbel, Log-Pearson III, Normal, or Weibull </span> 
              distributions and predict extreme events.
            </p>
            
            <div className="bg-slate-100/80 p-1 rounded-xl inline-flex mb-8 mx-auto shadow-inner">
               <button 
                 onClick={() => setInputMethod('upload')}
                 className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${inputMethod === 'upload' ? 'bg-white text-blue-700 shadow-md transform scale-105' : 'text-slate-500 hover:text-slate-700'}`}
               >
                 Upload CSV
               </button>
               <button 
                 onClick={() => setInputMethod('manual')}
                 className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${inputMethod === 'manual' ? 'bg-white text-blue-700 shadow-md transform scale-105' : 'text-slate-500 hover:text-slate-700'}`}
               >
                 Manual Entry
               </button>
            </div>

            <div>
              {inputMethod === 'upload' ? (
                <DataUploader onDataLoaded={handleDataLoaded} />
              ) : (
                <ManualDataEntry onDataLoaded={handleDataLoaded} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Configuration Panel & Results */}
      {rawData && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Sidebar Controls */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white/90 backdrop-blur p-5 rounded-xl border border-white shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-800">Settings</h3>
                <button onClick={() => setRawData(null)} className="text-xs text-red-500 hover:underline font-semibold">New Analysis</button>
              </div>
              
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wide">Input Granularity</label>
                  <select 
                    value={granularity}
                    onChange={(e) => setGranularity(e.target.value as TimeGranularity)}
                    className="w-full p-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                  >
                    {Object.values(TimeGranularity).map(g => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wide">Statistical Model</label>
                  <select 
                    value={distribution}
                    onChange={(e) => setDistribution(e.target.value as DistributionType)}
                    className="w-full p-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                  >
                    {Object.values(DistributionType).map(d => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                  <p className="text-[10px] text-slate-400 mt-1 px-1">
                    Select the distribution that best fits your regional data.
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-100">
                  <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wide">Map Columns</label>
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-slate-400 block mb-1">Date/Year Column</span>
                      <select 
                        value={dateCol}
                        onChange={(e) => setDateCol(e.target.value)}
                        className="w-full p-2 text-sm bg-slate-50 border border-slate-300 rounded-lg"
                      >
                        <option value="">Select...</option>
                        {headers.map(h => <option key={h} value={h}>{h}</option>)}
                      </select>
                    </div>

                    <div>
                      <span className="text-xs text-slate-400 block mb-1">Flow/Value Column</span>
                      <select 
                        value={valCol}
                        onChange={(e) => setValCol(e.target.value)}
                        className="w-full p-2 text-sm bg-slate-50 border border-slate-300 rounded-lg"
                      >
                        <option value="">Select...</option>
                        {headers.map(h => <option key={h} value={h}>{h}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            {result && (
              <div className="bg-white/90 backdrop-blur p-5 rounded-xl border border-white shadow-lg">
                <h3 className="font-bold text-slate-800 mb-3 border-b border-slate-100 pb-2">Statistics</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">N (Years)</span>
                    <span className="font-mono bg-slate-100 px-2 rounded text-slate-700">{result.stats.n}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Mean</span>
                    <span className="font-mono text-slate-700">{result.stats.mean.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Std Dev</span>
                    <span className="font-mono text-slate-700">{result.stats.stdDev.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Skewness</span>
                    <span className="font-mono text-slate-700">{result.stats.skew.toFixed(3)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Visualization */}
            {result ? (
              <>
                <div className="bg-white/95 backdrop-blur rounded-xl shadow-lg border border-white/50 overflow-hidden">
                   <FloodFrequencyChart result={result} distributionType={distribution} />
                </div>
                
                {/* Results Table */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                   {[10, 50, 100, 500].map(ari => {
                     const key = `q${ari}` as keyof typeof result.predictions;
                     return (
                       <div key={ari} className="bg-white/90 backdrop-blur p-4 rounded-xl border border-white shadow-md text-center transform transition hover:scale-105">
                         <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">{ari}-Year Event</div>
                         <div className="text-2xl font-bold text-blue-700 mt-1">{result.predictions[key].toFixed(1)}</div>
                         <div className="text-xs text-slate-400 mt-1">m³/s</div>
                       </div>
                     )
                   })}
                </div>

                {/* Gemini Integration */}
                <GeminiReport result={result} distribution={distribution} />
              </>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center bg-white/50 backdrop-blur rounded-xl border-2 border-dashed border-slate-300 text-slate-500">
                <svg className="w-12 h-12 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <span>Upload data and map columns to view analysis</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div 
      className="min-h-screen bg-cover bg-center bg-fixed bg-no-repeat"
      style={{ 
        backgroundImage: `url('https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=2574&auto=format&fit=crop')`,
      }}
    >
      {/* Overlay */}
      <div className="min-h-screen w-full bg-slate-50/85 backdrop-blur-sm pb-20">
        
        {/* Header */}
        <header className="bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-20 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <StartMenu onSelect={(view) => setCurrentView(view)} currentView={currentView} />
              
              <div className="h-6 w-px bg-slate-300 hidden sm:block"></div>
              
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentView('calculator')}>
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold shadow-lg">H</div>
                <h1 className="text-xl font-bold text-slate-800 tracking-tight hidden sm:block">HydroStat</h1>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
               {currentView !== 'calculator' && (
                 <span className="text-sm font-semibold text-slate-600 bg-slate-100 px-3 py-1 rounded-md capitalize">
                   {currentView}
                 </span>
               )}
               <div className="text-xs text-slate-500 font-mono bg-slate-100 px-2 py-1 rounded">v2.0.0</div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {currentView === 'calculator' && renderCalculator()}
          {currentView === 'theory' && <Theory />}
          {currentView === 'settings' && <Settings />}
          {currentView === 'about' && <About />}
        </main>
      </div>
    </div>
  );
};

export default App;
import React, { useState, useEffect } from 'react';
import DataUploader from './components/DataUploader';
import FloodFrequencyChart from './components/FloodFrequencyChart';
import GeminiReport from './components/GeminiReport';
import { convertToAMS } from './utils/dataProcessor';
import { performAnalysis } from './utils/statistics';
import { AnalysisResult, DistributionType, TimeGranularity } from './types';

const App: React.FC = () => {
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

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">H</div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">HydroStat</h1>
          </div>
          <div className="text-xs text-slate-400 font-mono">v1.0.0</div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Intro Section */}
        {!rawData && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-slate-900 text-center mb-4">Flood Frequency Analysis</h2>
            <p className="text-slate-600 text-center mb-8">
              Professional hydrological modeling tool. Upload your streamflow time-series data to calculate Annual Recurrence Intervals (ARI) and predict flood magnitudes using Gumbel or Log-Normal distributions.
            </p>
            <DataUploader onDataLoaded={handleDataLoaded} />
          </div>
        )}

        {/* Configuration Panel */}
        {rawData && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            
            {/* Sidebar Controls */}
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-slate-800">Configuration</h3>
                  <button onClick={() => setRawData(null)} className="text-xs text-red-500 hover:underline">Reset</button>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase">Time Granularity</label>
                    <select 
                      value={granularity}
                      onChange={(e) => setGranularity(e.target.value as TimeGranularity)}
                      className="w-full p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      {Object.values(TimeGranularity).map(g => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase">Distribution Model</label>
                    <select 
                      value={distribution}
                      onChange={(e) => setDistribution(e.target.value as DistributionType)}
                      className="w-full p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      {Object.values(DistributionType).map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>

                  <div className="pt-4 border-t border-slate-100">
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase">Date Column</label>
                    <select 
                      value={dateCol}
                      onChange={(e) => setDateCol(e.target.value)}
                      className="w-full p-2 text-sm border border-slate-300 rounded-md mb-3"
                    >
                      <option value="">Select Column...</option>
                      {headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>

                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase">Value Column (Flow)</label>
                    <select 
                      value={valCol}
                      onChange={(e) => setValCol(e.target.value)}
                      className="w-full p-2 text-sm border border-slate-300 rounded-md"
                    >
                      <option value="">Select Column...</option>
                      {headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              {result && (
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                  <h3 className="font-semibold text-slate-800 mb-3">Dataset Stats</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Record Length</span>
                      <span className="font-mono">{result.stats.n} years</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Mean Flow</span>
                      <span className="font-mono">{result.stats.mean.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Max Observed</span>
                      <span className="font-mono">{Math.max(...result.ams.map(a => a.value)).toFixed(1)}</span>
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
                  <FloodFrequencyChart result={result} distributionType={distribution} />
                  
                  {/* Results Table */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                     {[10, 50, 100, 500].map(ari => {
                       const key = `q${ari}` as keyof typeof result.predictions;
                       return (
                         <div key={ari} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
                           <div className="text-xs text-slate-500 uppercase font-bold">{ari}-Year Flood</div>
                           <div className="text-2xl font-bold text-blue-600 mt-1">{result.predictions[key].toFixed(1)}</div>
                           <div className="text-xs text-slate-400 mt-1">m³/s</div>
                         </div>
                       )
                     })}
                  </div>

                  {/* Gemini Integration */}
                  <GeminiReport result={result} distribution={distribution} />
                </>
              ) : (
                <div className="h-64 flex items-center justify-center bg-white rounded-xl border border-slate-200 text-slate-400">
                  Configure columns to generate analysis
                </div>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  );
};

export default App;
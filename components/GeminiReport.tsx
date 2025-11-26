import React, { useState } from 'react';
import { GoogleGenAI } from "@google/genai";
import { AnalysisResult, DistributionType } from '../types';

interface GeminiReportProps {
  result: AnalysisResult;
  distribution: DistributionType;
}

const GeminiReport: React.FC<GeminiReportProps> = ({ result, distribution }) => {
  const [report, setReport] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    if (!process.env.API_KEY) {
      alert("Please set the API_KEY environment variable to use AI features.");
      return;
    }

    setLoading(true);
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      const statsSummary = `
        Dataset Size (Years): ${result.stats.n}
        Mean Annual Flood: ${result.stats.mean.toFixed(2)} m3/s
        Std Dev: ${result.stats.stdDev.toFixed(2)}
        Distribution Used: ${distribution}
        
        Predictions:
        10-year ARI: ${result.predictions.q10.toFixed(2)} m3/s
        50-year ARI: ${result.predictions.q50.toFixed(2)} m3/s
        100-year ARI: ${result.predictions.q100.toFixed(2)} m3/s
        500-year ARI: ${result.predictions.q500.toFixed(2)} m3/s
        
        Top 3 Recorded Events:
        ${result.ams.slice(-3).reverse().map(e => `${e.year}: ${e.value.toFixed(2)}`).join(', ')}
      `;

      const prompt = `
        Role: Senior Hydrologist.
        Task: Write a concise Flood Frequency Analysis technical summary based on the provided data.
        
        Data:
        ${statsSummary}

        Requirements:
        1. Evaluate the flood risk based on the 100-year prediction.
        2. Comment on the fit consistency given the top recorded events vs predicted values.
        3. Suggest if the dataset length (${result.stats.n} years) is sufficient for reliable 100-year estimates (Rule of thumb: need >30-40 years).
        4. Keep it professional, formatted in Markdown.
      `;

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
      });

      setReport(response.text || "No response generated.");
    } catch (error) {
      console.error("Gemini API Error:", error);
      setReport("Failed to generate report. Please check API Key and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 text-white rounded-xl p-6 shadow-xl mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold flex items-center gap-2">
           <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
           AI Hydrologist Insights
        </h3>
        {!report && (
          <button 
            onClick={generateReport}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? 'Analyzing...' : 'Generate Report'}
          </button>
        )}
      </div>

      {loading && (
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-slate-700 rounded w-3/4"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
          <div className="h-4 bg-slate-700 rounded w-5/6"></div>
        </div>
      )}

      {report && (
        <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed">
            <pre className="whitespace-pre-wrap font-sans">{report}</pre>
        </div>
      )}
    </div>
  );
};

export default GeminiReport;
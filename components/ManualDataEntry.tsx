import React, { useState } from 'react';

interface ManualDataEntryProps {
  onDataLoaded: (data: any[], fileName: string) => void;
}

type Frequency = 'Annual' | 'Monthly' | 'Daily';

const ManualDataEntry: React.FC<ManualDataEntryProps> = ({ onDataLoaded }) => {
  const [frequency, setFrequency] = useState<Frequency>('Annual');
  const [start, setStart] = useState<string>('');
  const [end, setEnd] = useState<string>('');
  const [rows, setRows] = useState<{ date: string; value: string }[]>([]);

  const generateTable = () => {
    if (!start || !end) {
      alert('Please provide both start and end times.');
      return;
    }

    const newRows: { date: string; value: string }[] = [];
    let current = new Date(start);
    const endDate = new Date(end);

    // Safety cap to prevent browser hanging
    let count = 0;
    const MAX_ROWS = 3660; // Approx 10 years of daily data

    // Handle Annual separately to ensure integer years are respected if using text inputs or date inputs
    if (frequency === 'Annual') {
      let startYear = parseInt(start);
      let endYear = parseInt(end);
      
      // Fallback if full date strings were used
      if (isNaN(startYear)) startYear = new Date(start).getFullYear();
      if (isNaN(endYear)) endYear = new Date(end).getFullYear();

      if (isNaN(startYear) || isNaN(endYear)) {
          alert("Invalid Year format");
          return;
      }

      for (let y = startYear; y <= endYear; y++) {
        newRows.push({ date: y.toString(), value: '' });
        count++;
        if (count > MAX_ROWS) break;
      }
    } else {
      // Monthly and Daily
      while (current <= endDate && count < MAX_ROWS) {
        let dateStr = '';
        if (frequency === 'Monthly') {
           // YYYY-MM
           const m = current.getMonth() + 1;
           dateStr = `${current.getFullYear()}-${m < 10 ? '0' + m : m}`;
           // Increment month
           current.setMonth(current.getMonth() + 1);
        } else {
           // Daily YYYY-MM-DD
           dateStr = current.toISOString().split('T')[0];
           // Increment day
           current.setDate(current.getDate() + 1);
        }
        newRows.push({ date: dateStr, value: '' });
        count++;
      }
    }

    if (count >= MAX_ROWS) {
        alert(`Limit reached. Truncated to ${MAX_ROWS} rows.`);
    }

    setRows(newRows);
  };

  const updateValue = (index: number, val: string) => {
    const updated = [...rows];
    updated[index].value = val;
    setRows(updated);
  };

  const handleAnalyze = () => {
    // Filter out empty rows, but keep explicit "0"
    // Warn about missing or N/A?
    // The data processor handles N/A via isNaN check, but let's clean up slightly.
    const cleanData = rows.map(r => ({
      Date: r.date,
      Flow: r.value.trim() === '' || r.value.toUpperCase() === 'N/A' ? 'N/A' : r.value
    }));
    
    // Pass data back
    onDataLoaded(cleanData, 'Manual_Input_Data');
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="mb-6 border-b border-slate-100 pb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">Table Generator</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Interval</label>
            <select 
              value={frequency}
              onChange={(e) => setFrequency(e.target.value as Frequency)}
              className="w-full p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="Annual">Annual (Yearly)</option>
              <option value="Monthly">Monthly</option>
              <option value="Daily">Daily</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Start {frequency === 'Annual' ? 'Year' : 'Date'}</label>
            <input 
              type={frequency === 'Annual' ? "number" : "date"}
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="w-full p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder={frequency === 'Annual' ? "e.g. 1990" : ""}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">End {frequency === 'Annual' ? 'Year' : 'Date'}</label>
            <input 
              type={frequency === 'Annual' ? "number" : "date"}
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="w-full p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder={frequency === 'Annual' ? "e.g. 2023" : ""}
            />
          </div>

          <button 
            onClick={generateTable}
            className="px-4 py-2 bg-slate-800 text-white rounded-md text-sm font-medium hover:bg-slate-700 transition"
          >
            Create Table
          </button>
        </div>
      </div>

      {rows.length > 0 ? (
        <>
          <div className="mb-2 flex justify-between items-center">
            <span className="text-xs text-slate-500 italic">
              * Enter flow values below. Use <span className="font-bold text-slate-700">N/A</span> for missing data.
            </span>
            <span className="text-xs text-slate-400">{rows.length} rows generated</span>
          </div>

          <div className="max-h-[400px] overflow-y-auto border border-slate-200 rounded-lg">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 sticky top-0 z-10 shadow-sm">
                <tr>
                  <th className="px-4 py-3 font-semibold text-slate-600 border-b border-slate-200 w-1/2">Date / Year</th>
                  <th className="px-4 py-3 font-semibold text-slate-600 border-b border-slate-200 w-1/2">Peak Flow (m³/s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-4 py-2 text-slate-700 font-mono">{row.date}</td>
                    <td className="px-4 py-2">
                      <input 
                        type="text" 
                        value={row.value}
                        onChange={(e) => updateValue(idx, e.target.value)}
                        placeholder="N/A"
                        className="w-full p-1 border border-transparent hover:border-slate-300 focus:border-blue-500 rounded outline-none transition-colors bg-transparent"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex justify-end">
            <button 
              onClick={handleAnalyze}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition shadow-sm flex items-center gap-2"
            >
              Analyze Data
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-slate-400 bg-slate-50/50 rounded-lg border border-dashed border-slate-200">
          <p>Configure the parameters above to generate a data entry table.</p>
        </div>
      )}
    </div>
  );
};

export default ManualDataEntry;
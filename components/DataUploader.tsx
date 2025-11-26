import React from 'react';

interface DataUploaderProps {
  onDataLoaded: (data: any[], fileName: string) => void;
}

const DataUploader: React.FC<DataUploaderProps> = ({ onDataLoaded }) => {
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const { parseCSV } = await import('../utils/dataProcessor');
      
      try {
        const data = await parseCSV(file);
        onDataLoaded(data, file.name);
      } catch (err) {
        console.error("Error parsing CSV", err);
        alert("Failed to parse CSV. Please ensure it is a valid CSV file.");
      }
    }
  };

  return (
    <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100 transition-colors">
      <div className="flex flex-col items-center gap-3">
        <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <div>
          <h3 className="text-lg font-semibold text-slate-700">Upload Hydrological Data</h3>
          <p className="text-sm text-slate-500 mt-1">Supports CSV with Hourly, Daily, Monthly, or Annual records</p>
        </div>
        
        <label className="mt-4 cursor-pointer inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition">
          <span>Select File</span>
          <input type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
        </label>
      </div>
    </div>
  );
};

export default DataUploader;
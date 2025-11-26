import { AnnualMaxima, RawDataPoint, TimeGranularity } from '../types';

export const parseCSV = async (file: File): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const lines = text.split(/\r?\n/).filter(line => line.trim() !== '');
      if (lines.length < 2) {
        reject(new Error("File is empty or invalid"));
        return;
      }
      
      const headers = lines[0].split(',').map(h => h.trim());
      const data = lines.slice(1).map(line => {
        const values = line.split(',');
        const obj: any = {};
        headers.forEach((h, i) => {
          obj[h] = values[i]?.trim();
        });
        return obj;
      });
      resolve(data);
    };
    reader.onerror = (error) => reject(error);
    reader.readAsText(file);
  });
};

/**
 * Core Logic: Converts raw input into Annual Maxima Series
 * Handles:
 * 1. Annual (Year, Peak) -> Direct mapping
 * 2. Monthly/Daily/Hourly -> Group by Year, Find Max
 */
export const convertToAMS = (
  data: any[],
  dateCol: string,
  valCol: string,
  granularity: TimeGranularity
): AnnualMaxima[] => {
  const yearlyMax = new Map<number, number>();

  data.forEach(row => {
    const valStr = row[valCol];
    const dateStr = row[dateCol];

    if (!valStr || !dateStr) return;

    let year: number | null = null;
    let value = parseFloat(valStr);

    if (isNaN(value)) return;

    // Year Extraction Logic
    if (granularity === TimeGranularity.ANNUAL) {
      // Input might be just "1990" or a full date
      if (dateStr.length === 4 && !isNaN(parseInt(dateStr))) {
        year = parseInt(dateStr);
      } else {
        const d = new Date(dateStr);
        if (!isNaN(d.getTime())) year = d.getFullYear();
      }
    } else {
      // For Monthly, Daily, Hourly - we parse the date
      // Try standard Date constructor
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        year = d.getFullYear();
      } else {
        // Fallback for some excel formats or DD/MM/YYYY if needed?
        // Assuming standard ISO or US format for simplicity in this demo
        // Simple regex for YYYY at start
        const match = dateStr.match(/^(\d{4})/);
        if (match) year = parseInt(match[1]);
      }
    }

    if (year !== null) {
      const currentMax = yearlyMax.get(year) || -Infinity;
      if (value > currentMax) {
        yearlyMax.set(year, value);
      }
    }
  });

  const ams: AnnualMaxima[] = Array.from(yearlyMax.entries())
    .map(([year, value]) => ({ year, value }))
    .sort((a, b) => a.year - b.year); // Sort chronologically

  return ams;
};
import React from 'react';
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { AnalysisResult, DistributionType } from '../types';

interface ChartProps {
  result: AnalysisResult;
  distributionType: DistributionType;
}

const FloodFrequencyChart: React.FC<ChartProps> = ({ result, distributionType }) => {
  // Merge AMS points and Curve points into a format Recharts handles well
  // Ideally, we plot them as two separate data series on the same axis
  // Scatter expects {x, y}
  
  const scatterData = result.ams.map(p => ({
    x: p.returnPeriod || 0,
    y: p.value,
    year: p.year
  }));

  const curveData = result.curve.map(c => ({
    x: c.returnPeriod,
    curveY: c.discharge
  }));

  // Log scale domain tweaking
  const maxDischarge = Math.max(
    ...result.ams.map(d => d.value),
    ...result.curve.map(d => d.discharge)
  );
  
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-slate-200 shadow-lg rounded text-sm">
          <p className="font-bold text-slate-700 mb-1">Return Period: {Number(label).toFixed(1)} years</p>
          {payload.map((entry: any, idx: number) => (
            <p key={idx} style={{ color: entry.color }}>
              {entry.name}: {Number(entry.value).toFixed(2)} m³/s
              {entry.payload.year && <span className="text-slate-400 ml-2">({entry.payload.year})</span>}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-[500px] bg-white rounded-xl shadow-sm border border-slate-200 p-4">
      <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <span className="w-3 h-3 rounded-full bg-blue-500"></span>
        Return Period vs. Discharge
      </h3>
      
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          
          <XAxis 
            dataKey="x" 
            type="number" 
            scale="log" 
            domain={[1.01, 1000]}
            allowDataOverflow
            tickCount={8}
            ticks={[1.01, 2, 5, 10, 25, 50, 100, 200, 500, 1000]}
            label={{ value: 'Return Period (Years)', position: 'insideBottom', offset: -10, fill: '#64748b' }}
            tickFormatter={(val) => val >= 100 ? val.toFixed(0) : val.toFixed(1)}
            stroke="#94a3b8"
          />
          
          <YAxis 
            label={{ value: 'Discharge (m³/s)', angle: -90, position: 'insideLeft', offset: 0, fill: '#64748b' }}
            domain={[0, Math.ceil(maxDischarge * 1.1)]}
            stroke="#94a3b8"
          />
          
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />

          {/* The Fitted Curve */}
          <Line 
            data={curveData} 
            dataKey="curveY" 
            name={`${distributionType} Fit`} 
            stroke="#2563eb" 
            strokeWidth={3} 
            dot={false}
            type="monotone"
            isAnimationActive={true}
          />

          {/* The Observed Data Points */}
          <Scatter 
            data={scatterData} 
            name="Observed AMS" 
            fill="#0ea5e9" 
            fillOpacity={0.6}
            stroke="#0284c7"
          />
          
          {/* Reference Lines for common ARIs */}
          <ReferenceLine x={100} stroke="red" strokeDasharray="3 3" label={{ value: "100yr", fill: "red", fontSize: 12 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FloodFrequencyChart;
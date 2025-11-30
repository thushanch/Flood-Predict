import React from 'react';

const Theory: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto bg-white/95 backdrop-blur rounded-xl shadow-xl border border-white p-8 animate-fade-in-up">
      <h2 className="text-3xl font-bold text-slate-900 mb-6 flex items-center gap-3">
        <span className="bg-blue-100 text-blue-700 p-2 rounded-lg">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        </span>
        Hydrological Frequency Analysis
      </h2>
      
      <div className="prose prose-slate max-w-none">
        <h3 className="text-xl font-semibold text-slate-800 border-b border-slate-200 pb-2 mb-4">1. Annual Maxima Series (AMS)</h3>
        <p className="mb-4">
          The foundation of Flood Frequency Analysis (FFA) is the independence of data points. HydroStat converts raw continuous data (hourly, daily) into an <strong>Annual Maxima Series</strong> by extracting the single peak discharge (Q<sub>max</sub>) for each hydrological year.
        </p>
        
        <h3 className="text-xl font-semibold text-slate-800 border-b border-slate-200 pb-2 mb-4 mt-8">2. Statistical Distributions</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-slate-50 p-5 rounded-lg border border-slate-200">
            <h4 className="font-bold text-blue-700 mb-2">Gumbel (EV1)</h4>
            <p className="text-sm text-slate-600">
              The Extreme Value Type I distribution is widely used for modeling extreme events. It assumes a constant skewness ($\approx 1.14$) and is often used for general flood modeling in Europe and parts of Asia.
              <br/><br/>
              <code className="bg-slate-200 px-1 py-0.5 rounded text-xs">x(T) = u - \alpha \ln(-\ln(1 - 1/T))</code>
            </p>
          </div>

          <div className="bg-slate-50 p-5 rounded-lg border border-slate-200">
            <h4 className="font-bold text-purple-700 mb-2">Log-Pearson Type III</h4>
            <p className="text-sm text-slate-600">
              The standard distribution for US Federal Agency flood frequency analysis (USGS Bulletin 17C). It uses three parameters (mean, standard deviation, and skew of the log-transformed data) to flexibly fit data that deviates from normality.
            </p>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-slate-800 border-b border-slate-200 pb-2 mb-4 mt-8">3. Probability & Return Period</h3>
        <p className="mb-4">
          The Return Period ($T$) is the inverse of the exceedance probability ($P$). A "100-year flood" has a 1% chance ($P=0.01$) of being equaled or exceeded in any given year.
        </p>
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
          <p className="font-mono text-blue-900 font-bold">T = 1 / P</p>
          <p className="text-sm text-blue-800 mt-1">Example: A probability of 0.01 corresponds to T = 1/0.01 = 100 years.</p>
        </div>

        <h3 className="text-xl font-semibold text-slate-800 border-b border-slate-200 pb-2 mb-4 mt-8">4. Plotting Positions</h3>
        <p>
          To visualize observed data against the theoretical curve, we assign an empirical probability to each historical event based on its rank ($m$) within the total record length ($n$). HydroStat uses the <strong>Weibull Formula</strong>:
        </p>
        <div className="my-4 text-center">
            <code className="bg-slate-100 px-3 py-2 rounded text-lg border border-slate-300">P = m / (n + 1)</code>
        </div>
      </div>
    </div>
  );
};

export default Theory;
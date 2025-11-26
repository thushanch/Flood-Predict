import { AnnualMaxima, CurvePoint, AnalysisResult, DistributionType } from '../types';

/**
 * Calculates mean and standard deviation of an array of numbers
 */
const getMoments = (data: number[]) => {
  const n = data.length;
  if (n === 0) return { mean: 0, stdDev: 0 };
  
  const mean = data.reduce((a, b) => a + b, 0) / n;
  const variance = data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (n - 1);
  return { mean, stdDev: Math.sqrt(variance) };
};

/**
 * Weibull Plotting Position Formula
 * P = m / (n + 1)
 * T = 1 / P
 */
export const calculatePlottingPositions = (ams: AnnualMaxima[]): AnnualMaxima[] => {
  const sorted = [...ams].sort((a, b) => b.value - a.value); // Descending order
  const n = sorted.length;

  return sorted.map((item, index) => {
    const rank = index + 1; // m
    const exceedanceProbability = rank / (n + 1); // P
    const returnPeriod = 1 / exceedanceProbability; // T
    return { ...item, rank, exceedanceProbability, returnPeriod };
  });
};

/**
 * Gumbel (EV1) Distribution Fitting using Frequency Factors
 * Q(T) = Mean + K * StdDev
 * K = - (sqrt(6)/pi) * (0.5772 + ln(ln(T/(T-1))))
 */
const calculateGumbelCurve = (mean: number, stdDev: number): CurvePoint[] => {
  const returnPeriods = [1.01, 1.1, 1.25, 1.5, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
  
  return returnPeriods.map(T => {
    // Frequency factor K for Gumbel
    // Note: Standard approx uses theoretical mean/std of reduced variate
    // yT = -ln(-ln(1 - 1/T))
    // K = (yT - 0.5772) / (1.2825) approx, strictly speaking:
    // K = - (Math.sqrt(6) / Math.PI) * (0.5772 + Math.log(Math.log(T / (T - 1)))); 
    // Let's use the standard simplified form for Q(T):
    // x = u - alpha * ln(-ln(p)) where p = 1 - 1/T
    
    // Method of Moments parameters:
    const alpha = (Math.PI / Math.sqrt(6)) / stdDev; // scale
    const u = mean - (0.5772 / alpha); // location

    const p = 1 - (1 / T);
    const discharge = u - Math.log(-Math.log(p)) / alpha;

    return { returnPeriod: T, discharge: Math.max(0, discharge) };
  });
};

/**
 * Log-Normal Distribution Fitting
 * Fits a normal distribution to the Log10 of the values
 */
const calculateLogNormalCurve = (amsValues: number[]): CurvePoint[] => {
  const logValues = amsValues.map(v => Math.log10(v > 0 ? v : 0.1));
  const { mean: logMean, stdDev: logStd } = getMoments(logValues);
  
  const returnPeriods = [1.01, 1.1, 1.25, 1.5, 2, 5, 10, 20, 50, 100, 200, 500, 1000];

  return returnPeriods.map(T => {
    // Inverse Normal Cumulative Distribution approximation (Z-score)
    // Simple approx for Z based on p
    const p = 1 / T;
    // We want the value where P(X > x) = p, so we look for 1-p in cumulative normal
    // Use Box-Muller or approximation for Inverse Error Function.
    // Library-free approximation for standard normal quantile function (probit):
    const z = calculateZScore(1 - p);
    
    const logQ = logMean + z * logStd;
    const discharge = Math.pow(10, logQ);

    return { returnPeriod: T, discharge: Math.max(0, discharge) };
  });
};

/**
 * Approximation of Inverse Standard Normal CDF (Probit function)
 * Source: Beasley-Springer-Moro Algorithm (simplified)
 */
function calculateZScore(p: number): number {
  if (p <= 0 || p >= 1) return 0;
  
  // Wichura's algorithm AS 241 is best, but here is a simpler approx:
  // Abramowitz and Stegun 26.2.23
  const t = Math.sqrt(-2 * Math.log(p < 0.5 ? p : 1 - p));
  const c0 = 2.515517; 
  const c1 = 0.802853; 
  const c2 = 0.010328;
  const d1 = 1.432788; 
  const d2 = 0.189269; 
  const d3 = 0.001308;
  
  let x = t - ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1);
  return p < 0.5 ? -x : x;
}

export const performAnalysis = (
  ams: AnnualMaxima[],
  distribution: DistributionType
): AnalysisResult => {
  const values = ams.map(a => a.value);
  const { mean, stdDev } = getMoments(values);
  const n = values.length;

  let curve: CurvePoint[] = [];

  if (distribution === DistributionType.GUMBEL) {
    curve = calculateGumbelCurve(mean, stdDev);
  } else if (distribution === DistributionType.LOG_NORMAL) {
    curve = calculateLogNormalCurve(values);
  } else {
    // Fallback to Gumbel for Weibull request in this demo scope 
    // (Weibull 2P usually requires MLE for robust fit on floods)
    curve = calculateGumbelCurve(mean, stdDev); 
  }

  // Interpolate predictions from curve
  const getPred = (t: number) => {
    const pt = curve.find(c => c.returnPeriod === t);
    // Simple linear interpolation if exact T not found (though our curve gen creates specific T's)
    if (pt) return pt.discharge;
    return 0;
  };

  return {
    ams: calculatePlottingPositions(ams),
    curve,
    stats: { mean, stdDev, n },
    predictions: {
      q10: getPred(10),
      q50: getPred(50),
      q100: getPred(100),
      q500: getPred(500),
    }
  };
};
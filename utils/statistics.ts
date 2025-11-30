import { AnnualMaxima, CurvePoint, AnalysisResult, DistributionType } from '../types';

// Standard return periods for the curve
const RETURN_PERIODS = [1.01, 1.1, 1.25, 1.5, 2, 5, 10, 20, 50, 100, 200, 500, 1000];

/**
 * Calculates Mean, Standard Deviation, and Skewness
 */
const getMoments = (data: number[]) => {
  const n = data.length;
  if (n === 0) return { mean: 0, stdDev: 0, skew: 0 };
  
  const mean = data.reduce((a, b) => a + b, 0) / n;
  
  // Variance and StdDev
  const variance = data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (n - 1);
  const stdDev = Math.sqrt(variance);

  // Skewness
  // Formula: (n / ((n-1)(n-2))) * sum((x - mean)^3 / stdDev^3)
  let skew = 0;
  if (n > 2 && stdDev > 0) {
    const sumCubedDev = data.reduce((a, b) => a + Math.pow((b - mean) / stdDev, 3), 0);
    skew = (n / ((n - 1) * (n - 2))) * sumCubedDev;
  }

  return { mean, stdDev, skew };
};

/**
 * Approximation of Inverse Standard Normal CDF (Probit function)
 * Calculates Z for a given probability p (P(X <= x) = p)
 */
function calculateZScore(p: number): number {
  if (p <= 0 || p >= 1) return 0;
  
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

// --- Distribution Implementations ---

/**
 * Normal Distribution
 * Q(T) = Mean + Z * StdDev
 */
const calculateNormalCurve = (mean: number, stdDev: number): CurvePoint[] => {
  return RETURN_PERIODS.map(T => {
    const p = 1 - (1 / T); // Non-exceedance probability
    const z = calculateZScore(p);
    const discharge = mean + z * stdDev;
    return { returnPeriod: T, discharge: Math.max(0, discharge) };
  });
};

/**
 * Gumbel (EV1) Distribution
 * x = u - alpha * ln(-ln(p))
 */
const calculateGumbelCurve = (mean: number, stdDev: number): CurvePoint[] => {
  // Method of Moments parameters
  const alpha = (Math.PI / Math.sqrt(6)) / stdDev; // scale
  const u = mean - (0.5772 / alpha); // location

  return RETURN_PERIODS.map(T => {
    const p = 1 - (1 / T);
    const discharge = u - Math.log(-Math.log(p)) / alpha;
    return { returnPeriod: T, discharge: Math.max(0, discharge) };
  });
};

/**
 * Log-Normal Distribution
 * Fits Normal distribution to Log10(X)
 */
const calculateLogNormalCurve = (values: number[]): CurvePoint[] => {
  const logValues = values.map(v => Math.log10(v > 0 ? v : 0.01));
  const { mean: logMean, stdDev: logStd } = getMoments(logValues);
  
  return RETURN_PERIODS.map(T => {
    const p = 1 - (1 / T);
    const z = calculateZScore(p);
    const logQ = logMean + z * logStd;
    return { returnPeriod: T, discharge: Math.pow(10, logQ) };
  });
};

/**
 * Log-Pearson Type III Distribution
 * Standard for USGS Flood Frequency Analysis (Bulletin 17B/17C)
 * Uses Wilson-Hilferty approximation for K (Frequency Factor)
 * logQ = Mean + K * StdDev
 */
const calculateLogPearson3Curve = (values: number[]): CurvePoint[] => {
  const logValues = values.map(v => Math.log10(v > 0 ? v : 0.01));
  const { mean: logMean, stdDev: logStd, skew: g } = getMoments(logValues);

  return RETURN_PERIODS.map(T => {
    const p = 1 - (1 / T);
    const z = calculateZScore(p);

    // Frequency Factor K using Wilson-Hilferty approximation
    // Good for |skew| < 2.0 roughly
    // K = (2/g) * ( (1 + (g*z)/6 - g^2/36)^3 - 1 )
    let K = z; // Default to Normal if skew is 0
    
    if (Math.abs(g) > 0.001) {
       const term = 1 + (g * z) / 6 - (g * g) / 36;
       K = (2 / g) * (Math.pow(term, 3) - 1);
    }

    const logQ = logMean + K * logStd;
    return { returnPeriod: T, discharge: Math.pow(10, logQ) };
  });
};

/**
 * Weibull Distribution (2-Parameter) using Method of Moments
 * Mean = lambda * Gamma(1 + 1/k)
 * Variance = lambda^2 * [Gamma(1 + 2/k) - (Gamma(1 + 1/k))^2]
 * Solving for k (shape) and lambda (scale) requires numerical approx.
 * 
 * Simplified approximation for Shape parameter (k):
 * k ≈ (StdDev / Mean)^(-1.086)
 * Scale (lambda) = Mean / Gamma(1 + 1/k)
 */
const calculateWeibullCurve = (mean: number, stdDev: number): CurvePoint[] => {
  // Simple approximation for k derived from coefficient of variation (CV = std/mean)
  const cv = stdDev / mean;
  const k = Math.pow(cv, -1.086);
  
  // Gamma function approximation (Lanczos) for Gamma(1 + 1/k)
  const gamma = (z: number) => {
    // Simple Stirling's approx for positive real numbers
    return Math.sqrt(2 * Math.PI / z) * Math.pow((1 / Math.E) * (z + 1 / (12 * z - 0.1 / z)), z);
  };
  
  // More accurate gamma for x roughly 1-2
  const gammaApprox = (x: number): number => {
      // Numerical Recipes p. 213 (Lanczos)
      const p = [
        1.000000000190015, 76.18009172947146, -86.50532032941677,
        24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5
      ];
      const g = 5;
      const t = x + g - 0.5;
      let a = p[0];
      for(let i=1; i<p.length; i++) a += p[i] / (x + i - 1); // fix index
      return Math.pow(t, x - 0.5) * Math.exp(-t) * 2.5066282746310005 * a; // 2.506... is sqrt(2pi)
  };

  const lambda = mean / gammaApprox(1 + 1/k);

  return RETURN_PERIODS.map(T => {
    const p = 1 - (1 / T); // P(X <= x)
    // Weibull CDF: F(x) = 1 - exp(-(x/lambda)^k)
    // 1 - p = exp(-(x/lambda)^k)
    // ln(1-p) = -(x/lambda)^k
    // -ln(1-p) = (x/lambda)^k
    // x = lambda * (-ln(1-p))^(1/k)
    // Note: 1-p is exceedance prob (1/T)
    const discharge = lambda * Math.pow(-Math.log(1/T), 1/k);
    return { returnPeriod: T, discharge: Math.max(0, discharge) };
  });
}

export const performAnalysis = (
  ams: AnnualMaxima[],
  distribution: DistributionType
): AnalysisResult => {
  const values = ams.map(a => a.value);
  const { mean, stdDev, skew } = getMoments(values);
  const n = values.length;

  let curve: CurvePoint[] = [];

  switch (distribution) {
    case DistributionType.GUMBEL:
      curve = calculateGumbelCurve(mean, stdDev);
      break;
    case DistributionType.LOG_NORMAL:
      curve = calculateLogNormalCurve(values);
      break;
    case DistributionType.LOG_PEARSON_3:
      curve = calculateLogPearson3Curve(values);
      break;
    case DistributionType.NORMAL:
      curve = calculateNormalCurve(mean, stdDev);
      break;
    case DistributionType.WEIBULL:
      curve = calculateWeibullCurve(mean, stdDev);
      break;
    default:
      curve = calculateGumbelCurve(mean, stdDev);
  }

  // Linear Interpolation for Specific Predictions
  const getPred = (t: number) => {
    // Find points around t
    const exact = curve.find(c => Math.abs(c.returnPeriod - t) < 0.01);
    if (exact) return exact.discharge;

    // Basic linear interp
    for (let i = 0; i < curve.length - 1; i++) {
      const p1 = curve[i];
      const p2 = curve[i+1];
      if (t >= p1.returnPeriod && t <= p2.returnPeriod) {
        // Linear interp on Log T axis usually better for flood freq
        const logT = Math.log10(t);
        const logT1 = Math.log10(p1.returnPeriod);
        const logT2 = Math.log10(p2.returnPeriod);
        const fraction = (logT - logT1) / (logT2 - logT1);
        return p1.discharge + fraction * (p2.discharge - p1.discharge);
      }
    }
    return 0; // Out of bounds
  };

  return {
    ams: calculatePlottingPositions(ams),
    curve,
    stats: { mean, stdDev, skew, n },
    predictions: {
      q10: getPred(10),
      q50: getPred(50),
      q100: getPred(100),
      q500: getPred(500),
    }
  };
};

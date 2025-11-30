export enum DistributionType {
  GUMBEL = 'Gumbel (EV1)',
  LOG_NORMAL = 'Log-Normal',
  LOG_PEARSON_3 = 'Log-Pearson Type III',
  NORMAL = 'Normal (Gaussian)',
  WEIBULL = 'Weibull'
}

export enum TimeGranularity {
  ANNUAL = 'Annual (Year, Peak)',
  MONTHLY = 'Monthly (Year, Month, Value)',
  DAILY = 'Daily (Date, Value)',
  HOURLY = 'Hourly/TimeSeries (Datetime, Value)'
}

export interface RawDataPoint {
  date: string | Date;
  value: number;
  originalRow: any;
}

export interface AnnualMaxima {
  year: number;
  value: number;
  rank?: number;
  exceedanceProbability?: number;
  returnPeriod?: number;
}

export interface CurvePoint {
  returnPeriod: number;
  discharge: number;
}

export interface AnalysisResult {
  ams: AnnualMaxima[];
  curve: CurvePoint[];
  stats: {
    mean: number;
    stdDev: number;
    skew: number;
    n: number;
  };
  predictions: {
    q10: number;
    q50: number;
    q100: number;
    q500: number;
  };
}
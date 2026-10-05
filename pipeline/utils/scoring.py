
import numpy as np
import pandas as pd

def zscore(series: pd.Series):
    s = pd.to_numeric(series, errors="coerce")
    m = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - m) / sd

def weighted_mean(df: pd.DataFrame, cols, weights=None):
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return pd.Series([np.nan]*len(df), index=df.index)
    if weights is None:
        weights = np.ones(len(cols))
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()
    zcols = []
    for c in cols:
        z = zscore(df[c])
        zcols.append(z)
    Z = np.vstack([z.values for z in zcols]).T
    return pd.Series(np.dot(Z, weights), index=df.index)

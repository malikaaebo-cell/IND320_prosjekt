# analysis.py
# The analysis functions from the part 3 notebook, shared by the Streamlit pages:
#  - spc_outliers():       outliers with SPC on DCT high-pass filtered values (SATV)
#  - lof_anomalies():      anomalies with the Local Outlier Factor
#  - stl_decomposition():  STL of the reservoir degree of filling
#  - spectrogram():        spectrogram of the reservoir degree of filling
# See notebooks/projectwork_part3.ipynb for the explanations and tests.
# Update (part 4): the functions return interactive Plotly figures instead of matplotlib,
# and SPC/LOF work for any weather property (the label is given as an argument).
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import stft
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

from modules.theme import PRIMARY, HIGHLIGHT, MUTED


def spc_outliers(series, cutoff=25, n_std=3, label=None):
    """
    Find outliers in a time series with Statistical Process Control (SPC) on the
    DCT high-pass filtered values (SATV).

    cutoff : DCT frequency cut-off; the 'cutoff' lowest frequencies are removed
             (25 removes variations slower than about a month in one year of hourly data)
    n_std  : number of robust standard deviations between the median and the SPC limits
    label  : axis label, e.g. 'Temperature (°C)'
    Returns the Plotly figure, a summary and the outlying values.
    """
    series = series.dropna()                      # the DCT needs a complete series
    values = series.values
    label = label or series.name

    # High-pass filter: set the lowest DCT frequencies to zero and transform back
    freq = dct(values, norm='ortho')
    freq[:cutoff] = 0
    satv = idct(freq, norm='ortho')

    # Robust statistics of the SATV for the whole year: median and MAD scaled to a standard deviation
    median = np.median(satv)
    sd = median_abs_deviation(satv, scale='normal')

    # SPC limits: the removed slow variation plus median ± n_std robust standard deviations
    slow = values - satv
    upper = slow + median + n_std * sd
    lower = slow + median - n_std * sd
    is_outlier = (values > upper) | (values < lower)

    # Plot the series and the SPC limits, with the outliers highlighted
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=values, mode='lines', name=label,
                    line=dict(width=1, color=PRIMARY))
    fig.add_scatter(x=series.index, y=upper, mode='lines', name=f'SPC limits (± {n_std} robust SD)',
                    line=dict(width=1, color='#555555', dash='dash'))
    fig.add_scatter(x=series.index, y=lower, mode='lines', showlegend=False,
                    line=dict(width=1, color='#555555', dash='dash'), hoverinfo='skip')
    fig.add_scatter(x=series.index[is_outlier], y=values[is_outlier], mode='markers', name='Outliers',
                    marker=dict(color=HIGHLIGHT, size=5))
    fig.update_layout(title=f'SPC outliers in {label} (DCT cut-off {cutoff}, {n_std} SD)',
                      xaxis_title='Time (UTC)', yaxis_title=label, height=450)

    # Summary of the outliers
    outliers = series[is_outlier]
    summary = {
        'number of outliers': len(outliers),
        'share of outliers (%)': round(100 * len(outliers) / len(series), 2),
        'above upper limit': int((values > upper).sum()),
        'below lower limit': int((values < lower).sum()),
        'robust SD': round(float(sd), 3),
    }
    return fig, summary, outliers


def lof_anomalies(series, contamination=0.01, n_neighbors=20, time_step=0.01, label=None):
    """
    Find anomalies in a time series with the Local Outlier Factor (LOF) method.

    contamination : proportion of the observations marked as anomalies
    n_neighbors   : number of neighbours used to estimate the local density
    time_step     : distance between two consecutive hours on the scaled time axis
    label         : axis label, e.g. 'Temperature (°C)'
    Returns the Plotly figure, a summary and the anomalous values.
    """
    series = series.dropna()
    values = series.values
    label = label or series.name

    # Two features: scaled time index and standardised values (a constant series has std 0)
    time_index = np.arange(len(values)) * time_step
    std = values.std() if values.std() > 0 else 1
    standardised = (values - values.mean()) / std
    X = np.column_stack([time_index, standardised])

    # Fit LOF; observations labelled -1 are anomalies
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_anomaly = lof.fit_predict(X) == -1

    # Plot the series with the anomalies highlighted
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=values, mode='lines', name=label,
                    line=dict(width=1, color=PRIMARY))
    fig.add_scatter(x=series.index[is_anomaly], y=values[is_anomaly], mode='markers',
                    name='Anomalies (LOF)', marker=dict(color=HIGHLIGHT, size=6))
    fig.update_layout(title=f'LOF anomalies in {label} ({contamination:.1%} of the hours)',
                      xaxis_title='Time (UTC)', yaxis_title=label, height=450)

    # Summary of the anomalies
    anomalies = series[is_anomaly]
    summary = {
        'number of anomalies': len(anomalies),
        'share of anomalies (%)': round(100 * len(anomalies) / len(series), 2),
        'lowest anomaly': round(float(anomalies.min()), 2) if len(anomalies) else None,
        'highest anomaly': round(float(anomalies.max()), 2) if len(anomalies) else None,
    }
    return fig, summary, anomalies


def stl_decomposition(series, period=52, seasonal=13, trend=105, robust=False):
    """
    Decompose a time series into trend, seasonal and residual components with STL.

    period   : number of observations in one season (52 weeks = one year)
    seasonal : length of the seasonal smoother (odd number; higher = more stable season)
    trend    : length of the trend smoother (odd number, larger than the period; higher = smoother trend)
    robust   : True gives less weight to outliers when fitting
    Returns the Plotly figure of the decomposition.
    """
    result = STL(series.dropna(), period=period, seasonal=seasonal, trend=trend, robust=robust).fit()

    # Four panels with a shared time axis: the original series and the three components
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=['Observed', 'Trend', 'Seasonal', 'Residual'])
    for row, (component, color) in enumerate([(result.observed, PRIMARY), (result.trend, '#2A9D8F'),
                                              (result.seasonal, '#E9A03B')], start=1):
        fig.add_scatter(x=component.index, y=component.values, mode='lines', row=row, col=1,
                        line=dict(color=color, width=1.3), showlegend=False)
    fig.add_scatter(x=result.resid.index, y=result.resid.values, mode='markers', row=4, col=1,
                    marker=dict(color=MUTED, size=3), showlegend=False)
    fig.update_layout(title=f'STL of {series.name} (seasonal={seasonal}, trend={trend}, robust={robust})',
                      height=750, margin=dict(t=90))
    return fig


def spectrogram(series, window_length=104, overlap=78, samples_per_year=52):
    """
    Spectrogram of a time series using the short-time Fourier transform.

    window_length    : number of observations in each window (104 weeks = two years)
    overlap          : number of observations shared by two consecutive windows (must be < window_length)
    samples_per_year : sampling rate (52 for weekly data), gives the frequency in cycles per year
    Returns the Plotly figure.
    """
    series = series.dropna()
    # STFT; the mean of each window is removed so the constant level does not dominate
    f, t, Zxx = stft(series.values, fs=samples_per_year, nperseg=window_length,
                     noverlap=overlap, detrend='constant')

    # Time axis in years from the first date in the series; only the low frequencies (≤ 6
    # cycles per year) are shown, since that is where the variation is
    start = series.index[0].year + series.index[0].dayofyear / 365
    keep = f <= 6
    fig = go.Figure(go.Heatmap(x=start + t, y=f[keep], z=np.abs(Zxx[keep]), colorscale='Viridis',
                               colorbar=dict(title='Amplitude'),
                               hovertemplate='Year %{x:.1f}<br>%{y:.2f} cycles/year<br>Amplitude %{z:.3f}<extra></extra>'))
    fig.update_layout(title=f'Spectrogram of {series.name} (window {window_length}, overlap {overlap})',
                      xaxis_title='Year', yaxis_title='Frequency (cycles per year)', height=420)
    return fig

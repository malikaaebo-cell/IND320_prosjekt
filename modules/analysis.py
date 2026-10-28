# analysis.py
# The analysis functions from the part 3 notebook, shared by the Streamlit pages:
#  - spc_outliers():       outliers in precipitation with SPC on DCT high-pass filtered values
#  - lof_anomalies():      anomalies in temperature with the Local Outlier Factor
#  - stl_decomposition():  STL of the reservoir degree of filling
#  - spectrogram():        spectrogram of the reservoir degree of filling
# See notebooks/projectwork_part3.ipynb for the explanations and tests.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import dct, idct
from scipy.signal import stft
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


def spc_outliers(series, cutoff=25, n_std=3):
    """
    Find outliers in a time series with Statistical Process Control (SPC) on the
    DCT high-pass filtered values (SATV).

    cutoff : DCT frequency cut-off; the 'cutoff' lowest frequencies are removed
             (25 removes variations slower than about a month in one year of hourly data)
    n_std  : number of robust standard deviations between the median and the SPC limits
    Returns the plot, a summary and the outlying values.
    """
    values = series.values

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

    # Plot the series and the SPC limits, with the outliers in red
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(series.index, values, linewidth=0.6, label=series.name)
    ax.plot(series.index, upper, 'k--', linewidth=1, label=f'SPC limits (± {n_std} robust SD)')
    ax.plot(series.index, lower, 'k--', linewidth=1)
    ax.scatter(series.index[is_outlier], values[is_outlier], color='red', s=10, zorder=3, label='Outliers')
    ax.set_title(f'SPC outliers in {series.name} (DCT cut-off {cutoff}, {n_std} SD)')
    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel(series.name)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right')

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


def lof_anomalies(series, contamination=0.01, n_neighbors=20, time_step=0.01):
    """
    Find anomalies in a time series with the Local Outlier Factor (LOF) method.

    contamination : proportion of the observations marked as anomalies
    n_neighbors   : number of neighbours used to estimate the local density
    time_step     : distance between two consecutive hours on the scaled time axis
    Returns the plot, a summary and the anomalous values.
    """
    values = series.values

    # Two features: scaled time index and standardised values
    time_index = np.arange(len(values)) * time_step
    standardised = (values - values.mean()) / values.std()
    X = np.column_stack([time_index, standardised])

    # Fit LOF; observations labelled -1 are anomalies
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_anomaly = lof.fit_predict(X) == -1

    # Plot the series with the anomalies in red
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(series.index, values, linewidth=0.6, label=series.name)
    ax.scatter(series.index[is_anomaly], values[is_anomaly], color='red', s=12, zorder=3,
               label='Anomalies (LOF)')
    ax.set_title(f'LOF anomalies in {series.name} ({contamination:.1%} of the hours)')
    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel(series.name)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right')

    # Summary of the anomalies
    anomalies = series[is_anomaly]
    summary = {
        'number of anomalies': len(anomalies),
        'share of anomalies (%)': round(100 * len(anomalies) / len(series), 2),
        'lowest anomaly': round(float(anomalies.min()), 2),
        'highest anomaly': round(float(anomalies.max()), 2),
    }
    return fig, summary, anomalies


def stl_decomposition(series, period=52, seasonal=13, trend=105, robust=False):
    """
    Decompose a time series into trend, seasonal and residual components with STL.

    period   : number of observations in one season (52 weeks = one year)
    seasonal : length of the seasonal smoother (odd number; higher = more stable season)
    trend    : length of the trend smoother (odd number, larger than the period; higher = smoother trend)
    robust   : True gives less weight to outliers when fitting
    Returns the plot of the decomposition.
    """
    stl = STL(series, period=period, seasonal=seasonal, trend=trend, robust=robust)
    result = stl.fit()

    # Plot the original series and the three components
    fig = result.plot()
    fig.set_size_inches(12, 8)
    fig.suptitle(f'STL of {series.name} (seasonal={seasonal}, trend={trend}, robust={robust})', y=1.02)
    return fig


def spectrogram(series, window_length=104, overlap=78, samples_per_year=52):
    """
    Plot a spectrogram of a time series using the short-time Fourier transform.

    window_length    : number of observations in each window (104 weeks = two years)
    overlap          : number of observations shared by two consecutive windows (must be < window_length)
    samples_per_year : sampling rate (52 for weekly data), gives the frequency in cycles per year
    Returns the plot.
    """
    # STFT; the mean of each window is removed so the constant level does not dominate
    f, t, Zxx = stft(series.values, fs=samples_per_year, nperseg=window_length,
                     noverlap=overlap, detrend='constant')

    # Time axis in years from the first date in the series
    start = series.index[0].year + series.index[0].dayofyear / 365

    fig, ax = plt.subplots(figsize=(12, 4))
    mesh = ax.pcolormesh(start + t, f, np.abs(Zxx), shading='gouraud')
    ax.set_ylim(0, 6)                                 # show the low frequencies, where the variation is
    ax.set_title(f'Spectrogram of {series.name} (window {window_length}, overlap {overlap})')
    ax.set_xlabel('Year')
    ax.set_ylabel('Frequency (cycles per year)')
    fig.colorbar(mesh, ax=ax, label='Amplitude')
    return fig

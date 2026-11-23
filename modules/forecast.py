# forecast.py
# Dynamic forecast of the reservoir degree of filling with River's SNARIMAX (part 4).
# Same function as forecast_filling() in the part 4 notebook, where it is explained and
# tested. DEFAULTS holds the best settings found in the notebook's tests.
import time

import pandas as pd
from river import time_series, linear_model, optim, preprocessing

from modules.weather import SUM_VARS

# Best settings from the tests in the notebook (lowest mean absolute error over four starts)
DEFAULTS = dict(p=1, d=0, q=1, sp=0, sd=1, sq=0, lr=0.005, history_years=8, horizon=26,
                exog=('temperature_2m_mean',), future_exog='climatology', interval=True)


def make_snarimax(p, d, q, m, sp, sd, sq, lr, loss=None, intercept_lr=None):
    """SNARIMAX with a standardised linear regression trained by SGD."""
    regressor = preprocessing.StandardScaler() | linear_model.LinearRegression(
        optimizer=optim.SGD(lr), intercept_lr=intercept_lr or lr, loss=loss or optim.losses.Squared())
    return time_series.SNARIMAX(p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq, regressor=regressor)


def forecast_filling(data, p=1, d=0, q=1, sp=0, sd=1, sq=0, lr=0.005,
                     history_years=8, horizon=26, exog=('temperature_2m_mean',),
                     forecast_start=None, future_exog='climatology', quantiles=(0.05, 0.95),
                     interval_lr=0.1):
    """
    Dynamic forecast of the weekly degree of filling for one area with River's SNARIMAX.

    data           : weekly data set from weekly_data() (column 'fill' plus exogenous columns)
    p, d, q        : order of the AR part, the differencing and the MA part
    sp, sd, sq     : the same for the seasonal part (season length 52 weeks)
    lr             : learning rate of the SGD
    history_years  : years of training data before the forecast start
    horizon        : number of weeks to forecast
    exog           : names of the exogenous columns to use (empty for none)
    forecast_start : first forecast date; None forecasts after the last observation
    future_exog    : 'climatology' (mean of the same week in the training years) or
                     'actual' (measured values, only possible for past periods)
    quantiles      : e.g. (0.05, 0.95) for a 90 % interval, or None
    interval_lr    : learning rate of the intercept in the quantile models
    Returns a DataFrame with the forecast (and interval and actual values if available),
    the training data, the mean absolute error (None without actual values) and the run time.
    """
    t0 = time.perf_counter()
    exog = list(exog)
    df = data[['fill'] + exog].dropna()
    m, freq = 52, pd.Timedelta(weeks=1)
    season = df.index.isocalendar().week.clip(upper=52).to_numpy(dtype=int)   # week 53 → 52

    # Training data: the chosen number of years before the forecast start
    start = df.index[-1] + freq if forecast_start is None else pd.Timestamp(forecast_start)
    in_train = (df.index < start) & (df.index >= start - pd.DateOffset(years=history_years))
    train, season_train = df[in_train], season[in_train]
    if len(train) < 2 * m:
        raise ValueError(f"Only {len(train)} weeks of training data; at least {2 * m} are needed.")
    future_dates = pd.DatetimeIndex([train.index[-1] + freq * (k + 1) for k in range(horizon)])

    # Future exogenous values: measured values (only for past periods) or the seasonal mean
    xs = None
    if exog:
        if future_exog == 'actual':
            future_x = df.reindex(future_dates, method='nearest', tolerance=pd.Timedelta(days=3))[exog]
            if future_x.isna().any().any():
                raise ValueError("Measured exogenous values are not available for the whole "
                                 "horizon; use the seasonal mean instead.")
        else:
            clim = train[exog].groupby(season_train).mean()
            future_season = future_dates.isocalendar().week.clip(upper=52).to_numpy(dtype=int)
            future_x = clim.reindex(future_season).set_index(future_dates).ffill().bfill()
        xs = future_x.to_dict('records')

    # One model for the forecast, and one per quantile for the interval
    losses = {'forecast': optim.losses.Squared()}
    for qt in quantiles or ():
        losses[f'q{qt:.2f}'] = optim.losses.Quantile(alpha=qt)
    result = pd.DataFrame(index=future_dates)
    for name, loss in losses.items():
        model = make_snarimax(p, d, q, m, sp, sd, sq, lr, loss,
                              intercept_lr=None if name == 'forecast' else interval_lr)
        for _, row in train.iterrows():
            model.learn_one(row['fill'], row[exog].to_dict() if exog else None)
        result[name] = model.forecast(horizon=horizon, xs=xs)

    # Compare with the measured filling when the forecast period is in the past
    actual = df['fill'].reindex(future_dates, method='nearest', tolerance=pd.Timedelta(days=3))
    mae = None
    if actual.notna().any():
        result['actual'] = actual
        mae = float((result['forecast'] - result['actual']).abs().mean())

    return result, train, mae, time.perf_counter() - t0

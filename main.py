from collections import Counter
from datetime import date, timedelta
from typing import Annotated, Callable, Optional, Sequence, TypeVar

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn
from scipy.stats import poisson

from util import load

seaborn.set()

# Top 100 chat users
with open("./data/top100_users.txt", "r") as f:
    TOP100_USERS = {line.strip() for line in f}

# Figure size configuration
# Used to convert matplotlib figsize dimensions to pixels
DPI = 144
FIG_WIDTH = 1920 / DPI
FIG_HEIGHT = 1080 / DPI

# Average das crazy moments per second (see /data/clean_worksheet.xlsx to see how this value was calculated)
MOMENT_RATE = 0.000857682

# Heatmap day abbreviations
DAYS = ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")

# Custom colormap for user mentions plot
CMAP_BIFLAG = mpl.colors.ListedColormap(mpl.cm.plasma(np.linspace(0.0, 0.5, 256)))

# Type vars
Hours = TypeVar("Hours")


def init_plot() -> tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """
    Initialize a matplotlib figure and axes

    Returns:
        A matplotlib figure and axes instance, respectively
    """
    return plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), tight_layout=True, dpi=DPI)


def line_segment(ax: mpl.axes.Axes, xy1: tuple[float, float], xy2: tuple[float, float]) -> None:
    """
    Plot a line segment

    Args:
        ax: Axes to plot on
        xy1: Starting coordinate
        xy2: Ending coordinate
    """
    ax.plot((xy1[0], xy2[0]), (xy1[1], xy2[1]), ":", color="k", alpha=0.9)


def trace_coordinate(ax: mpl.axes.Axes, xy: tuple[float, float]) -> None:
    """
    Plot line segments converging to a single coordinate

    Args:
        ax: Axes to plot on
        xy: Coordinate to converge on
    """
    x, y = xy
    line_segment(ax, (x, 0), (x, y))
    line_segment(ax, (0, y), (x, y))
    ax.plot(x, y, "o", color="k")


def user_mentions(df: pd.DataFrame, top: int = 25) -> None:
    """
    Plots a frequency chart of the top peepoHas users

    Args:
        df: Chat-log dataset
        top: Top number of chat users to plot
    """
    fig, ax = init_plot()

    freqs = df["user"].value_counts().drop("braedynl_")[:top]
    y_pos = np.arange(top - 1, -1, -1)

    ax.barh(y_pos, freqs.values, color=np.flipud(CMAP_BIFLAG(np.linspace(0, 1, top))))
    ax.set_yticks(y_pos)
    ax.set_yticklabels(freqs.index)

    # Drawing a line marking the end of the top user's freq bar
    user, x, y = freqs.index[0], freqs.values[0], y_pos[0]
    line_segment(ax, (x, 0), (x, y))

    ax.text(
        x - 1, y / 2, f"Top peepoHas user during the analysis period\n'{user}' with ~{x} peepoHas mentions!", ha="right"
    )

    # Coloring top 100 user tick labels red
    ticklabels = ax.get_yticklabels()
    for ticklabel in ticklabels:
        if ticklabel.get_text() in TOP100_USERS:
            ticklabel.set_color("C3")

    ax.set_title(
        f"Top {top} 'peepoHas' Users\n(red username = among the top 100 users with the most messages sent in Hasan's chat)"
    )
    ax.set_xlabel("Mentions")
    ax.set_ylabel("User")

    plt.show()


def das_crazy_timeline(df: pd.DataFrame) -> None:
    """
    Plots days versus time with a marker signifying every das crazy moment

    Args:
        df: Chat-log dataset
    """

    # Matplotlib doesn't allow you to make a purely time-based axis, you HAVE to pair it with a date,
    # so there's a lot of odd workarounds that you'll see here (I just chose the Unix epoch)

    ts_start = pd.Timestamp("1970-01-01 14:00:00")
    ts_stop = pd.Timestamp("1970-01-01 23:59:59")

    days = sorted(list({date(ts.year, ts.month, ts.day) for _, ts in df["sent"].iteritems()}))
    times = pd.date_range(ts_start, ts_stop, freq="S")

    occur_map = pd.DataFrame(index=times, columns=days, dtype=int).fillna(0)

    for _, ts in df["sent"].iteritems():
        time = pd.Timestamp(year=1970, month=1, day=1, hour=ts.hour, minute=ts.minute, second=ts.second)
        day = date(year=ts.year, month=ts.month, day=ts.day)
        occur_map.at[time, day] = 1

    fig, ax = init_plot()

    # ax.hlines(range(len(occur_map.columns)), ts_start, ts_stop, color="k")

    for y_pos, col in enumerate(occur_map.columns, start=-1):
        occur = occur_map[col][occur_map[col] == 1] + y_pos
        ax.plot(occur.index, occur.values, "-o", color="k", markerfacecolor="w")

    ax.set_yticks(range(len(occur_map.columns)))
    ax.set_yticklabels(occur_map.columns)

    hours = mdates.HourLocator(interval=1)
    h_fmt = mdates.DateFormatter("%I %p")
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)

    ax.set_xlim((ts_start, ts_stop + timedelta(seconds=1)))

    ax.set_title("Das Crazy Moment Timeline\n(each dot = Hasan said something was crazy)")
    ax.set_xlabel("Time (Eastern)")
    ax.set_ylabel("Date")

    plt.show()


def das_crazy_heatmap(df: pd.DataFrame) -> None:
    """
    Plots a calendar heatmap of das crazy mentions on a daily basis

    Args:
        df: Chat-log dataset
    """
    counts = Counter(date(ts.year, ts.month, ts.day) for _, ts in df["sent"].iteritems())
    start, stop = min(counts.keys()), max(counts.keys())

    dstart = start - timedelta(start.toordinal() % 7)
    dstop = stop + timedelta(7 - stop.toordinal() % 7)

    n_weeks = (dstop - dstart).days // 7
    dates = np.full((7, n_weeks), fill_value="", dtype=object)
    freqs = np.zeros((7, n_weeks), dtype=int)

    d = dstart
    for col in range(n_weeks):
        for row in range(7):
            dates[row][col] = d.strftime("%m/%d")
            freqs[row][col] = counts[d]
            d += timedelta(1)

    fig, ax = init_plot()

    im = ax.imshow(freqs)

    for row in range(7):
        for col in range(n_weeks):
            ax.text(col, row, dates[row][col], ha="center", va="center", color="w")

    ticks = [0, 10, 20, 30, 40, 50]
    cbar = ax.figure.colorbar(im, ax=ax, ticks=ticks)
    cbar.ax.set_yticklabels(["No Data"] + [str(n) for n in ticks[1:]])
    cbar.ax.set_ylabel("Das Crazy Moments", rotation=-90, va="bottom")

    ax.set_title("Das Crazy Moment Frequency")
    ax.set_xticks([])
    ax.set_yticks(np.arange(len(DAYS)))
    ax.set_yticklabels(DAYS)

    ax.grid(False)

    plt.show()


def das_crazy_distribution(
    poisson_func: Callable[[Sequence[int], float], Sequence[float]],
    time_range: Sequence[Annotated[float, Hours]],
    moment_range: Sequence[int],
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
) -> mpl.axes.Axes:
    """
    Plot a das crazy mentions Poisson distribution function

    Args:
        poisson_func: Poisson distribution function that accepts an event range and a mu
        time_range: A range of stream time hours
        moment_range: A range of das crazy moment counts
        title: Plot title
        xlabel: Plot x label
        ylabel: Plot y label
    """
    fig, ax = init_plot()

    # Using the derived Poisson mu, mu = r*t, where r is the event rate and t is an interval of time
    # in this case, r being the rate of crazy mentions and t being the length of the stream
    for time in time_range:
        mu = MOMENT_RATE * (time * 3600)
        prob_range = poisson_func(moment_range, mu)
        ax.plot(moment_range, prob_range, "o--", label=time, alpha=0.9)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.legend(title="Stream Time (Hours)")

    return ax


def das_crazy_pmf(time_range: Sequence[Annotated[float, Hours]], moment_range: Sequence[int]) -> None:
    """
    Plot the das crazy mentions Poisson probability mass function

    Args:
        time_range: A range of stream time hours
        moment_range: A range of das crazy moment counts
    """
    ax = das_crazy_distribution(
        poisson.pmf,
        time_range,
        moment_range,
        title="Das Crazy Moment Probability Mass Function\n(the probability that Hasan says something is crazy exactly $k$ times)",
        xlabel="Das Crazy Moments ($k$)",
        ylabel="Probability ($P(X = k)$)",
    )

    t = time_range[3]
    x = 12
    y = poisson.pmf(x, MOMENT_RATE * (t * 3600))
    trace_coordinate(ax, (x, y))
    ax.annotate(
        f"There's an {y:.1%} chance that Hasan will say something\nis crazy exactly {x} times during a {t} hour stream",
        (x + 0.5, y),
    )

    plt.show()


def das_crazy_cdf(time_range: Sequence[Annotated[float, Hours]], moment_range: Sequence[int]) -> None:
    """
    Plot the das crazy mentions Poisson cumulative distribution function

    Args:
        time_range: A range of stream time hours
        moment_range: A range of das crazy moment counts
    """
    ax = das_crazy_distribution(
        poisson.cdf,
        time_range,
        moment_range,
        title="Das Crazy Moment Cumulative Distribution Function\n(the probability that Hasan says something is crazy $\leq k$ times)",
        xlabel="Das Crazy Moments ($k$)",
        ylabel="Probability ($P(X \leq k)$)",
    )

    t = time_range[-1]
    x = 30
    y = poisson.cdf(x, MOMENT_RATE * (t * 3600))
    trace_coordinate(ax, (x, y))
    ax.annotate(
        f"There's a {y:.1%} chance that Hasan will say something\nis crazy {x} times or less during a {t} hour stream",
        (x + 0.5, y),
    )

    plt.show()


def main():
    df_raw = load("raw")
    df_clean = load("clean")

    user_mentions(df_raw)

    das_crazy_timeline(df_clean)
    das_crazy_heatmap(df_clean)
    das_crazy_pmf(range(1, 11), range(0, 60))
    das_crazy_cdf(range(1, 11), range(0, 60))


if __name__ == "__main__":
    main()

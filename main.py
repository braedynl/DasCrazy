from collections import Counter
from datetime import date, timedelta
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn

from util import load

seaborn.set()

# Figure size configuration
DPI = 144
FIG_WIDTH = 960 / DPI
FIG_HEIGHT = 720 / DPI

# Heatmap constants
DAYS = ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")


def init_plot(nrows: int = 1, ncols: int = 1) -> tuple[mpl.figure.Figure, mpl.axes.Axes]:
    return plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(FIG_WIDTH, FIG_HEIGHT),
        tight_layout=True,
        dpi=DPI
    )


def user_freq(df: pd.DataFrame, top: int = 25, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None) -> None:
    fig, ax = init_plot()

    freqs = df["user"].value_counts().drop("braedynl_")[:top]
    y_pos = np.arange(len(freqs) - 1, -1, -1)

    ax.barh(y_pos, freqs.values)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(freqs.index)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    plt.show()


def dascrazy_heatmap(df: pd.DataFrame) -> None:
    counts = Counter(
        date(ts.year, ts.month, ts.day) for _, ts in df["sent"].iteritems()
    )
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

    cbar = ax.figure.colorbar(im, ax=ax, ticks=[0, 10, 20, 30, 40])
    cbar.ax.set_yticklabels(["No Data", "10", "20", "30", "40"])
    cbar.ax.set_ylabel("Das Crazy Moments", rotation=-90, va="bottom")

    ax.set_title("Das Crazy Moment Frequency")
    ax.set_xticks([])
    ax.set_yticks(np.arange(len(DAYS)))
    ax.set_yticklabels(DAYS)

    ax.grid(False)

    plt.show()


def main():
    df = load("clean")

    # dascrazy_heatmap(df)
    # user_freq(df)


if __name__ == "__main__":
    main()

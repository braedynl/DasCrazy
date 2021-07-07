from collections import Counter
from datetime import date, timedelta
from typing import Optional

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


def user_freq(df: pd.DataFrame, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, top: int = 25) -> None:
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), tight_layout=True, dpi=DPI)

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
    dstop = (stop - timedelta(stop.toordinal() % 7)) + timedelta(7)

    n_weeks = (dstop - dstart).days // 7
    dates = np.full((7, n_weeks), fill_value="", dtype=object)
    freqs = np.zeros((7, n_weeks), dtype=int)

    d = dstart
    for i in range(n_weeks):
        for j in range(7):
            dates[j][i] = d.strftime("%m/%d")
            freqs[j][i] = counts[d]
            d += timedelta(1)

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), tight_layout=True, dpi=DPI)

    im = ax.imshow(freqs)

    for i in range(7):
        for j in range(n_weeks):
            ax.text(j, i, dates[i][j], ha="center", va="center", color="w")

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

    dascrazy_heatmap(df)
    # user_freq(df)


if __name__ == "__main__":
    main()

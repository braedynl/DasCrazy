import sys
from datetime import datetime
from typing import Any

import pandas as pd


def load(filename: str) -> pd.DataFrame:
    """
    Load a chat-log dataset as a pandas dataframe

    Args:
        filename: Name of the chat-log dataset

    Returns:
        Chat-log dataset
    """
    df = pd.read_csv(f"data/{filename}.csv")
    df["sent"] = pd.to_datetime(df["sent"], infer_datetime_format=True)
    return df


def log(obj: Any) -> None:
    """
    Prints an object with timestamp

    Args:
        obj: Any representable object
    """
    sys.stdout.write(f"[{datetime.now()}] {obj}\n")

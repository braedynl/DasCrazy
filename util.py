import pandas as pd

def load(filename: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{filename}.csv")
    df["sent"] = pd.to_datetime(df["sent"], infer_datetime_format=True)
    return df

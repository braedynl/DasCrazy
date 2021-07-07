import pandas as pd

from util import load


def main(raw_filename: str, clean_filename: str) -> None:
    raw_data = load(raw_filename)
    clean_data = pd.DataFrame(columns=raw_data.columns)

    # First chat message to signal a "das crazy" moment
    indicator_row = None

    for _, row in raw_data.iterrows():
        if "crazy" in row["message"].lower():

            # Filters other users messaging at (roughly) the same time, i.e., discards
            # all messages containing the word "crazy" within a 30 second interval
            if (
                indicator_row is None
                or (row["sent"] - indicator_row["sent"]).total_seconds() > 30
            ):
                indicator_row = row
                clean_data = clean_data.append(row, ignore_index=True)

    clean_data.to_csv(f"data/{clean_filename}.csv", index=False)


if __name__ == "__main__":
    main("raw", "clean")

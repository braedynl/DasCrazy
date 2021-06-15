import csv
import datetime
import random

# LSF and OKBH (even Politics, to some extent) could be considered a sub-class of Reactlord,
# but for the purposes of this analysis, they were considered different.
SEGMENTS = ["Politics", "LSF", "Introduction", "OKBH", "PO Box", "Gaming", "IRL", "Reactlord"]

# Very rough segment frequency estimates; used to make a random segment choice for generation
SEGMENT_WEIGHTS = [0.3, 0.1, 0.01, 0.05, 0.05, 0.2, 0.02, 0.27]


def generate_test(n: int, filename: str = 'data/testing.csv') -> None:
    """
    Generate a testing set of "das crazy" mentions

    The real data would be a lot more repetitive, but this is
    simply to test formatting, shapes, and sizes.

    Parameters
    ----------
    n: int
        Number of dates to generate for
    
    filename: str = 'data/testing.csv'
        Output filename for the dataset
    """

    csvfile = csv.writer(open(filename, 'w', newline=''))
    csvfile.writerow(["date", "uptime", "view_count", "segment"])

    d = datetime.date(2021, 1, 1)

    for _ in range(n):
        rows = []

        # Hypothesis estimate of how many "das crazy" mentions there are in a day
        n_mentions = random.randint(20, 30) 

        for _ in range(n_mentions):
            h = random.randint(8, 10)                               # Uptime; Hasan tends to stream 8-10 hours
            m = random.randint(0, 59)
            s = random.randint(0, 59)
            view_count = random.randint(20000, 55000)               # View count; 20K on slow days, >40K on busy ones
            segment, = random.choices(SEGMENTS, SEGMENT_WEIGHTS)    # Random segment; would be much more consistent realistically

            rows.append([d.isoformat(), f"{h:02}:{m:02}:{s:02}", view_count, segment])

        csvfile.writerows(rows)

        d += datetime.timedelta(1)


def main():
    generate_test(10)


if __name__ == "__main__":
    main()

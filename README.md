# DasCrazy

A statistical analysis of Hasan Piker's obsession with the term, "that's crazy". [See the project on GitHub](https://github.com/braedynl/DasCrazy).

### Collection Methodology

A Python script was executed to read Hasan's Twitch chat everyday from 6/19/2021 to 7/10/2021. This collection script does a blanket-search for the "peepoHas" emote in user chat messages, and periodically exports the updated data as a CSV file. There are some entries in the raw set that were manually entered by me, due to some of the problems that this type of collection method has (see section below).

A second script is ran to process this raw data for "that's crazy" moments, as many users will post similar messages at (roughly) the same time, and most uses of the "peepoHas" emote do not indicate a "that's crazy" moment.

### Problems

While it may seem that Twitch chat will always type the same messages for every recurring occasion, I had observed _many_ instances where no user would post a reference to Hasan saying "that's crazy", particularly in situations where Hasan was engaged in long discussions. I was present for a majority of the collection script's runtime, and so I would post in chat myself to correct for these misses. I cannot guarentee that every "that's crazy" moment was accounted for, however, as I did leave the collection script to run on its own sometimes.

For occasions where I would be gone for extended periods of time, I would manually label missed "that's crazy" moments by going through the VOD. These cases are denoted by a `MANUALENTRY` under the `user` column.

In rare circumstances, there have been cases where users would post a message containing "peepoHas" and "crazy" (the two keywords the programs look for) together for indiscernible reasons. These cases were so rare that I didn't bother correcting for them (I can think of only two instances).

### FAQ

> Why just search for "peepoHas" in the collection script over searching for both "peepoHas" and "crazy"?

Python is a slow language, and its `socket` library is even slower. I was originally planning on doing it in C because of that, but I wasn't feeling up to the task of dealing with stupid C crap when I wrote the program.

Python's slowness is the reason for the blanket search. Two searches (one for both "peepoHas" and "crazy") and a transformation (lowercasing all letters) would have to occur between socket `recv()` calls, which could result in loss of data if not fast enough. The lowercasing has to be done, since many users would type "CRAZY" or some other variation of the casing. "peepoHas" can only be written one way, unless the user makes a typo. Thus, a search for "peepoHas" alone was the best option, with a second pass for "crazy" later.

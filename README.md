# DasCrazy

A statistical look into Hasan Piker's obsession with calling things "crazy". [Code and data can be found here](https://github.com/braedynl/DasCrazy).

More technical behind-the-scenes info on the analysis (likely too boring to be read on stream, meant more so for the nerds):

### Collection Methodology

A collection script is used to search for any message containing the emote, "peepoHas". A second pass through the collected data is then performed to find moments where Hasan was likely to have said that something is crazy (simply searching for the keyword, "crazy", after some minor text transformations). Do note that, because of this search method, this data encompasses _all_ forms of Hasan saying something is crazy, as often recognized by Hasan's chat.

One primary issue you might see here is message repetition. Often, when Hasan says something is crazy, _many_ users will type similar and/or identical messages to signify a "crazy moment". Each user's message does not indicate an _individual_ crazy moment in this context, and so, a 30 second boundary is required between crazy moment "indicator" messages to hopefully filter for actual instances where Hasan said that something on stream was crazy. 

This method is not without problems. I have witnessed cases where users would pair the keywords ("peepoHas" and "crazy") in inappropriate circumstances on very rare occasions. I've also seen instances where _someone else_ would say that something is crazy, where chat would reciprocate as if it was _Hasan_ that had said something was crazy -- this only happened once during the analysis period, to my knowledge. There are also cases where Hasan would say something is crazy numerous times within a short time span, which often can't be deduced from looking at chat messages -- these cases are pretty rare as well, however.

### The Math

The method of prediction, chosen by me, was a simple Poisson distribution. [From Wikipedia](https://en.wikipedia.org/wiki/Poisson_distribution):

> In probability theory and statistics, the Poisson distribution, named after French mathematician Denis Poisson, is a discrete probability distribution that expresses the probability of a given number of events occurring in a fixed interval of time or space if these events occur with a known constant mean rate and independently of the time since the last event.

In order for a Poisson distribution to be applicable, here, the following assumptions must be true:

- Events occur independently
- The average rate at which events occur is independent of any occurrences
- Two events cannot occur at exactly the same instant

If Hasan is not _thinking_ about how or when he is saying something is crazy (i.e., it's an arbitrary choice that he's making to use the word, "crazy", as a descriptor at every moment), then it's likely a safe assumption that the events (crazy moments) are happening independently. Another assumption we can pretty confidently rule out is the third one; it's impossible for Hasan to say something is crazy multiple times within the same instant, though it _is_ possible for him to say it within a short timespan, such that it makes it indistinguishable from looking at the chat alone. As discussed earlier, these cases are rare, and not a large enough concern to warrant modification for a rough analysis.

What can be mildly concerning is the second assumption (something that another chatter may be willing to continue this work on). I have noticed that, during gaming streams in particular, it's possible that the rate of crazy moments is significantly higher, to the extent of declaring the event rate as variable and therefore a Poisson distribution is unfit for this data. Working under this assumption could yield better predictions if a more suitable model is applied, but again, it might be something another chatter can take on (I want to move onto other projects that I have planned ;) ).

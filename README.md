## Insight Data Engineering Fellowship Challenge

Entry for:
Evan Miller

### Table of Contents

1. [Introduction] (README.md#introduction)
2. [filecleaner.py] (README.md#filecleaner.py)
3. [antifraud_2.py] (README.md#antifraud_2.py)
4. [antifraud_1.py](README.md#antifraud_1.py)
5. [antifraud_1.5.py] (README.md#antifraud_1.5.py)
6. [antifraud_2.extras.py] (README.md#antifraud_2.extras.py)
7. [Other Thoughts] (README.md#other-thoughts)


### Introduction

Thank you for giving me this opportunity to apply for an Insight data
engineering fellowship! I have produced four versions of my code, which meet
different critereon, as well as a small file cleaning utility. All of my codes
are written in Python.

The codes are described briefly below. More extensive descriptions are given in
the headers to the files themselves.


### filecleaner.py
Requires: sys

This is a simple utility program which cleans input files of the '\r' new line 
character. The given data uses '\n' for the end of a transaction, but allows 
'\r' to occur in the message column. Unfortunately, Python's csv reader module
does not yet allow specifying the lineterminator (it defaults to including both
options), so comments with '\r' in them create new lines on reading. Running
this program first is unnecessary (i.e. the code will accurately complete with
the original data), but it will prevent the generation of some error messages.



### antifraud_2.py
Requires: sys, csv

This is likely going to be the preferred version of my code, as it is the
simplest, fastest and least data intensive. However, the tradeoff is that most
of the substantial calculations occur between when a client requests a
transaction and the transaction's trustworthiness is determined. Thus, the end
user experience for our clients will be somewhat slower.

In this version, the code creates a dictionary called 'network' containing an
entry for each unique costumer id. The value attached this entry is the set of
ids corresponding to the people that person has transacted with ('friends').
When a new transaction is initiated, the code first checks one participant's
friends set for the other party, then checks for overlap between the friends
sets, then finally makes two new sets containing each party's friends and 
friends-of-friends. If these two new sets don't overlap, the parties are not
fourth-order friends or lower.



### antifraud_1.py
Requires: sys, csv

This version of my code is EXTREMELY data-intensive and slow, so much so that I
would recommend not running it on the full data sets unless you have copious
amounts of memory available. However, this code has the advantage that all
calculations are preformed and the results are ready before the customer ever
makes a request. Thus, between when a client submits a transaction and the
system responds is almost instantaneous; only a simple set check needs to be
preformed. If the company desides that minimizing a customer's wait time is a
lexical priority to data usage and total run time, this version might be
preferable.

In version 1, the code creates a dictionary of Unique_id class objects, which
contain sets of a given users first-, second-, third-, and fourth-order friends.
All of this information is on hand, so when a new request comes in, the code
only has to check its lists before responding. However, after that response the
code has to go through the arduous process of updating both parties friends
sets, as well as the friends sets of their friends, second-order friends and so
forth. Thus the total runtime of this code is incredibly slow, compared to other
versions. Besides the quick response time, this version might also be more
desireable if degrees of friendship were needed for other applications, e.g.
marketing or advertising.



### antifraud_1.5.py
Requires: sys, csv

Version 1.5 is a hybrid of versions 1 and 2. In this version, both first- and 
second- order friends are recorded for every user. When a new request is made,
the only substantial calculation is a set intersection to determine third- and
fourth-order connections. Afterwards, only friends and friends of friends need
to be updated. Thus, version 1.5 is substantially faster and less data-intensive
than version 1, and also takes less time to respond to a client than version 2.



### antifraud_2.extras.py
Requires: sys, csv, datetime, re

This version of the code works similarly to version 2, but has been expanded to 
include a number of extra features, exploring new means of fraud detection as
well as others methods of employing the provided data. The basic outline of this 
version is identical to version 2, except that instead of a set, the values in
the network dictionary are instances of the User_account class, which contains
a variety of other data about the user and their transaction history. Additionally, 
to account for more complicated means of fraud detection, instead of the binary
trusted/unverified options in the challenge, each transaction is given an
integer trustworthiness rating, saved in the output.txt file.

The extra features are discussed in detail as they come up in the code. For a
summary, they are:<br />
Extra 0: A system where accounts that have gone through an external verification are treated as trustworthy<br />
Extra 1: A variety of checks flagging accounts which send / request requests with suspicious frequencies<br />
Extra 2: A means of mitigating the suspicion status of accounts after periods of non-suspicious activity<br />
Extra 3: A rewards program that makes a payment to returning customers<br />
Extra 4: A system which increases the untrustworthiness of payment requests from accounts that have been externally flagged for suspected fraud<br />
Extra 5: A system which increases the untrustworthiness of transaction requests for suspicious amounts<br />
Extra 6: A system which increases the untrustworthiness of requests with no message<br />
Extra 7: A system which flags and records accounts suspected of criminal activity<br />
Extra 8: A system which raises the suspicion of accounts that request the same amount from different people several times in a row<br />



### Other Thoughts

Even in my most data efficient version, version 2, fully half of the data I
save is redundant. Because all friendships are reciprocal, B being in the set of
A's friends implies that A is a member of B's friends as well. However, at least
in the time frame we were given, I couldn't come up with any way to use this to
halve the data requirements (and possibly make the code run faster too). I
mean, I could just make a giant table comparing everyone to everyone else, but
unless we are considering 6+ order friendships or something that is bound to be
way less efficient. The problem is that if only one person records each
friendship, it could transpire that B (and only B) records their friendship with
both A and C. If A and C then interact, the only way they can know they share
the mutual friend B is if they scan every client for potential matches. Anyway,
if this becomes an issue maybe we can find another solution.


From looking into the operation of Extra 1, it's pretty clear that most people
only participate in a few transactions, but a few participate in a truely vast
number. Maybe this is major companies or something?


If I were asked to implement this feature in real life, I would have to point
out that it doesn't seem like a very good system. All a scammer would have to
do is make a single payment to some huge retailer like Amazon, and suddenly they
would be second-order friends with (potentially) millions of people. This was 
the problem I was trying to fix with Extra 0.

#!/usr/bin/env bash

# example of the run script for running the fraud detection algorithm with a python file,
# but could be replaced with similar files from any major language

# I'll execute my programs, with the input directory paymo_input and output the files in the directory paymo_output

# 2 is simpler and less data intensive. However, it preforms the calculation of degree-of-friendship after 
#   a client makes a request. 1 is far more complicated, but it pre-loads all of the calculations and so
#   only needs to check existing records once a customer makes a payment request. It would also be more versatile
#   if degree of friendship was needed for other applications.

#python ./src/filecleaner.py ./paymo_input/stream_payment.csv ./paymo_input/stream_payment_2.csv

python ./src/antifraud_1.py ./paymo_input/batch_payment.txt ./paymo_input/stream_payment.txt ./paymo_output/output1.txt ./paymo_output/output2.txt ./paymo_output/output3.txt

# python ./src/antifraud_2_extras.py ./paymo_input/batch_payment.csv ./paymo_input/stream_payment.csv ./paymo_output/output1.txt ./paymo_output/output2.txt ./paymo_output/output3.txt

#!/usr/bin/env bash

# Run script for antifraud files
#
# This script assume inputs in directory paymo_input and outputs in the
# directory paymo_output.
#
# Remove # from in front of desired script to run.
# 
# See README for more complete file descriptions.
#


# File cleaning script. Overwrites batch_payment_2.csv with a cleaned version of
#   batch_payment.csv (can be used with stream_payment as well)
# Requires modules: sys

#python ./src/filecleaner.py ./paymo_input/batch_payment.csv ./paymo_input/batch_payment_2.csv


# Fraud Detection System versions 1, 1.5 and 2. Be sure to specify version
#   number of first arguement. With inputs batch_payment.csv and
#   stream_payment.csv, writes outputs output1.txt, output2.txt and output3.txt.
#   Output files are replaced.
# Requires modules: sys, csv

#python ./src/antifraud_2.py ./paymo_input/batch_payment.csv ./paymo_input/stream_payment.csv ./paymo_output/output1.txt ./paymo_output/output2.txt ./paymo_output/output3.txt


# Fraud Detection System version 2 with extra features. With inputs
#   batch_payment.csv and stream_payment.csv, writes outputs output.txt,
#   rewards.csv and suspects.txt. Output files are replaced.
# Requires modules: sys, csv, datetime, re

python ./src/antifraud_2.extras.py ./paymo_input/batch_payment_2.csv ./paymo_input/stream_payment_2.csv ./paymo_output/output.txt ./paymo_output/rewards.csv ./paymo_output/suspects.txt

### File Cleaning System ###
# 
# Removes '\r' character from input files
#
#
# Description:
#
# This program cleans input files of the '\r' new line character. The given data
#   uses '\n' for the end of a transaction, but allows '\r' to occur in the
#   message column. Unfortunately, Python's csv reader module does not yet allow
#   specifying the lineterminator (it defaults to including both options), so
#   comments with '\r' in them create new lines on reading. Running this program
#   first is unnecessary (i.e. the code will accurately complete with the
#   original data), but it will prevent some error messages from being generated

import sys

try:
    file_in = sys.argv[1]
except:
    sys.exit("No input file given")

try:
    file_out = sys.argv[2]
except:
    sys.exit("No output file given")    

content = open(file_in, "r").read().replace('\r','')

out = open(file_out,"w")
out.write(content)
out.close()
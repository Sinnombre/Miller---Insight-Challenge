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
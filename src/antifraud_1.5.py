### Fraud Detection System, version 1.5 ###
#
# Version 1.5 of the Fraud Detection System
#
# Description:
#
# This code is a hybridization of versions 1 and 2. Instead of storing
#   connections up to fourth-order for every client (like version 1), it only
#   saves first- and second-order friendships. However, it does save these
#   friendships for everyone, so instead of having to calculate a client's
#   second-order relationships after they make a transaction request (like
#   version 2), this version can simply pull the relevant data. Thus, the only
#   complicated calculation this code must preform between receiving and
#   responding to a client's request is a set intersection (importantly, the for
#   loop in version 2 has been effectively moved to after the client interaction
#   is complete). This code is therefore significantly faster and less
#   data-instensive than version 1 (though not as fast as version 2), and has
#   much less time between a client's request and the response than version 2
#   (though responses aren't quite as quick as in version 1).
#
#
# Basic outline:
#
# The code creates a dictionary called 'network' containing an entry for each
#   unique costumer id. The value attached this entry is an instance of the
#   class 'Unique_id,' which contains verification functions and the variable
#   Unique_id.friends. This variable contains a list of two sets, which
#   contain the ids of the costumer's first-order friends and their first- and
#   second-order friends respectively (by saving this data redundantly, we
#   remove the need for the 'collapse' function in version 2).
#
# When a new transaction occurs, the code simply checks whether the participants
#   are first- or second-order friends. If they are not, the code then creates
#   an intersection of the Unique_id.friends[1] sets. If this intersection is
#   non-empty, the two participants share a third- or fourth-order friend. The
#   transaction's trustworthiness is then flagged accordingly.
#
# The function merge(net,id_1,id_2) is called whenever a new valid transaction
#   is complete. It takes the network net and integer ids id_1 and id_2 and
#   merges the friend sets of the relevant network entries. id_1 becomes id_2's
#   friend, id_1's friends become id_2's second-order friends and so forth.
#   additionally, all of id_1's friends gain id_2 as a second-order friend. This
#   process can be time consuming. However, as noted above, this time is spent
#   after the costumer's request has been processed.


import sys
import csv

# Class containing friends sets
class Unique_id:
    
    def __init__(self):
        self.friends = [set(), set()]                                           # self.friends[0] is the client's set of friends. self.friends[1] contains both first- and second-order friends

    def verification_1x(self,id_2):                                             # Checks if new request is from a friend
        if(id_2 in self.friends[0]):
            return "trusted"
        else:
            return "unverified"
    
    def verification_2x(self,id_2):                                             # Checks if new request is from a friend or friend of a friend
        if(id_2 in self.friends[1]):
            return "trusted"
        else:
            return "unverified"
    
    def verification_4x(self,other,id_2):                                       # Checks if new request is from a fourth-order friend or lower
        if(id_2 in self.friends[0] or
        len(self.friends[1] & other.friends[1]) > 0):
            return "trusted"
        else:
            return "unverified"


# Function for updating friendships after a new transaction. Inputs: network
#   dictionary net, integer ids id_1 and id_2 of the two participants
def merge(net,id_1,id_2):                                                       

    net[id_1].friends[1] |= net[id_2].friends[0]                                # Adds all of id_2's friends to id_1's set of second-order friends
    for person in net[id_2].friends[0]:                                         # For each of id_2's friends:
        net[person].friends[1].add(id_1)                                        #   Add id_1 as a second-order friend

    net[id_2].friends[1] |= net[id_1].friends[0]                                # Adds all of id_1's friends to id_2's set of second-order friends
    for person in net[id_1].friends[0]:                                         # For each of id_1's friends:
        net[person].friends[1].add(id_2)                                        #   Add id_2 as a second-order friend

    net[id_1].friends[0].add(id_2)                                              # Add id_2 as id_1's friend
    net[id_1].friends[1].add(id_2)                                              # Add id_2 to id_1's first- and second-order friends set
    net[id_2].friends[0].add(id_1)                                              # Add id_1 as id_2's friend
    net[id_2].friends[1].add(id_1)                                              # Add id_1 to id_2's first- and second-order friends set
    
    net[id_1].friends[1].discard(id_1)                                          # Discard self from set of second-order friends
    net[id_2].friends[1].discard(id_2)
        

### Main code ###

# Input files
try:
    batch_in = sys.argv[1]                                                      # Batch input payments
    stream_in = sys.argv[2]                                                     # Stream input payments
    out_1 = sys.argv[3]                                                         # Feature 1 output
    out_2 = sys.argv[4]                                                         # Feature 2 output
    out_3 = sys.argv[5]                                                         # Feature 3 output
except:
    sys.exit("Input failed. Please check command line syntax.")


# Read batch file
network = {}
row_number = 1                                                                  # Row numbering starts at 2 (increments at beginning of loop) so that row_number lines up with files, which contain header line

with open(batch_in,'rU') as batch_file:                                         # Opening with 'rU' instead of 'r' circumvents a bug related to newline characters in csv module
    batch_connections = csv.DictReader(batch_file, skipinitialspace = True,
    quoting=csv.QUOTE_NONE)
    for row in batch_connections:
        # For each row in the batch file:

        row_number += 1
        
        # See if the id1 and id2 elements of the csv file are integers and
        #   create simple references
        try:
            id_1 = int(row['id1'])
            id_2 = int(row['id2'])
        except:
            # Send error message and skip rows that do not contain integer ids
            print "(In batch_payments) id field does not contain an integer! "+\
            "Ignoring this entry... row number is:\n", row_number               # Outputs the string for debugging
            continue
        
        # If a dictionary entry does not yet exist for one of the participants,
        #   create it and initialize its value as an empty instance of Unique_id
        if (not network.has_key(id_1)):
            network[id_1] = Unique_id()
            
        if (not network.has_key(id_2)):
            network[id_2] = Unique_id() 
        
        # If they aren't already friends, update friends sets for new
        #   transaction    
        if( not (id_2 in network[id_1].friends[0])):
            merge(network,id_1,id_2)

    
# Read stream file
out1 = open(out_1,'w')
out2 = open(out_2,'w')
out3 = open(out_3,'w')
row_number = 1                                                                  # Row numbering starts at 2 (increments at beginning of loop) so that row_number lines up with files, which contain header line

with open(stream_in,'rU') as stream_file:                                       # Opening with 'rU' instead of 'r' circumvents a bug related to newline characters in csv module
    stream = csv.DictReader(stream_file, skipinitialspace = True,
    quoting=csv.QUOTE_NONE)
    for row in stream:
        # For each row in the stream file:

        row_number += 1
        
        # See if the id1 and id2 elements of the csv file are integers and
        #   create simple references
        try:
            id_1 = int(row['id1'])
            id_2 = int(row['id2'])
        except:
            # Send error message and skip rows that do not contain integer ids
            print "(In stream_payments) id field does not contain an integer! "+\
            "Ignoring this entry... row number is:\n", row_number               # Outputs the string for debugging
            continue
        
        # If a dictionary entry does not yet exist for one of the participants,
        #   create it and initialize its value as an empty instance of Unique_id
        if (not network.has_key(id_1)):
            network[id_1] = Unique_id()
            
        if (not network.has_key(id_2)):
            network[id_2] = Unique_id()
        
        # Check if friends
        out1.write(network[id_1].verification_1x(id_2))
        out1.write("\n")
        out2.write(network[id_1].verification_2x(id_2))
        out2.write("\n")
        out3.write(network[id_1].verification_4x(network[id_2],id_2))
        out3.write("\n")
        
        # Here insert the code to get verification from the customer, if needed.
        # If verification withheld, flag as spam and continue. Else:
        
        # If they aren't already friends, update friends sets for new
        #   transaction    
        if( not (id_2 in network[id_1].friends[0])):
            merge(network,id_1,id_2)
  
# Close output files     
out1.close()
out2.close()
out3.close()

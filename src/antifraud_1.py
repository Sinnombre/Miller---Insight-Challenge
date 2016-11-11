### Fraud Detection System, version 1 ###
#
# Version 1 of the Fraud Detection System
# WARNING: Extremely data intensive and slow
#
# Description:
#
# This code is substantially more data intensive and slower than versions 1.5
#   and 2, so much so that I would not recommend running it on the entire data
#   set unless you have copious amounts of memory available. HOWEVER, the bulk
#   of the calculations happen after the costumer's query has been processed.
#   If minimizing customer's wait time is a lexical priority to data usage and 
#   total run time, this version might be preferable.
#
#
# Basic outline:
#
# The code creates a dictionary called 'network' containing an entry for each
#   unique costumer id. The value attached this entry is an instance of the
#   class 'Unique_id,' which contains several functions and the variable
#   Unique_id.friends. This variable contains a list of four sets, corresponding
#   to the costumer's first-, second-, third- and fourth-order friends.
#
# When a new transaction occurs, the code simply checks whether the participants
#   are first-, second-, third- or fourth-order friends and flags the
#   transaction's trustworthiness accordingly.
#
# The function merge(net,id_1,id_2) is called whenever a new valid transaction
#   is complete. It takes the network net and integer ids id_1 and id_2 and
#   merges the friends sets of the relevant network entries. id_1 becomes id_2's
#   friend, id_1's friends become id_2's second-order friends and so forth.
#   additionally, all of id_1's friends gain id_2 as a second-order friend and
#   all of id_2's friends as third-order friends etc. Thus, each merge can be
#   very time consuming, especially as these extended friends networks grow
#   larger. However, as noted above, this time is spent after the costumer's
#   request has been processed.


import sys
import csv

# Class containing friends sets
class Unique_id:
    
    def __init__(self):
        self.friends = [set(), set(), set(), set()]                             # self.friends[0] contains the client's friends, self.friends[1] their second-order friends and so forth

    def collapse(self,id):                                                      # Removes repititions of same person at higher friendship degrees
        self.friends[3] -= self.friends[2]
        self.friends[3] -= self.friends[1]
        self.friends[3] -= self.friends[0]
        self.friends[2] -= self.friends[1]
        self.friends[2] -= self.friends[0]
        self.friends[1] -= self.friends[0]
        self.friends[3].discard(id)                                             # Discards self from friends sets
        self.friends[2].discard(id)
        self.friends[1].discard(id)
        self.friends[0].discard(id)
        
    def verification_1x(self,id_2):                                             # Checks if new request is from a friend
        if(id_2 in self.friends[0]):
            return "trusted"
        else:
            return "unverified"
    
    def verification_2x(self,id_2):                                             # Checks if new request is from a friend or friend of a friend
        if(id_2 in self.friends[0] or id_2 in self.friends[1]):
            return "trusted"
        else:
            return "unverified"
    
    def verification_4x(self,id_2):                                             # Checks if new request is from a fourth-order friend or lower
        if(id_2 in self.friends[0] or id_2 in self.friends[1]):                 # NOTE: Small amount of redundency here. Could fix
            return "trusted"
        elif (id_2 in self.friends[2] or id_2 in self.friends[3]):
            return "trusted"
        else:
            return "unverified"


# Function for updating friendships after a new transaction. Inputs: network
#   dictionary net, integer ids id_1 and id_2 of the two participants
def merge(net,id_1,id_2):                                                       

    net[id_1].friends[3] |= net[id_2].friends[2]                                # Adds all of id_2's third-order friends to id_1's set of fourth-order friends
    for person in net[id_2].friends[2]:                                         # For each of id_2's third-order friends:
        net[person].friends[3].add(id_1)                                        #   Add id_1 as a fourth-order friend
    
    net[id_2].friends[3] |= net[id_1].friends[2]                                # Adds all of id_1's third-order friends to id_2's set of fourth-order friends
    for person in net[id_1].friends[2]:                                         # For each of id_1's third-order friends:
        net[person].friends[3].add(id_2)                                        #   Add id_2 as a fourth-order friend
    
    net[id_1].friends[2] |= net[id_2].friends[1]                                # Adds all of id_2's second-order friends to id_1's set of third-order friends
    for person in net[id_2].friends[1]:                                         # For each of id_2's second-order friends:
        net[person].friends[2].add(id_1)                                        #   Add id_1 as a third-order friend
        net[person].friends[3] |= net[id_1].friends[0]                          #   Add all of id_1's friends as fourth-order friends
        
    net[id_2].friends[2] |= net[id_1].friends[1]                                # Adds all of id_1's second-order friends to id_2's set of third-order friends
    for person in net[id_1].friends[1]:                                         # For each of id_1's second-order friends:
        net[person].friends[2].add(id_2)                                        #   Add id_2 as a third-order friend
        net[person].friends[3] |= net[id_2].friends[0]                          #   Add all of id_2's friends as fourth-order friends
    
    net[id_1].friends[1] |= net[id_2].friends[0]                                # Adds all of id_2's friends to id_1's set of second-order friends
    for person in net[id_2].friends[0]:                                         # For each of id_2's friends:
        net[person].friends[1].add(id_1)                                        #   Add id_1 as a second-order friend
        net[person].friends[2] |= net[id_1].friends[0]                          #   Add id_1's friends as third-order friends
        net[person].friends[3] |= net[id_1].friends[1]                          #   Add id_1's second-order friends as fourth-order friends
        
    net[id_2].friends[1] |= net[id_1].friends[0]                                # Adds all of id_1's friends to id_2's set of second-order friends
    for person in net[id_1].friends[0]:                                         # For each of id_1's friends:
        net[person].friends[1].add(id_2)                                        #   Add id_2 as a second-order friend
        net[person].friends[2] |= net[id_2].friends[0]                          #   Add id_2's friends as third-order friends
        net[person].friends[3] |= net[id_2].friends[1]                          #   Add id_2's second-order friends as fourth-order friends
        
    net[id_1].friends[0].add(id_2)                                              # Add id_2 as id_1's friend
    net[id_2].friends[0].add(id_1)                                              # Add id_1 as id_2's friend
    
    for friends_set in list(net[id_1].friends + [net[id_2].friends[3]]):        # Removes redundant entries in sets. Only id_2's fourth-order set needs to be added,
        for person in list(friends_set):                                        #   since all of their third-order and lower friends are now included in id_1's sets
            net[person].collapse(person)
    net[id_1].collapse(id_1)                                                    # Collapses id_1 itself


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
network = {}                                                                    # The dictionary of client ids and their Unique_id instance
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
        out3.write(network[id_1].verification_4x(id_2))
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

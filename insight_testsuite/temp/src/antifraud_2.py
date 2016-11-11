### Fraud Detection System, version 2 ###
#
# This code is simpler and faster than version 1. HOWEVER, the bulk of the
#   calculations happen between when a costumer makes a payment request and
#   the code desides whether or not to flag it. If minimizing this time is
#   a lexical priority to data usage / total run time, consider using versions
#   1 or 1.5 instead.
#
#
# Basic outline:
#
# The code creates a dictionary called 'network' containing an entry for each
#   unique costumer id. The value attached this entry is the set of ids
#   corresponding to the people that person has transacted with ('friends').
#
# While reading the batch file, with each transaction both participants are
#   simply added to each other's friends sets.
#
# While reading the stream file, with each new transaction the code checks
#   whether the participants are already friends, then checks if the
#   intersection of their friend sets is non-empty (i.e. they have a mutual
#   friend, i.e. they are second-order friends), and if that fails finally
#   constructs sets of the union of each participant's first- and second-order
#   friends and sees if there is any overlap (which would make them third- or
#   fourth-order friends). Outputs are recorded and last of all the participants
#   are added to each other's friends sets for future transactions (since we are
#   assuming each transaction becomes a new, valid payment record after it is
#   processed).


import sys
import csv


# Input files
try:
    batch_in = sys.argv[1]                                                      # Batch input payments
    stream_in = sys.argv[2]                                                     # Stream input payments
    out_1 = sys.argv[3]                                                         # Feature 1 output
    out_2 = sys.argv[4]                                                         # Feature 2 output
    out_3 = sys.argv[5]                                                         # Feature 3 output
except:
    sys.exit("Input failed. Please check command line syntax")


# Read batch file
network = {}                                                                    # The dictionary containing costumer ids and their friends sets

with open(batch_in,'rU') as batch_file:                                         # Opening with 'rU' instead of 'r' circumvents a bug related to newline characters in csv module
    batch_connections = csv.DictReader(batch_file, skipinitialspace = True)
    for row in batch_connections:                                               
        # For each row in the batch file:
        
        # See if the id1 and id2 elements of the csv file are integers and create simple references
        try:                                                                    
            id_1 = int(row['id1'])
            id_2 = int(row['id2'])
        except ValueError:
            # Send error message and skip rows that do not contain integer ids
            print("(In batch_payments) id field does not contain an integer! "+
            "Ignoring this entry... id1 contains the following string:\n" +
            row['id1'])                                                         # Outputs the string for debugging
            continue
        
        # If a dictionary entry does not yet exist for one of the participants, create it and initialize its value as an empty set
        if (not network.has_key(id_1)):
            network[id_1] = set()
            
        if (not network.has_key(id_2)):
            network[id_2] = set() 
        
        # Add each participant to the other's friends set
        network[id_1].add(id_2)
        network[id_2].add(id_1)
        

# Read stream file
out1 = open(out_1,'w')
out2 = open(out_2,'w')
out3 = open(out_3,'w')

second_degree_1 = set()                                                         # Initialize second degree sets for later use
second_degree_2 = set()

with open(stream_in,'rU') as stream_file:                                       # Opening with 'rU' instead of 'r' circumvents a bug related to newline characters in csv module
    stream = csv.DictReader(stream_file, skipinitialspace = True)  
    for row in stream:
        # For each row in the stream file:
        
        # See if the id1 and id2 elements of the csv file are integers and create simple references
        try:
            id_1 = int(row['id1'])
            id_2 = int(row['id2'])
        except ValueError:
            # Send error message and skip rows that do not contain integer ids
            print("(In stream_payments) id field does not contain an integer! "+
            "Ignoring this entry... id1 contains the following string:\n" +
            row['id1'])                                                         # Outputs the string for debugging
            continue
        
        # If a dictionary entry does not yet exist for one of the participants, create it and initialize its value as an empty set
        if (not network.has_key(id_1)):
            network[id_1] = set()
            
        if (not network.has_key(id_2)):
            network[id_2] = set() 
        
        # Check if friends
        if (id_2 in network[id_1]):
            out1.write('trusted\n')
            out2.write('trusted\n')
            out3.write('trusted\n')
        
        # Else check if friends of friends
        elif (len(network[id_1] & network[id_2]) > 0):                          # If the intersection of participant's friends sets are non-empty, they have at least one mutual friend
            out1.write('unverified\n')
            out2.write('trusted\n')
            out3.write('trusted\n')
            
        # Else check if third- or fourth-order friends
        else:
            out1.write('unverified\n')
            out2.write('unverified\n')
            
            second_degree_1 = network[id_1].copy()                              # Creates copy of id_1's friends set
            for friend in network[id_1]:                                        # For each of id_1's friends:
                second_degree_1 |= network[friend]                              #   Add their friends sets to second_degree_1. second_degree_1 thus contains all of id_1's first- and second-order friends
                
            second_degree_2 = network[id_2].copy()                              # Repeat for id_2
            for friend in network[id_2]:
                second_degree_2 |= network[friend]
                
            if (len(second_degree_1 & second_degree_2) > 0):                    # Checks for overlap between second degree friends sets
                out3.write('trusted\n')
            else:
                out3.write('unverified\n')
                
            second_degree_1.clear()                                             # Clear sets for future cycles
            second_degree_2.clear()
        
        
        # Here input the code to get verification from the customer, if needed.
        # If verification withheld, flag as spam and continue. Else:
        
        # Since a valid transaction has occured between id_1 and id_2, add them to one another's friends sets
        network[id_1].add(id_2)                                                 
        network[id_2].add(id_1)

# Close output files
out1.close()
out2.close()
out3.close()
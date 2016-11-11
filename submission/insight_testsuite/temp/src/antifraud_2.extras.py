### Fraud Detection System, version 2 with extras ###
#
# This code is equivalent to version 2, except with some extra features for
#   different means of fraud detection. Additionally, to accomodate for multiple
#   methods of fraud detection, I have changed the binary trusted / unverified
#   output into an integer representing the degree of untrustworthiness of a
#   given transaction. There is thus only a single output file for this program,
#   each line of which gives the calculated untrustworthiness of the
#   corresponding line in stream_payments.csv.
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


# DISCUSS:  Note that from setup of PayMo, users request payments from others. Thus id2 is the one both sending the request and recieving the money
# Obviously one-sided suspicion

#  ____FLAG EVERYTHING BY EXTRA_____

import sys
import csv
import datetime

# Class containing client information. Can be considered a client's 'account'
class Unique_id:
    
    def __init__(self):
        self.friends = set()                                                    # List of client's previous transaction partners
        self.fraud_score = 0                                                    # Measure of how much this client is suspected of fraud/scamming, used in multiple Extras
        self.five_transactions_ago = datetime(1,1,1,1,0,0)                      # The timestamp of the fifth-previous transaction, for Extra 1b
        self.four_transactions_ago = datetime(1,1,1,1,0,0)                      # The timestamp of the fourth-previous transaction, for Extra 1b
        self.three_transactions_ago = datetime(1,1,1,1,0,0)                     # The timestamp of the third-previous transaction, for Extra 1b
        self.two_transactions_ago = datetime(1,1,1,1,0,0)                       # The timestamp of the second-previous transaction, for Extra 1b
        self.last_transaction = datetime(1,1,1,1,0,0)                           # The timestamp of the previous transaction, for Extra 1b
        self.big_transactions_count = 0                                         # The number of large transactions the account has been part of, for Extra 3
        self.transactions_take_count_today = 0                                  # The number of transaction requests the accound has sent (i.e. requests to be paid) today (NOTE: count only resets on new transaction), for Extra 1a.1
        self.transactions_give_count_today = 0                                  # The number of transaction requests the accound has recieved (i.e. requests for them to pay) today (NOTE: count only resets on new transaction), for Extra 1a.2
#        self.crime_flags = 0
        self.suspected_scammer = 0                                              # Whether or not an account has been manually flagged as a scammer, for Extra 4
        self.verified = 0                                                       # Whether or not an account has been verified, for Extra 0
        self.clean_transactions_count = 0                                       # The number of 'clean' transactions the account has participated in sequentially, for Extra 2
    
    # Extra 1: A variety of fraud detection algorithms based on the timing and
    #   frequency of payment requests.
    def tick(self,current,give_take):                                           # give_take = 1 for the person giving money, 0 for person receiving
        c_time = datetime.strptime(current, "%d-%m-%y %H:%M:%S")
        
        if (not c_time.day == self.last_transaction.day):
            self.transactions_give_count_today = 0
            self.transactions_take_count_today = 0
        
        # Increment appropriate daily counter
        if (give_take):
            self.transactions_give_count_today += 1
        else:
            self.transactions_take_count_today += 1

        # Extra 1a.1: We have found that customers who send more than 10
        #   payment requests in a day are frequently scammer accounts. This
        #   implementation increments the id's fraud score for the 11th payment
        #   request each day, and every payment request thereafter
        if (self.transactions_take_count_today > 10):
            self.fraud_score += 1

        # Extra 1a.2: We have found that customers who receive more than 50
        #   payment offers in a day are frequently associated with scammers 
        #   (since several scammer bot accounts will send their money to one 
        #   centralized depository). This implimentation increments the id's
        #   fraud score for the 51st daily recieve transaction and every 3
        #   transactions thereafter (until the next day). NOTE: it might make
        #   more sense to give such "bank" accounts a unique flag.
        if (self.transactions_give_count_today > 50 and 
        self.transactions_give_count_today % 3 == 0):
            self.fraud_score += 1

        # Extra 1b: We have found that scammer accounts frequently make many
        #   transactions (both sending and receiving) in short time frames. This
        #   implementation increases fraud score every time five transactions
        #   are made within 10 seconds of eachother.
        if ((c_time - self.five_transactions_ago).total_seconds() < 10):
            self.fraud_score += 1
        
        # Ticks time recordings for Extra 1b
        self.five_transactions_ago = self.four_transactions_ago
        self.four_transactions_ago = self.three_transactions_ago
        self.three_transactions_ago = self.two_transactions_ago
        self.two_transactions_ago = self.last_transaction
        self.last_transaction = current
        
        
    # Extra 2: Making four transactions in a row which don't trigger any fraud
    #   detection algorithms makes a client account more trustworthy in general,
    #   reducing its fraud score (with a minimum score of 0).
    def fraud_reducer(initial):                                                 # This subroutine is called at the end of a transaction. Variable 'initial' is the account's fraud score on entering the transaction
        if (initial == self.fraud_score):
            self.clean_transactions_count += 1
            if (self.clean_transactions_count >= 4):
                self.clean_transactions_count = 0
                self.fraud_score = max(self.fraud_score-1,0)
        else:
            self.clean_transactions_count = 0                                   # A suspicious transaction resets the counter
    
    # Extra 3: Marketing has decided to implement a rewards system. After
    #   participating in 20 'large' transactions (either as sender or reciever),
    #   accounts are given a one-time award of 5 dollars. This is implemented by
    #   writing to a new file (saved as a global variable), which is read after
    #   stream_payments. Note that this program began between the periods
    #   covered by the two input files.
    def account_rewards(id):
        self.big_transactions_count += 1
        if (self.big_transactions_count == 20):
            rewards_writer.writerow([datetime.utcnow().isoformat(sep = ' '), 0, # 0 is the id of PayMo itself
            id,' 5.00',' Thank you for being a loyal customer!'])

### Main code ###

## Input files
try:
    batch_in = sys.argv[1]                                                      # Batch input payments
    stream_in = sys.argv[2]                                                     # Stream input payments
    out_file = sys.argv[3]                                                      # Trustworthiness output
    rewards_file = sys.argv[4]                                                  # Extra 3 rewards file
except:
    sys.exit("Input failed. Please check command line syntax")


# Extra 0: We have implemented a program where buisnesses can get their accounts
#   verified. All requests from verified accounts are assumed to be trustworthy.
#   However, since thousands or even millions of people might have transactions
#   with certain buisnesses, it's been decided that connections through verified
#   accounts don't contribute to 'friendship' chains. I'm hard-coding the list
#   here, but it could just as easily be imported from a file.
verified_accounts = set([6101,1023,67385,18768,22467])
for account in verified_accounts:
    if (not network.has_key(account)):                                           # With the final placement of this section the if command is superfluous. I'm leaving it in since the time cost is negligible and if things change again it could prevent a nasty (and hard to trace) bug
        network[account] = Unique_id()                                           
    network[account].verified = 1


## Read batch file
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
        
        # If the account requesting the payment is verified, the transaction
        #   doesn't generate friendships.
        if (network[id_1].verified == 1 or network[id_2].verified == 1):
            continue
        
        # If a dictionary entry does not yet exist for one of the participants,
        #   create it and initialize its value as an empty set
        if (not network.has_key(id_1)):
            network[id_1] = Unique_id()
        if (not network.has_key(id_2)):
            network[id_2] = Unique_id() 
        
        # Add each participant to the other's friends set
        network[id_1].friends.add(id_2)
        network[id_2].friends.add(id_1)
        

## Read stream file
out = open(out_file,'w')

# Open rewards file for Extra 3
rewards = open(rewards_file,'w',newline='')
global rewards_writer = csv.writer(rewards)
rewards_writer.writerow(['time',' id1',' id2',' amount',' message'])

# Extra 4: In addition to the fraud score, we have manually flagged certain
#   accounts as suspected scammers. I'm hard-coding this here, but it could just
#   as easily be imported from a file.
suspects = set([49594,20681,78285,20400,2316])
for person in suspects:
    if (not network.has_key(person)):
        network[person] = Unique_id()                                           # Not sure how we could suspect someone of being a scammer before they made any transactions... Guess our precrime division is amazing!
    network[person].suspected_scammer = 1

# Extra 5: Don't ask us why, but the data analysis team has discovered that
#   scammers frequently make requests for payments where the cent value is
#   certain specific amounts. Again I'm hard-coding the amounts, but they could
#   be read as well.
suspicious_amounts = set([3,47,62,94])

second_degree_1 = set()                                                         # Initialize second degree sets for later use
second_degree_2 = set()

untrust = 0                                                                     # Initialize untrustworthiness variable
id_1_initial_fraud = 0                                                          # Initialize fraud scores on entering transaction, for Extra 2
id_2_initial_fraud = 0

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
        
        # Unpack rest of data
        try:
            amount = map(in,row['amount'].split("."))                           # Amount is now an integer list. amount[0] is the number of dollars and amount[1] is the number of cents requested
            time_stamp = row['time'])                                           # Note that time_stamp is an iso-formatted string (with ' ' as the separator), not a datetime() object
            message = row['message']
            if (not row[None]):                                                 # If there is more data, i.e. the message itself had a comma
                message = message + "," + ",".join(row[None])                   # Recombine the entire
        except:
            print("(In stream_payments) Read error, skipping entry\n")
            continue
        
        # If the account requesting payment is verified (Extra 0), the
        #   transaction is automatically trusted and no friendships are updated.
        #   Both participants are still eligible for the awards program though 
        #   (Extra 3).
        if (network[id_2].verified == 1):
            continue
        
        # If a dictionary entry does not yet exist for one of the participants, create it and initialize its value as an empty set
        if (not network.has_key(id_1)):
            network[id_1] = Unique_id()
            
        if (not network.has_key(id_2)):
            network[id_2] = Unique_id() 
        
        # Record fraud scores on transaction entry
        id_1_initial_fraud = network[id_1].fraud_score
        id_2_initial_fraud = network[id_2].fraud_score
        
        # Check if friends
        if (id_2 in network[id_1].friends):
            untrust = 0
        
        # Else check if friends of friends
        elif (len(network[id_1].friends & network[id_2].friends) > 0):          # If the intersection of participant's friends sets are non-empty, they have at least one mutual friend
            untrust = 1
            
        # Else check if third- or fourth-order friends
        else:
            second_degree_1 = network[id_1].friends.copy()                      # Creates copy of id_1's friends set
            for person in network[id_1].friends:                                # For each of id_1's friends:
                second_degree_1 |= network[person].friends                      #   Add their friends sets to second_degree_1. second_degree_1 thus contains all of id_1's first- and second-order friends
                
            second_degree_2 = network[id_2].friends.copy()                      # Repeat for id_2
            for person in network[id_2]:
                second_degree_2 |= network[person].friends
                
            if (len(second_degree_1 & second_degree_2) > 0):                    # Checks for overlap between second degree friends sets
                untrust = 3
            else:
                untrust = 5
                
            second_degree_1.clear()                                             # Clear sets for future cycles
            second_degree_2.clear()
        
        # Apply Extra 1 methods to ids
        network[id_1].tick(time_stamp,1)
        network[id_2].tick(time_stamp,0)
        
        # Increase untrust if the money receiver (request sender) is a manually
        #   flagged scammer (Extra 4)
        if (network[id_2].suspected_scammer):
            untrust += 20
        
        # Increase untrust if cent amount suspicious (Extra 5)
        if (amount[1] in suspicious_amounts):
            untrust += 3


        # Increases untrust based on suspected scammer status of the money
        #   receiver (request sender)
        untrust += network[id_2].fraud_score        
        
        # Record transaction trustworthiness
        out.write('%d\n' % untrust)
        
        # Here input the code to get verification from the customer, if needed.
        # If verification withheld, flag as spam and continue. Else:
        
        # Since a valid transaction has occured between id_1 and id_2, add them
        #   to one another's friends sets
        network[id_1].add(id_2)                                                 
        network[id_2].add(id_1)
        
        # Run Extra 2 fraud reducer. This is coming after the untrust is
        #   measured, because better safe than sorry!
        network[id_1].fraud_reducer(id_1_initial_fraud)
        network[id_2].fraud_reducer(id_2_initial_fraud)
        
        # Run Extra 3 rewards program, if the transaction was for 2 dollars or
        #   more
        if (amount[0] >= 2):
            network[id_1].account_rewards(id_1)                                                 
            network[id_2].account_rewards(id_2)



#_______loop over rewards

# Close output files
out.close()
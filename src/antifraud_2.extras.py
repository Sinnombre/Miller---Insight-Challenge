### Fraud Detection System, version 2 with extras ###
#
# Version 2 of the Fraud Detection System, with some extra features
#
#
# Description:
#
# This code is equivalent to version 2, except with some extra features for
#   new means of fraud detection (and other things we can do with this data).
#   To accomodate for multiple methods of fraud detection, I have changed the
#   binary trusted / unverified output into an integer representing the degree
#   of untrustworthiness of a given transaction. There is thus only a single
#   output file for this program, each line of which gives the calculated
#   untrustworthiness of the corresponding line in stream_payments.csv.
#
#
# Basic outline:
#
# The code creates a dictionary 'network' containing an entry for each unique
#   costumer id. The value attached this entry is a User_account object
#   containing their friends set and a wealth of other information about their
#   PayMo transaction history.
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
#   fourth-order friends). This sets the basline untrustworthiness of the
#   transaction. A variety of new fraud detection methods (explained in the
#   code) are then employed, which further refine the untrustworthiness of the
#   transaction and flag User_accounts for suspicious behaviors. The final
#   untrustworthiness of the transaction is outputted, friends lists are updated
#   with the new transaction information.
#
#
# Extra Features:
# 0: A system where accounts that have gone through an external verification
#    are treated as trustworthy
# 1: A variety of checks flagging accounts which send / request requests with
#    suspicious frequencies
# 2: A means of mitigating the suspicion status of accounts after periods of
#    non-suspicious activity
# 3: A rewards program that makes a payment to returning customers
# 4: A system which increases the untrustworthiness of payment requests from
#    accounts that have been externally flagged for suspected fraud
# 5: A system which increases the untrustworthiness of transaction requests for
#    suspicious amounts
# 6: A system which increases the untrustworthiness of requests with no message
# 7: A system which flags and records accounts suspected of criminal activity
# 8: A system which raises suspicion of accounts that request the same amount
#    from different people several times in a row
#
#
# Side note on ids: From setup of PayMo, users request payments from others (or
#   at least that's how I read the instructions). Thus the user with id2 is both
#   sending the request and recieving the money. Obviously, that makes them
#   the one much more likely to be commiting fraud. The fact that amounts are 
#   specified by the receiver also makes fraud far more likely.


import sys
import csv
import datetime
import re

# Class containing client information. Can be considered a client's 'account'
class User_account:
    
    def __init__(self):
        self.friends = set()                                                    # List of client's previous transaction partners
        self.fraud_score = 0                                                    # Measure of how much this client is suspected of fraud/scamming, used in multiple Extras
        self.five_transactions_ago = datetime.datetime(1,1,1,1,0,0)             # The timestamp of the fifth-previous transaction, for Extra 1b
        self.four_transactions_ago = datetime.datetime(1,1,1,1,0,0)             # The timestamp of the fourth-previous transaction, for Extra 1b
        self.three_transactions_ago = datetime.datetime(1,1,1,1,0,0)            # The timestamp of the third-previous transaction, for Extra 1b
        self.two_transactions_ago = datetime.datetime(1,1,1,1,0,0)              # The timestamp of the second-previous transaction, for Extra 1b
        self.last_transaction = datetime.datetime(1,1,1,1,0,0)                  # The timestamp of the previous transaction, for Extra 1b
        self.big_transactions_count = 0                                         # The number of large transactions the account has been part of, for Extra 3
        self.transactions_take_count_today = 0                                  # The number of transaction requests the accound has sent (i.e. requests to be paid) today (NOTE: count only resets on new transaction), for Extra 1a.1
        self.transactions_give_count_today = 0                                  # The number of transaction requests the accound has recieved (i.e. requests for them to pay) today (NOTE: count only resets on new transaction), for Extra 1a.2
        self.crime_flags = 0                                                    # The number of transactions where this user has been flagged for possible illegal activity (Extra 7)
        self.suspected_scammer = 0                                              # Whether or not an account has been manually flagged as a scammer, for Extra 4
        self.verified = 0                                                       # Whether or not an account has been verified, for Extra 0
        self.clean_transactions_count = 0                                       # The number of 'clean' transactions the account has participated in sequentially, for Extra 2
        self.last_requested_amount = '0.00'                                     # The last amount this client requested, for Extra 8
        self.request_targets = set()                                            # The targets of repeated requests, for Extra 8
    
    # Extra 1: A variety of fraud detection algorithms based on the timing and
    #   frequency of payment requests.
    def tick(self,current,give_take):                                           # give_take = 1 for the person giving money, 0 for person receiving
        c_time = datetime.datetime.strptime(current, "%Y-%m-%d %H:%M:%S")
        
        # If it's been a day since last transaction, reset daily counters
        if ((c_time - self.last_transaction).days > 1):
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
        if (self.transactions_take_count_today > 10 and not give_take):
            self.fraud_score += 1

        # Extra 1a.2: We have found that customers who receive more than 50
        #   payment offers in a day are frequently associated with scammers 
        #   (since several scammer bot accounts will send their money to one 
        #   centralized depository). This implimentation increments the id's
        #   fraud score for the 51st daily recieve transaction and every 3
        #   transactions thereafter (until the next day). NOTE: It might make
        #   more sense to give such "bank" accounts a unique flag.
        if (self.transactions_give_count_today > 50 and 
        self.transactions_give_count_today % 3 == 0 and
        give_take):
            self.fraud_score += 1

        # Extra 1b: We have found that scammer accounts frequently make many
        #   transactions (both sending and receiving) in short time frames. This
        #   implementation increases fraud score every time six transactions
        #   are made within 10 seconds of eachother.
        if ((c_time - self.five_transactions_ago).total_seconds() < 10):
            self.fraud_score += 1
        
        # Ticks time recordings for Extra 1b
        self.five_transactions_ago = self.four_transactions_ago
        self.four_transactions_ago = self.three_transactions_ago
        self.three_transactions_ago = self.two_transactions_ago
        self.two_transactions_ago = self.last_transaction
        self.last_transaction = c_time
        
        
    # Extra 2: Making four transactions in a row which don't trigger any fraud
    #   detection algorithms makes a client account more trustworthy in general,
    #   reducing its fraud score (with a minimum score of 0).
    def fraud_reducer(self,initial):                                            # This subroutine is called at the end of a transaction. Variable 'initial' is the account's fraud score on entering the transaction
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
    #   writing to a new file, which is read after stream_payments. Note that 
    #   this program began between the periods covered by the two input files.
    def account_rewards(self,id,rewards_writer):
        self.big_transactions_count += 1
        if (self.big_transactions_count == 20):
            rewards_writer.writerow([
            datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),' 0',      # 0 is the id of PayMo itself
            ' %d' % id,' 5.00',' Thank you for using PayMo! Here is a special' +
            ' gift for our loyal customers!'])


### Main code ###

## Input files
try:
    batch_in = sys.argv[1]                                                      # Batch input payments
    stream_in = sys.argv[2]                                                     # Stream input payments
    out_file = sys.argv[3]                                                      # Trustworthiness output
    rewards_file = sys.argv[4]                                                  # Extra 3 rewards file
    suspects_file = sys.argv[5]                                                 # Extra 7 suspects file
except:
    sys.exit("Input failed. Please check command line syntax")

network = {}                                                                    # The dictionary containing costumer ids and their friends sets

# Extra 0: We have implemented a program where buisnesses can get their accounts
#   verified. All requests from verified accounts are assumed to be trustworthy.
#   However, since thousands or even millions of people might have transactions
#   with certain buisnesses, it's been decided that connections through verified
#   accounts don't contribute to 'friendship' chains. I'm hard-coding the list
#   here, but it could just as easily be imported from a file.
verified_accounts = set([6101,1023,67385,18768,22467])
for account in verified_accounts:
    if (not network.has_key(account)):                                          # With the final placement of this section the if command is superfluous. I'm leaving it in since the time cost is negligible and if things change again it could prevent a nasty (and hard to trace) bug
        network[account] = User_account()                                           
    network[account].verified = 1


## Read batch file
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
        #   create it and initialize its value as an empty set
        if (not network.has_key(id_1)):
            network[id_1] = User_account()
        if (not network.has_key(id_2)):
            network[id_2] = User_account() 
        
        # If the account requesting the payment is verified, the transaction
        #   doesn't generate friendships.
        if (network[id_1].verified == 1 or network[id_2].verified == 1):
            continue
        
        # Add each participant to the other's friends set
        network[id_1].friends.add(id_2)
        network[id_2].friends.add(id_1)
        

## Read stream file
out = open(out_file,'w')

# Open rewards file for Extra 3
rewards = open(rewards_file,'w')
rewards_writer = csv.writer(rewards)
rewards_writer.writerow(['time',' id1',' id2',' amount',' message'])

# Extra 4: In addition to the fraud score, we have manually flagged certain
#   accounts as suspected scammers. I'm hard-coding this here, but it could just
#   as easily be imported from a file.
suspects = set([49594,20681,78285,20400,2316])
for person in suspects:
    if (not network.has_key(person)):
        network[person] = User_account()                                        # Not sure how we could suspect someone of being a scammer before they made any transactions... Guess our precrime division is amazing! (Or I copied these ids from stream and can't be positive they occured in batch...)
    network[person].suspected_scammer = 1

# Extra 5: Don't ask us why, but the data analysis team has discovered that
#   scammers frequently make requests for payments where the cent value is
#   certain specific amounts. Again I'm hard-coding the amounts, but they could
#   be read as well.
suspicious_amounts = set([3,47,62,94])

# Extra 7: The FBI suspects PayMo is being used to transfer money during illicit
#   purchases (oh my!). They have come to us with a court order requiring that
#   we turn over the account information of people using certain words in
#   payment messages. We will do this by first flagging accounts for using these
#   'bad' words, then later printing out a list of account ids for the FBI. Note
#   that the bad words list uses regular expressions
bad_words = set([r'[Ww]ee+d',r'[Dd]ru+gs',r'[Rr]estore.*[Rr][Ee][Ii][Cc][Hh]']) # Yes, that last one appears 7 times in our data set...


second_degree_1 = set()                                                         # Initialize second degree sets for later use
second_degree_2 = set()
row_number = 1                                                                  # Row numbering starts at 2 (increments at beginning of loop) so that row_number lines up with files, which contain header line

untrust = 0                                                                     # Initialize untrustworthiness variable
id_1_initial_fraud = 0                                                          # Initialize fraud scores on entering transaction, for Extra 2
id_2_initial_fraud = 0

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
        
        # Unpack rest of data
        try:
            amount = map(int,row['amount'].split("."))                          # amount is now an integer list. amount[0] is the number of dollars and amount[1] is the number of cents requested
            time_stamp = row['time']                                            # Note that time_stamp is an iso-formatted string (with ' ' as the separator), not a datetime() object
            message = row['message']
            try:
                message = message + ", " + ", ".join(row[None])                 # If there is more data, i.e. the message itself had a comma, this will recombine the entire message. If the message has a \r linebreak, it will still not be included. NOTE: If the original message did not put a space after a comma, this implementation will add one. This seems like too minor of a problem to bother with for now, but keep in mind if it ever becomes an issue
            except:
                pass
        except:
            print("(In stream_payments) Read error, skipping entry. Message:\n")
            print row['message']                                                # Output for debugging
            continue

        # If a dictionary entry does not yet exist for one of the participants, 
        #   create it and initialize its value as an empty instance of
        #   User_account
        if (not network.has_key(id_1)):
            network[id_1] = User_account()
            
        if (not network.has_key(id_2)):
            network[id_2] = User_account() 
        
        # If the account requesting payment is verified (Extra 0), the
        #   transaction is automatically trusted and no friendships are updated.
        #   Both participants are still eligible for the awards program though 
        #   (Extra 3).
        if (network[id_2].verified == 1):
            out.write('0\n')
            if (amount[0] >= 2):
                network[id_1].account_rewards(id_1,rewards_writer)                                                 
                network[id_2].account_rewards(id_2,rewards_writer)
            continue
        
        # Record fraud scores on transaction entry, for Extra 2
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
            for person in network[id_2].friends:
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
        
        # Extra 6: We have found that payment requests with no messages attached
        #   (or where the message is only spaces) are often fraudulent. This
        #   raises the untrust accordingly.
        if (len(set(message) - set([' '])) == 0):
            untrust += 4
            
        # Scan messages for the bad words (Extra 7)
        for phrase in bad_words:
            if (re.search(phrase,message)):
                network[id_1].crime_flags += 1
                network[id_2].crime_flags += 1
        
        # Extra 8: We have determined that scammers frequently request the same
        #   amount repeatedly. However, many people also use PayMo for recurring
        #   payments, e.g. rent, which is also in the same amount each time.
        #   Thus, we have decided to flag accounts that request the same amount
        #   repeatedly, but only if its from different people.
        if (row['amount'] == network[id_2].last_requested_amount):
            if(len(network[id_2].request_targets) >= 5 and 
            not (id_1 in network[id_2].request_targets)):
                network[id_2].fraud_score += 3
            network[id_2].request_targets.add(id_1)
        else:
            network[id_2].request_targets.clear()
            network[id_2].last_requested_amount = row['amount']
            network[id_2].request_targets.add(id_1)
 
        # Increases untrust based on fraud score of the money receiver
        #   (request sender)
        untrust += network[id_2].fraud_score        
        
        # Record transaction trustworthiness
        out.write('%d\n' % untrust)
        
        # Here insert the code to get verification from the customer, if needed.
        # If verification withheld, flag as spam and continue. Else:
        
        # Run Extra 2 fraud reducer. This is coming after the untrust is
        #   measured, because better safe than sorry!
        network[id_1].fraud_reducer(id_1_initial_fraud)
        network[id_2].fraud_reducer(id_2_initial_fraud)
        
        # Run Extra 3 rewards program, if the transaction was for 2 dollars or
        #   more
        if (amount[0] >= 2):
            network[id_1].account_rewards(id_1,rewards_writer)                                                 
            network[id_2].account_rewards(id_2,rewards_writer)
        
        # If the account payment is requested from is verified (Extra 0),
        #   friendships are not updated. However, since verified accounts can
        #   still be the victims of fraud, this check comes at the end of the
        #   loop.
        if (network[id_1].verified == 1):
            continue
        
        # Since a valid transaction has occured between id_1 and id_2, add them
        #   to one another's friends sets
        network[id_1].friends.add(id_2)                                                 
        network[id_2].friends.add(id_1)
        
        
# Process rewards payments (Extra 3)
rewards.close()
with open(rewards_file,'rU') as rewards:                                        # Opening with 'rU' instead of 'r' circumvents a bug related to newline characters in csv module
    rew = csv.DictReader(rewards, skipinitialspace = True)
    for row in rew:
        # Because we know these payments come from us, they are automatically
        #   trusted and don't generate friendships or other Extras features
        out.write('0\n')

# Close output files
out.close()

# Save suspects list for FBI (Extra 7)
with open(suspects_file,'w') as suspects:
    for id in network:
        if (network[id].crime_flags >= 3):
            suspects.write('%d\n' % id)
        
    

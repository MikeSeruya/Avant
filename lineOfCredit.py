# -*- coding: utf-8 -*-
"""
Runs a simulation of the database and calculates interest over the time period
@author: Mike Seruya
"""
import sqlite3
import sys
import datetime
from tabulate import tabulate

# currrent date of database is 30 days ago
databaseDate = datetime.date.today() - datetime.timedelta(days=30)

def calcInterest(principal, apr, numOfDays):
    """Calculate interest over number of days, apr example 24.99%
    should be entered as 24.99"""
    return principal * ((apr/100.00) / 365.00 ) * numOfDays;
    
def advanceDatabase(setDate):
    """updates the state of the database to the given date in the future"""
    if databaseDate >= setDate:
        print "Date in the past, current databaseDate: " + databaseDate
        sys.exit(1)
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # select all accounts where there is an outstanding balance
        cur.execute("SELECT AccountNum, apr, Principal, AccountCreationDate\
                    FROM Users where Principal > 0")
        accounts = cur.fetchall()
        # calculate how many days since current database date
        daysPassed = (setDate - databaseDate).days
        # 
        daysAgo = setDate - datetime.timedelta(days=daysPassed)
        for day in range(daysPassed):
            for account in accounts:
                cur.execute("SELECT Amount, Balance, TransDate FROM\
                            Transactions where AccountNum=? and \
                            TransDate >= ?" ,(account[0], daysAgo))
                dateCheck = (databaseDate + datetime.timedelta(days=day) - \
                   datetime.datetime.strptime(str(account[3]), "%Y-%m-%d").date()).days % 30
                if dateCheck == 0: # if billing date calculate interest
                    values = cur.fetchall()
                    if len(values) == 0:
                        interest = round(calcInterest(account[2], account[1], \
                                    daysPassed),2)
                        cur.execute("UPDATE Users SET Interest=Interest+? WHERE \
                                    AccountNum=?",(interest,account[0]))
                    elif len(values) == 1:
                        transDate = datetime.datetime.strptime(str(values[0][2]), \
                                    "%Y-%m-%d").date()
                        interest = abs(round(calcInterest(values[0][0], account[1], \
                                    daysPassed),2))     
                        cur.execute("UPDATE Users SET Interest=Interest+? WHERE \
                                    AccountNum=?", (interest,account[0]))
                    else:
                        for rowNum in range(len(values) - 1):
                            transDate = datetime.datetime.strptime(str(values[rowNum][2]), \
                                        "%Y-%m-%d").date()
                            transDate2 = datetime.datetime.strptime(str(values[rowNum+1][2]), \
                                        "%Y-%m-%d").date()
                            interest = abs(round(calcInterest(values[0][0], account[1], \
                                        (transDate2 - transDate).days),2))
                            cur.execute("UPDATE Users SET Interest=Interest+? \
                                        WHERE AccountNum=?",(interest,account[0]))
            
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()
    return 0;

def newTransaction(accountNum, amount, transDate):
    """Process a new transaction - negative amounts are considered
    withdrawls and positive amounts are payments"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        cur.execute("SELECT Principal, Interest, creditLimit FROM Users WHERE \
                    AccountNum=?",(accountNum,))
        row = cur.fetchone()
        if row == "":
            #if no account exit
            print("Account not found")
            sys.exit(1)
        uPrincipal = row[0]
        uInterest = row[1]
        uCreditLimit = row[2]
        uBalance = uPrincipal + uInterest
        uAvailable = uCreditLimit - uBalance
        newTotal = uBalance - amount
        # check if there is available funds
        if uAvailable <= 0:
            print "Declined: Account has no available funds"
        #check if the new transaction will exceed the credit limit
        elif newTotal > uCreditLimit:
            print "Declined: Requested transaction amount:"+str(amount)+", \
                   exceeds current available balance:"+str(uAvailable)
        # create new entry on transactions table
        else:
            cur.execute("INSERT INTO Transactions(AccountNum, Amount, Balance, TransDate) \
                    VALUES(?, ?, ?, ?)", (accountNum, amount, newTotal, transDate))
        # update prinicpal balance on users table
        if amount > 0 and uInterest > 0 and uInterest - amount > 0:
            # payment and amount does not cover interest
            cur.execute("UPDATE Users SET Interest=Interest-? \
                        WHERE AccountNum=?",(amount,accountNum))
        if amount > 0 and uInterest > 0 and uInterest - amount <= 0:
            # payment amount covers interest
            cur.execute("UPDATE Users SET Interest=0, Principal=? \
                        WHERE AccountNum=?",(amount-uInterest,accountNum))
        else:
            # withdrawl
            cur.execute("UPDATE Users SET Principal=Principal-? \
                        WHERE AccountNum=?",(amount,accountNum))
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()

def buildDatabase():
    """Creates the database and tables for storing users and transactions"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # create Users and Transactions tables
        cur.execute("CREATE TABLE Users(AccountNum INTEGER primary key NOT NULL,\
             Name varchar NOT NULL, Principal DECIMAL NOT NULL, Interest DECIMAL NOT NULL, \
             APR DECIMAL NOT NULL, AccountCreationDate DATE, creditLimit DECIMAL NOT NULL CHECK(Principal <= creditLimit))")
        cur.execute("CREATE TABLE Transactions( \
             TransNumber INTEGER PRIMARY KEY NOT NULL,\
             AccountNum INTEGER, Amount DECIMAL, Balance DECIMAL, TransDate DATE)")
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()
            
def clearDatabase():
    """Drop all tables to clear out database"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # drop both tables
        cur.execute("DROP TABLE IF EXISTS Users")
        cur.execute("DROP TABLE IF EXISTS Transactions")
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()

def newAccount(accountNum, name, apr, accountCreationDate, creditLimit):
    """Add new account to database"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # create new account
        cur.execute("INSERT into Users VALUES(?, ?, ?, ?, ?, ?, ?)", \
            (accountNum, name, 0, 0, apr, accountCreationDate, creditLimit))
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()

def showUsersDatabase():
    """Prints Users Database for testing purposes"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # select all records from Users and print
        cur.execute("SELECT * FROM Users")
        print tabulate(cur.fetchall(), headers=['Account ID', 'Name', \
            'Principal', 'Interest', 'APR', 'Account Created', 'Limit'])
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()
            
def showTransactionsDatabase():
    """Prints Transactions database for testing purposes"""
    try:
        # open sql database
        con = sqlite3.connect("lineOfCredit.db")
        cur = con.cursor()
        # select all records from Transactions and print
        cur.execute("SELECT * FROM Transactions")
        print tabulate(cur.fetchall(), headers=['Transaction ID', 'Account ID', \
            'Amount', 'Balance', 'Date'])
        con.commit()
        
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if con:
            con.close()
            
clearDatabase()
buildDatabase()
newAccount(111, "Bob", 35.00, \
                datetime.date.today() - datetime.timedelta(days=30), 10000)
newAccount(112, "Leonardo", 10.00, \
                datetime.date.today() - datetime.timedelta(days=45), 1000)
newAccount(113, "Bruce Wayne", 15.00, \
                datetime.date.today() - datetime.timedelta(days=17), 5000)
newAccount(114, "Jon", 35.00, \
                datetime.date.today() - datetime.timedelta(days=30), 500)
newAccount(115, "Bill", 10.00, \
                datetime.date.today() - datetime.timedelta(days=50), 1000)
newTransaction(114, -500, datetime.date.today() - datetime.timedelta(days=30))
newTransaction(111, -500, datetime.date.today() - datetime.timedelta(days=30))
newTransaction(111, 200, datetime.date.today() - datetime.timedelta(days=15))
newTransaction(111, -100, datetime.date.today() - datetime.timedelta(days=5))
newTransaction(113, -4000, datetime.date.today() - datetime.timedelta(days=17))
newTransaction(112, -100, datetime.date.today() - datetime.timedelta(days=45))
newTransaction(115, -700, datetime.date.today() - datetime.timedelta(days=50))
newTransaction(115, -100, datetime.date.today() - datetime.timedelta(days=30))
newTransaction(115, 200, datetime.date.today() - datetime.timedelta(days=15))
newTransaction(115, -100, datetime.date.today() - datetime.timedelta(days=5))
print "\nDatabase Beginning State on " + str(databaseDate) +"\n"
showUsersDatabase()
dateToAdvanceTo = datetime.date.today()
print "\nDatabase End State on " + str(dateToAdvanceTo) +"\n"
advanceDatabase(dateToAdvanceTo)
showUsersDatabase()
print "\nTransaction List\n"
showTransactionsDatabase()
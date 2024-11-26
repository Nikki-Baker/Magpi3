import mysql.connector
import random
import numpy as np
import re
import time
import bcrypt


print("db is running")


def connect():
    """connect to mysql"""
    conn = mysql.connector.connect(host="127.0.0.1", port=3306,
                                   user="root", password="root",
                                   database="magpi3",
                                   autocommit=True,
                                   use_pure=True,
                                   charset="utf8")
    cur = conn.cursor(prepared=True)
    return conn, cur


if connect() is not None:
    print("successful db connection")
    print(f"connection :{connect()}")

else:
    print("Error 'connect() is None'")


def addUser(adminBool, fName, sName, email, lHandBool, passHash):
    """takes args and adds to db in the user table"""

    # data sanitization
    try:
        if adminBool:
            admin = 1
        else:
            admin = 0
        if lHandBool:
            lHand = 1
        else:
            lHand = 0

        # set up connection, define SQL, execute, retrieve result, and close connection
        conn, cur = connect()
        sql = "INSERT INTO `users` " \
              "(`UserID`, `Admin`, `Firstname`, `Surname`, `Email`, `LeftHanded`, `passHash`) " \
              "VALUES (NULL, %s, %s, %s, %s, %s, %s)"
        userVal = (admin, fName, sName, email, lHand, passHash)
        cur.execute(sql, userVal)
        conn.close()


    except Exception as e:
        print(f"Error :{e}")

    finally:
        if conn is not None:
            conn.close()


def bandUser():
    """puts users into bands based on their best 10 of last 12 shoots to compare with data of similar level user"""
    # not currently used, used in earlier version, was going to be used to compare users agains eachother

    try:
        BANDRETRIVELIMIT = 12  # how many targets will be considered (per user) to calculate the band
        BANDRETRIVEBEST = 10
        con, cur = connect()
        max = highestUserID()

        # looks at scores to determine band
        scoreArr = []
        userAvgs = []
        for userID in range(1, max + 1):
            # gets user avg scores in last N shoots
            sqlRetrive = 'SELECT AVG(`scoreLimit`.`score`) FROM ' \
                         '( SELECT * FROM (SELECT `score` FROM `target` INNER JOIN `shootsrelational` ' \
                         'ON `target`.`targetID` = `shootsrelational`.`targetID` WHERE ' \
                         '`shootsRelational`.`userID` = %s ORDER BY `dateShot` DESC LIMIT %s) AS dateLimit ORDER BY ' \
                         '`dateLimit`.`score` DESC LIMIT %s) AS scoreLimit'

            cur.execute(sqlRetrive, [userID, BANDRETRIVEBEST, BANDRETRIVELIMIT])
            score = cur.fetchall()
            # data cleaning
            score = str(score).strip("(),\'[]Decimal")
            if score == "Non":
                score = 0
            scoreArr.append(float(score))
            userAvgs.append((userID, score))

        scoreArr.sort()

        # put users into band

        # works out where the boundries are for the 20th, 40th, 60th, and 80th percentile is
        length = len(scoreArr)

        boundryIndex = []
        boundryValues = []
        for i in range(1, 5):
            # calculates the boundries for
            boundry = length * ((20 * i) / 100)  # finds the position of the boundry
            boundry = boundry.__round__()  # rounds it to nearest int to find index
            boundryIndex.append(boundry)  # adds index to arr
            boundryValues.append(scoreArr[boundry])  # finds boundry value and adds to arr

        # bound users

        # determins a users band
        for i in range(len(userAvgs)):  # increments through all stored avgs + ID pairs
            userID = float(userAvgs[i][0])  # gets user id from arr
            avg = float(userAvgs[i][1])  # gets user avg

            band = 1  # if lower than all band boundries user will stay in the default band of 1
            for i in range(4):
                if avg >= boundryValues[
                    i]:  # if user is above a band boundry they will get moved up untill they are not
                    band = i + 2  # +1 because it is index not position, +1 again as it is above the boundry

            # puts user into band
            sqlBandUpdate = 'UPDATE `users` SET `band` = %s WHERE `users`.`UserID` = %s'
            cur.execute(sqlBandUpdate, [band, userID])

            con.close()

    except Exception as e:
        print(f"Error :{e}")

    finally:
        if con is not None:
            con.close()


def selectUsersFromBand(band):
    """selects all user ID's in a given band"""
    # not currently used, used in earlier version, was going to be used to compare users against each other

    try:
        con, cur = connect()

        sqlBandRetrive = 'SELECT `UserID` FROM `users` WHERE `band` = %s'
        cur.execute(sqlBandRetrive, [band])
        users = cur.fetchall()

        # cleaning
        users = [int(str(item).strip(("(),\'[]"))) for item in users]  # mfw list comprehension

        return users

        con.close()

    except Exception as e:
        print(f"Error :{e}")

    finally:
        if con is not None:
            con.close()


# reformat 2d vector array into 1d and adds the score to the front
def vectorArrayReformat(score, diagramVectorArray):
    """reformat vector arr for use"""
    reformattedArr = [score]
    for i in range(len(diagramVectorArray)):
        index0 = diagramVectorArray[i][0]
        index0 = round(float(index0), 3)
        reformattedArr.append(index0)
        index1 = diagramVectorArray[i][1]
        index1 = round(float(index1), 3)
        reformattedArr.append(index1)

    return reformattedArr


def addTarget(userID, score, diagramVectorArray, notes):
    """takes given args and adds to db in the target table"""
    try:

        conn, cur = connect()

        # reformat the array to make it 1D and adds the score to the start
        reformattedArr = vectorArrayReformat(score, diagramVectorArray)
        reformattedArrAndNotes = reformattedArr[:]
        reformattedArrAndNotes.append(notes)

        #: add targets to database
        sqlAppend = 'INSERT INTO `target` (`targetID`, `Score`, `dateShot`, `diagramBearing0`, `diagramMagnitude0`, ' \
                    '`diagramBearing1`, `diagramMagnitude1`, `diagramBearing2`, `diagramMagnitude2`, ' \
                    '`diagramBearing3`, `diagramMagnitude3`, `diagramBearing4`, `diagramMagnitude4`, ' \
                    '`diagramBearing5`, `diagramMagnitude5`, `diagramBearing6`, `diagramMagnitude6`, ' \
                    '`diagramBearing7`, `diagramMagnitude7`, `diagramBearing8`, `diagramMagnitude8`, ' \
                    '`diagramBearing9`, `diagramMagnitude9`, `userNotes`) VALUES (NULL, %s, CURRENT_TIMESTAMP, ' \
                    '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

        cur.execute(sqlAppend, reformattedArrAndNotes)  # adds target details to database

        #: recover target ID
        # This will attempt to get the target ID of the target that has just been stored by taking the highest targetID
        # from the table where the score, and all the vectors are equal to those just entered. There could be
        # a problem where the wrong target ID is retrieved if two users enter data at the same time. However, this
        # would require all the vectors to be exactly the same which is probably not going to happen

        sqlRetrive = 'SELECT `targetID` FROM `target` ORDER BY `target`.`targetID` DESC LIMIT 1'

        """
        sqlRetrive = 'SELECT `targetID` FROM `target` WHERE `Score` = %s AND `diagramBearing0` = %s AND ' \
                     '`diagramMagnitude0` = %s AND `diagramBearing1` = %s AND `diagramMagnitude1` = %s AND ' \
                     '`diagramBearing2` = %s AND `diagramMagnitude2` = %s AND `diagramBearing3` = %s AND ' \
                     '`diagramMagnitude3` = %s AND `diagramBearing4` = %s AND `diagramMagnitude4` = %s AND ' \
                     '`diagramBearing5` = %s AND `diagramMagnitude5` = %s AND `diagramBearing6` = %s AND ' \
                     '`diagramMagnitude6` = %s AND `diagramBearing7` = %s AND `diagramMagnitude7` = %s AND ' \
                     '`diagramBearing8` = %s AND `diagramMagnitude8` = %s AND `diagramBearing9` = %s AND ' \
                     '`diagramMagnitude9` = %s AND `userNotes` = %s ORDER BY `target`.`targetID` DESC'
        """

        cur.execute(sqlRetrive)
        targetIDarr = cur.fetchall()
        print("targetIDarr", targetIDarr)

        targetID = str(targetIDarr[0]).strip("(),\'")
        print("targetID:", targetID)

        # Note: due to the way this is retrieved it will most likely be an array of 1 item, the first item will almost
        # always be the relevant one (see comment by ## recover targe ID)

        #: adds data to relational databse
        sqlRelational = 'INSERT INTO `shootsrelational` (`ID`, `userID`, `targetID`) VALUES (NULL, %s, %s)'
        idArr = (userID, targetID)
        cur.execute(sqlRelational, idArr)

        conn.close()


    except Exception as e:
        print(f"error: {e}")

    finally:
        if conn is not None:
            conn.close()


def deleteTarget(targetID):
    """deletes a target from the database with the provided ID"""
    try:
        conn, cur = connect()

        sqlDeleteRelation = 'DELETE FROM `shootsRelational` WHERE `shootsRelational`.`targetID` = %s'
        sqlDeleteFromGroup = 'DELETE FROM `groupsrelational` WHERE `groupsrelational`.`targetID` = %s'
        sqlDeleteTarget = 'DELETE FROM `target` WHERE `target`.`targetID` = %s'

        if targetExists(targetID):
            cur.execute(sqlDeleteRelation, [targetID])
            cur.execute(sqlDeleteFromGroup, [targetID])
            cur.execute(sqlDeleteTarget, [targetID])

    except Exception as e:
        print(f"error: {e}")

    finally:
        if conn is not None:
            conn.close()


def deleteUser(userID):
    """deletes a user from the database with the provided ID"""
    try:
        conn, cur = connect()

        sqlDeleteFromGroup = 'DELETE FROM groups WHERE `groups`.`userID` = %s'
        sqlDeleteTarget = 'DELETE FROM users WHERE `users`.`UserID` = %s'

        cur.execute(sqlDeleteFromGroup, [userID])
        cur.execute(sqlDeleteTarget, [userID])

    except Exception as e:
        print(f"error: {e}")

    finally:
        if conn is not None:
            conn.close()


def targetExists(targetID):
    """returns True if target with given ID is in the database"""
    try:
        conn, cur = connect()

        sqlTargets = 'SELECT * FROM `target` WHERE `target`.`targetID` = %s'

        cur.execute(sqlTargets, [targetID])
        data = cur.fetchall()

        if len(data) != 0:
            return True
        else:
            return False


    except Exception as e:
        print(f"error: {e}")

    finally:
        if conn is not None:
            conn.close()


def emailRegexValid(email):
    """checks if the email is a valid format by comparing to regex thingy, returns True if match"""

    # regex sourced from:
    # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/

    regex = re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")

    if re.fullmatch(regex, email):
        flag = True
    else:
        flag = False
    return flag


def verifyEmail(email):
    """checks email is not in use and checks regex is valid, returns bool, false if in use"""
    try:
        emailValidFlag = True

        if not emailRegexValid(email):
            emailValidFlag = False

        conn, cur = connect()

        # gets table of all emails
        sql = "SELECT `Email` FROM `users`"  # defines column 'email' should be taken from table users
        cur.execute(sql)  # executes the sql
        emailTable = cur.fetchall()  # fetches result


        # checks email is not in use
        for i in range(len(emailTable)):
            emailTableStrip = str(emailTable[i]).strip("(),\'")  # strips unwanted characters
            if emailTableStrip == email:
                emailValidFlag = False
        if emailValidFlag:
            print("email not in use")
        else:
            print("email in use")
        return emailValidFlag

    except Exception as e:
        print(f"error :{e}")

    finally:
        if conn is not None:
            conn.close()


def verifyPasswordHash(userID, providedPassword):
    """This will take a user ID and confirm that the password hash provided matches the stored hash
    Takes: userID, providedPassHash
    Returns: bool(isValid)"""

    isValid = False

    try:
        # retrive users pass hash and compare, returns if match
        conn, cur = connect()

        sqlGetHash = "SELECT passHash FROM users WHERE userID = %s"
        cur.execute(sqlGetHash, [userID])
        storedHash = cur.fetchall()

        cleanedStoredHash = storedHash[0][0]

        # calculated hash from provided password
        salt = str(cleanedStoredHash[:29]).encode('utf-8')
        calculatedHash = bcrypt.hashpw(providedPassword.encode('utf-8'), salt)
        encoded = cleanedStoredHash.encode('utf-8')

        return encoded == calculatedHash


    except Exception as e:
        print(f"error :{e}")

    finally:
        if conn is not None:
            conn.close()




def retriveUserTargets(userID, retriveVectors, lastN):
    """
    retrieve user targets

    this will generate an SQL statement to retrieve targets
    by default it will retrive just score and date,
    if vectors are also wanted it will add this in  the middle of the statement
    """
    try:
        conn, cur = connect()
        sqlRetrive = 'SELECT target.Score, target.dateShot'
        if retriveVectors:
            sqlRetrive += ', target.diagramBearing0, target.diagramMagnitude0, target.diagramBearing1, ' \
                          'target.diagramMagnitude1, target.diagramBearing2, target.diagramMagnitude2, ' \
                          'target.diagramBearing3, target.diagramMagnitude3, target.diagramBearing4, ' \
                          'target.diagramMagnitude4, target.diagramBearing5, target.diagramMagnitude5, ' \
                          'target.diagramBearing6, target.diagramMagnitude6, target.diagramBearing7, ' \
                          'target.diagramMagnitude7, target.diagramBearing8, target.diagramMagnitude8, ' \
                          'target.diagramBearing9, target.diagramMagnitude9'

        sqlRetrive += ' FROM shootsrelational, target WHERE userID = %s AND shootsrelational.targetID =' \
                      ' target.targetID ORDER BY `dateShot` DESC LIMIT %s'

        dataArr = [userID, lastN]
        cur.execute(sqlRetrive, dataArr)
        targetArr = (cur.fetchall())

        return targetArr

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if conn is not None:
            conn.close()

    pass


def retriveNotes(userID):
    """retrieves notes attached to given user ID"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `userNotes` FROM `target` ' \
                      'INNER JOIN `shootsrelational` ON `target`.`targetID` = `shootsrelational`.`targetID` ' \
                      'WHERE `shootsrelational`.`userID` = %s ORDER BY `dateShot` DESC'
        cur.execute(sqlRetrieve, [userID])
        notes = cur.fetchall()

        notesClean = []
        for i in range(len(notes)):
            notesClean.append(str(notes[i]).strip("(),\'"))

        return notesClean

    except Exception as E:
        print(E)

    finally:
        if con is not None:
            con.close()


def createGroup(userID, groupName):
    """creates group in group table"""
    try:
        conn, cur = connect()

        sql = 'INSERT INTO `groups` (`groupID`, `userID`, `groupName`, `userNotes`) VALUES (NULL, %s, %s, NULL)'
        cur.execute(sql, [userID, groupName])

    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def updateTargetGroup(targetID, groupID):
    """change the group that a target is in, if target not in group then add to group"""
    try:
        conn, cur = connect()

        sqlSelect = 'SELECT * FROM `groupsrelational` WHERE `targetID` = %s'
        cur.execute(sqlSelect, [targetID])
        select = cur.fetchall()

        if len(select) == 0 and groupID != 0:
            # target does not exist in relational db and group ID is not 0 (remove from group) , create field

            sqlCreate = 'INSERT INTO `groupsrelational` (`ID`, `groupID`, `targetID`) VALUES (NULL, %s, %s)'
            cur.execute(sqlCreate, [groupID, targetID])

        elif groupID == 0:
            # remove target from relational db
            sqlDelete = 'DELETE FROM groupsrelational WHERE `groupsrelational`.`targetID` = %s'
            cur.execute(sqlDelete, [targetID])

        else:
            # target exists in relational db, update field
            sqlUpdate = 'UPDATE `groupsrelational` SET `groupID` = %s WHERE `groupsrelational`.`targetID` = %s'
            cur.execute(sqlUpdate, [groupID, targetID])

    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def userGroups(userID):
    """fetches all the groups tied to a given user ID"""
    try:
        conn, cur = connect()

        sqlFind = 'SELECT `groupID` FROM `groups` WHERE `userID` = %s'

        cur.execute(sqlFind, [userID])
        groupIDarr = cur.fetchall()
        cleanIDs = [int(str(item).strip(("(),\'[]"))) for item in groupIDarr]

        return cleanIDs


    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def groupSize(groupID):
    """returns number of targets in group"""
    try:
        conn, cur = connect()

        sql = 'SELECT `ID` FROM `groupsrelational` WHERE `groupID` = %s'

        cur.execute(sql, [groupID])
        num = len(cur.fetchall())

        return num


    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def deleteGroup(groupID):
    """deletes a given group and removes all feilds tied to it in the groups relational table"""
    try:
        conn, cur = connect()
        sql = 'DELETE FROM groups WHERE `groups`.`groupID` = %s'
        cur.execute(sql, [groupID])

    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def deleteGroupRelation(targetID):
    """deletes target from group relational DB"""
    try:
        conn, cur = connect()
        sql = 'DELETE FROM groupsrelational WHERE `groupsrelational`.`targetID` = %s'
        cur.execute(sql, [targetID])

    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def findGroupFromTargetID(targetID):
    """finds the group that a target is in and returns group ID"""
    try:
        conn, cur = connect()

        sqlFind = 'SELECT `groups`.`groupID` FROM `groups` ' \
                  'INNER JOIN `groupsrelational` ON `groupsrelational`.`groupID` = `groups`.`groupID` ' \
                  'WHERE `groupsrelational`.`targetID` = %s'

        cur.execute(sqlFind, [targetID])
        groupID = cur.fetchall()
        groupID = [str(item).strip("(),\'") for item in groupID]
        if not groupID:
            groupID = None
        else:
            groupID = int(groupID[0])

        return groupID

    except Exception as E:
        print(E)

    finally:
        if conn is not None:
            conn.close()


def showUserGroups(userID):
    """fetches all the users groups"""
    try:
        con, cur = connect()

        sqlRetrive = 'SELECT `groupName`, `userNotes` FROM `groups` WHERE `groups`.`userID` = %s'
        cur.execute(sqlRetrive, [userID])
        groups = cur.fetchall()

        return groups

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()



def getGroupIDFromName(groupName, userID):
    """gets group"""
    try:
        conn, cur = connect()

        sqlRetrieve = 'SELECT `groupID` FROM `groups` WHERE `groupName` = %s and `groups`.`userID` = %s'
        cur.execute(sqlRetrieve, [groupName, userID])
        groupID = str(cur.fetchall()[0]).strip("(),\'")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if conn is not None:
            conn.close()


def getGroupNameFromID(groupID):
    """gets group name from a given group ID"""
    try:
        conn, cur = connect()

        sqlRetrieve = 'SELECT `groupName` FROM `groups` WHERE `groupID` = %s'
        cur.execute(sqlRetrieve, [groupID])
        groupName = str(cur.fetchall()[0]).strip("(),\'")

        return groupName

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if conn is not None:
            conn.close()


def getNameFromID(userID):
    """gets user first name and surname from user ID"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `Firstname`, `Surname` FROM `users` WHERE `userID` = %s'
        cur.execute(sqlRetrieve, [userID])
        names = cur.fetchall()
        names = names[0]

        fName, sName = str(names[0]).strip("[](),\'"), str(names[1]).strip("[](),\'")
        return fName, sName

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def getEmailFromID(userID):
    """gets email from user ID"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `Email` FROM `users` WHERE `userID` = %s'
        cur.execute(sqlRetrieve, [userID])
        email = cur.fetchall()

        email = str(email).strip("[](),\'")
        return email

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def getIDFromEmail(email):
    """gets user ID from email (email is unique field)"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `userID` FROM `users` WHERE `Email` = %s'
        cur.execute(sqlRetrieve, [email])
        ID = cur.fetchall()

        ID = str(ID).strip("[](),\'")
        return ID

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def isAdmin(userID):
    """returns bool, whether the user is an admin or not"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `Admin` FROM `users` WHERE `UserID` = %s'
        cur.execute(sqlRetrieve, [userID])
        admin = cur.fetchall()

        return admin[0][0] == 1

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def isLeftHanded(userID):
    """returns bool, whether the user is an admin or not"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `LeftHanded` FROM `users` WHERE `UserID` = %s'
        cur.execute(sqlRetrieve, [userID])
        leftHanded = cur.fetchall()
        leftHanded = leftHanded[0][0]

        return leftHanded

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def getPassHash(userID):
    """fetches user pass hash from ID"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT `passHash` FROM `users` WHERE `UserID` = %s'
        cur.execute(sqlRetrieve, [userID])
        passHash = cur.fetchall()

        passHash = str(passHash).strip("[](),\'")

        return passHash

        con.close()
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def retriveTargetsInGroup(groupID):
    """retrieves the target IDs of targets in a given group"""
    try:
        con, cur = connect()

        sqlRetrive = 'SELECT `targetID` FROM `groupsrelational` WHERE `groupID` = %s'

        cur.execute(sqlRetrive, [groupID])
        targets = cur.fetchall()
        IDs = [int(str(item).strip(("(),\'[]"))) for item in targets]

        return IDs

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def retriveTargetIDs(userID):
    """retrieves all the targets tied to a given user"""
    try:
        con, cur = connect()

        sqlRetrive = 'SELECT `target`.`targetID` FROM `target` INNER JOIN `shootsrelational` ON ' \
                     '`target`.`targetID` = `shootsrelational`.`targetID` WHERE `shootsrelational`.`userID` = %s ' \
                     'ORDER BY `dateShot` DESC'

        cur.execute(sqlRetrive, [userID])
        IDs = cur.fetchall()
        con.close()

        IDs = [int(str(item).strip(("(),\'[]"))) for item in IDs]
        return IDs


    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def extractTargetScores(targetArr, lastNShoots):
    """pass in array of targets, will strip and return the scores, if lastN <= 0 then = len(arr)"""
    try:
        scoreList = []
        if lastNShoots > len(targetArr):  # if lastNShoots is an incorrect value it will return all shoots
            lastNShoots = len(targetArr)
        elif lastNShoots <= 0:
            lastNShoots = len(targetArr)

        for i in range(lastNShoots):
            scoreList.append(targetArr[i][0])  # adds 'cleaned' scores to new arr
        return scoreList

    except Exception as e:
        print(f"error: {e}")


def extractTargetDates(targetArr, lastNShoots):
    """pass in array of targets, will strip and return the dates, if lastN <= 0 then = len(arr)"""
    try:
        datesList = []
        if lastNShoots > len(targetArr):  # if lastNShoots is an incorrect value it will return all shoots
            lastNShoots = len(targetArr)
        elif lastNShoots <= 0:
            lastNShoots = len(targetArr)

        for i in range(lastNShoots):
            datesList.append(targetArr[i][1])  # adds 'cleaned' dates to new arr
        return datesList

    except Exception as e:
        print(f"error: {e}")


def bestNofLastN(userID, bestN, lastN):
    """fetches best N of last N scores for a user and calculates an average"""
    try:
        con, cur = connect()

        sqlRetrieve = 'SELECT AVG(`tableScoreOrder`.`score`) FROM ' \
                      '(SELECT `tableDateOrder`.`score` FROM ' \
                      '(SELECT `Score`, `dateShot` FROM `target` ' \
                      'INNER JOIN `shootsrelational` ON `target`.`targetID` = `shootsrelational`.`targetID` ' \
                      'INNER JOIN `users` ON `shootsrelational`.`userID` = `users`.`UserID` ' \
                      'WHERE `users`.`userID` = %s ORDER BY `DateShot` DESC LIMIT %s) ' \
                      'AS tableDateOrder ORDER BY `Score` DESC LIMIT %s) AS tableScoreOrder'

        cur.execute(sqlRetrieve, [userID, lastN, bestN])
        avg = cur.fetchall()

        return avg

        con.close()
    except Exception as e:
        print(f"error: {e}")

    finally:
        if con is not None:
            con.close()


def extractVectorArray(targetArr):
    """vectors passed in as flat 1d arr, reformatted as pairs and returned"""
    try:
        con, cur = connect()
        vectorArr = []
        for i in range(len(targetArr)):  # gets a little cursed here \/
            singleTargetArr = []
            for j in range(0, 10):
                singleVector = (
                    (targetArr[i][(j * 2) + 2]), (targetArr[i][(j * 2) + 3]))  # appends bearing then magnitude
                singleTargetArr.append(singleVector)
            vectorArr.append(singleTargetArr)
        return vectorArr

        con.close()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con is not None:
            con.close()


def highestUserID():
    """finds the highest userID
    returns data as int"""
    try:
        con, cur = connect()

        # find amount of users
        sqlMax = 'SELECT MAX(users.UserID) FROM users'  # finds highest userID
        cur.execute(sqlMax)
        max = cur.fetchall()
        max = int(str(max).strip("[](),\'"))  # strips unnecessary chars and converts to int
        return max

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if con is not None:
            con.close()


def retriveAllUserIDs():
    """returns arr of all user IDs"""
    try:
        con, cur = connect()

        sqlID = 'SELECT users.UserID FROM users'
        cur.execute(sqlID)
        IDs = cur.fetchall()
        for i in range(len(IDs)):
            IDs[i] = str(IDs[i]).strip("(), ")

        return IDs

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if con is not None:
            con.close()


# will retrive avg from best n shoots of last n shoots
def adminSeeTopShooters(adminBool, bestN, lastN):
    """gets avgs of all users and orders users by averages"""
    try:
        con, cur = connect()

        max = highestUserID()

        userAvgs = []
        for user in range(1, max + 1):  # increments through each userID

            sqlRetrieve = 'SELECT AVG(`tableScoreOrder`.`score`) FROM ' \
                          '(SELECT `tableDateOrder`.`score` FROM ' \
                          '(SELECT `Score`, `dateShot` FROM `target` ' \
                          'INNER JOIN `shootsrelational` ON `target`.`targetID` = `shootsrelational`.`targetID` ' \
                          'INNER JOIN `users` ON `shootsrelational`.`userID` = `users`.`UserID` ' \
                          'WHERE `users`.`userID` = %s ORDER BY `DateShot` DESC LIMIT %s) ' \
                          'AS tableDateOrder ORDER BY `Score` DESC LIMIT %s) AS tableScoreOrder'

            # i genuenly spent like 20 minuets trying to wrok out wy this diint return anything, i diddnt cur.fetchall()
            tableVars = [user, bestN, lastN]
            cur.execute(sqlRetrieve, tableVars)  # executes query for defined userID
            avg = cur.fetchall()

            # clean data
            cleanAvg = str(avg).strip("[](),\'Decimal")
            if cleanAvg == "Non":
                cleanAvg = 0
            cleanAvg = float(cleanAvg)

            userAvgs.append((user, cleanAvg))  # appends arr with userID and user avg

        userAvgs.sort(key=lambda x: -x[1])  # sorts data based on score (second item of sub array)

        userAvgsNamed = []
        for i in range(len(userAvgs)):  # iterates through and changes userID to users name
            fName, sName = getNameFromID(userAvgs[i][0])
            userAvgsNamed.append((fName + " " + sName, userAvgs[i][1]))

        return userAvgsNamed

        con.close()

    except Exception as e:
        print(f"error: {e}")

    finally:
        if con is not None:
            con.close()


def diagramMagnitudeInfo(userID, lastN):
    """Retrives the standard deviation and average for each diagram for a user in last n targets
    returns data as 'avgArr, stdDevArr', len: 10"""
    try:
        con, cur = connect()

        sqlAvgs = 'SELECT AVG(`lastN`.`diagramMagnitude0`), AVG(`lastN`.`diagramMagnitude1`), ' \
                  'AVG(`lastN`.`diagramMagnitude2`), AVG(`lastN`.`diagramMagnitude3`), ' \
                  'AVG(`lastN`.`diagramMagnitude4`), AVG(`lastN`.`diagramMagnitude5`), ' \
                  'AVG(`lastN`.`diagramMagnitude6`), AVG(`lastN`.`diagramMagnitude7`), ' \
                  'AVG(`lastN`.`diagramMagnitude8`), AVG(`lastN`.`diagramMagnitude9`) ' \
                  'FROM (SELECT `diagramMagnitude0`, `diagramMagnitude1`, `diagramMagnitude2`, `diagramMagnitude3`, ' \
                  '`diagramMagnitude4`,  `diagramMagnitude5`,  `diagramMagnitude6`, `diagramMagnitude7`, ' \
                  '`diagramMagnitude8`, `diagramMagnitude9` FROM `target` ' \
                  'INNER JOIN `shootsrelational` ON `target`.`targetID` = `shootsrelational`.`targetID` ' \
                  'WHERE `shootsrelational`.`userID` = %s ORDER BY `target`.`dateShot` DESC LIMIT %s) AS lastN'

        sqlStdDev = 'SELECT STDDEV(`lastN`.`diagramMagnitude0`), STDDEV(`lastN`.`diagramMagnitude1`), ' \
                    'STDDEV(`lastN`.`diagramMagnitude2`), STDDEV(`lastN`.`diagramMagnitude3`), ' \
                    'STDDEV(`lastN`.`diagramMagnitude4`), STDDEV(`lastN`.`diagramMagnitude5`), ' \
                    'STDDEV(`lastN`.`diagramMagnitude6`), STDDEV(`lastN`.`diagramMagnitude7`), ' \
                    'STDDEV(`lastN`.`diagramMagnitude8`), STDDEV(`lastN`.`diagramMagnitude9`) ' \
                    'FROM (SELECT `diagramMagnitude0`, `diagramMagnitude1`, `diagramMagnitude2`, `diagramMagnitude3`, ' \
                    '`diagramMagnitude4`,  `diagramMagnitude5`,  `diagramMagnitude6`, `diagramMagnitude7`, ' \
                    '`diagramMagnitude8`, `diagramMagnitude9` FROM `target` ' \
                    'INNER JOIN `shootsrelational` ON `target`.`targetID` = `shootsrelational`.`targetID` ' \
                    'WHERE `shootsrelational`.`userID` = %s ORDER BY `target`.`dateShot` DESC LIMIT %s) AS lastN'

        # fetch and retrive data
        cur.execute(sqlAvgs, [userID, lastN])
        avgs = cur.fetchall()

        cur.execute(sqlStdDev, [userID, lastN])
        stdDevs = cur.fetchall()

        # clean + return data
        return avgs[0], stdDevs[0]

    except Exception as e:
        print(f"error: {e}")

    finally:
        if con is not None:
            con.close()


def numOfTargets(userID):
    """retrieves the number of targets shot by a user"""
    try:
        con, cur = connect()

        sql = 'SELECT targetID FROM `shootsrelational` WHERE UserID = %s'
        cur.execute(sql, [userID])

        targets = cur.fetchall()
        return len(targets)


    except Exception as e:
        print(f"error: {e}")

    finally:
        if con is not None:
            con.close()


# stubs -----------------------------------------------------------------------------------------

def randTargetDetails():
    """random target vectors as polar"""
    diagramVectorArray = []

    for i in range(10):
        diagramVectorArray.append(
            (random.randint(0, 360), random.randint(0, 100)))  # generates random angle and magnitude

    return diagramVectorArray

# stubs end -------------------------------------------------------------------------------------


"""                                       MAIN                                       """

if __name__ == "__main__":
    print("Running db as main")





# regex for email validation
# ([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|"([]!#-[^-~ \t]|(\\[\t -~]))+")@([0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?(\.[0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?)*|\[((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|IPv6:((((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){6}|::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){5}|[0-9A-Fa-f]{0,4}::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){4}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):)?(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){3}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,2}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){2}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,3}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,4}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,5}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,6}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)|(?!IPv6:)[0-9A-Za-z-]*[0-9A-Za-z]:[!-Z^-~]+)])

import db
import bcrypt

import mathFunctions


# This file wraps the database in a class to make it easier to use.
# This file does not talk to the database, instead it acts as an interface to the db file to abstract its function.

class DBClass:

	def __init__(self):
		"""noting passed into the __init__ , all data is passed in when methods are called.
        This means only one instance of the class is needed to function for all users"""

		pass

	def fetchUserID(self, email):
		"""fetches user ID from email and returns user ID"""
		return db.getIDFromEmail(email)

	def fetchUserSaltAndHash(self, userID):
		"""fetches user salt and hash using ID argument, returns salt, hash"""

		Phash = db.getPassHash(userID)  # get salt and hash and sets them to instance variables
		Psalt = Phash[0:29]
		return Psalt, Phash

	def userDetailsValid(self, email, password, userID):
		"""If email in use, regex is valid, and calculated hash = stored hash, return True"""
		valid = False
		# if the email is in use and the password matches the hash stored at the user ID...
		if (not db.verifyEmail(email)) and db.emailRegexValid(email) and db.verifyPasswordHash(userID, password):
			# make flag true
			valid = True

		return valid


	def diagramMagnitudeInfo(self, userID, LastN):
		"""returns diagram magnitude info"""
		return db.diagramMagnitudeInfo(userID, LastN)


	def signUp(self, email, password, fName, sName, lHandBool):
		"""Adds user with provided details, bool admin is hardcoded false
		returns true if successful"""

		if db.emailRegexValid(email) and db.verifyEmail(email):
			print("Valid email")
			# encodes password, generates a salt, then hashes the password with the salt
			encoded = password.encode('utf-8')
			Psalt = bcrypt.gensalt()
			Phash = bcrypt.hashpw(encoded, Psalt)

			db.addUser(False, fName, sName, email, lHandBool, Phash)
			return True
		else:
			print("invalid email")
			return False

	def getName(self, userID):
		"""returns fName, sName of user based on userID"""
		return db.getNameFromID(userID)

	def isAdmin(self, userID):
		"""returns bool as to whether user is an admin or not"""
		return db.isAdmin(userID)

	def isLeftHanded(self, userID):
		"""returns y/n if users is left handed"""
		leftHanded = db.isLeftHanded(userID)
		if leftHanded == 0:
			out = "N"
		else:
			out = "Y"
		return out

	def makeUserAdmin(self):
		"""WIP"""
		# allow an admin to make another user an admin
		pass

	def fetchStats(self, userID, lastN):
		"""Fetches all user stats, returns: avg, avg10of12, avg5of6, targetScores, targetDates, targetVectors"""
		if lastN < 1:
			lastN = db.numOfTargets(userID)
		targetIDs = db.retriveTargetIDs(userID)
		allTargetData = db.retriveUserTargets(userID, True, lastN)
		targetVectors = db.extractVectorArray(allTargetData)
		targetScores = db.extractTargetScores(allTargetData, 0)
		targetDates = db.extractTargetDates(allTargetData, 0)
		avg = mathFunctions.meanAverage(targetScores)
		avg10of12 = db.bestNofLastN(userID, 10, 12)
		avg5of6 = db.bestNofLastN(userID, 5, 10)
		notes = db.retriveNotes(userID)


		return targetIDs, avg, avg5of6, avg10of12, targetScores, targetDates, targetVectors, notes

	def deleteTarget(self, targetID):
		"""deletes target, duh..."""
		db.deleteTarget(targetID)

	def submitTarget(self, userID, score, polarVectArr, notes):
		db.addTarget(userID, score, polarVectArr, notes)

	def groupFromTargetID(self, targetID):
		return db.findGroupFromTargetID(targetID)

	def groupName(self, groupID):
		return db.getGroupNameFromID(groupID)

	def createGroup(self, userID, groupName):
		if groupName:
			db.createGroup(userID, groupName)

	def updateGroup(self, targetID, groupID):
		db.updateTargetGroup(targetID, groupID)

	def userGroups(self, userID):
		"""returns all user groups"""
		groupIDs = db.userGroups(userID)
		groupsArr = []

		for ID in groupIDs:
			groupsArr.append((ID, self.groupName(ID)))
		return groupsArr

	def userGroupData(self, userID):
		"""input userID
		returns IDs, groupNames, groupSizes, numOfTargets"""
		IDs = db.userGroups(userID)
		groupNames = [db.getGroupNameFromID(ID) for ID in IDs]
		groupSizes = [db.groupSize(ID) for ID in IDs]
		numOfTargets = len(IDs)

		return IDs, groupNames, groupSizes, numOfTargets

	def deleteGroup(self, groupID):
		"""deletes all targets tied to group from group relational db then deletes group"""
		targetsInGroup = db.retriveTargetsInGroup(groupID)
		for ID in targetsInGroup:
			db.deleteGroupRelation(ID)
		db.deleteGroup(groupID)

	def deleteUser(self, isAdmin, userID):
		"""deletes all of a users targets and then deletes the targets"""
		if isAdmin:
			# had to get target IDs but diddnt want to write a whole new function.
			targetIDs, avg, avg10of12, avg5of6, targetScores, targetDates, targetVectorsPol, notes = self.fetchStats(
				userID, -1)

			for ID in targetIDs:
				self.deleteTarget(ID)
			db.deleteUser(userID)

	def fetchAllUsersADMIN(self, Admin):
		"""returns all user ID's in user"""
		return db.retriveAllUserIDs()

	def testMethod(self):
		print("Test method called")


if __name__ == "__main__":
	print("running dbWrap as main")
	DB = DBClass()

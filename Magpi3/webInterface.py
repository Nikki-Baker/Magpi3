from flask import Flask, render_template, redirect, request, session, jsonify
import os
import json
import time
import re

# my files
import dbWrap
import mathFunctions
import analysis
import compVision

app = Flask(__name__)
dataBase = dbWrap.DBClass()

# stuff for sessions n that
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Session(app)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'  # for the love of god change this to something random TODO

# render landing page with base url
@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template("magpi3LandingPage.html")


# handles user login, sets up session data and renders relevant homepage
@app.route('/handle_data', methods=['POST'])
def handle_data(*args):

    # if no arguments passed fetch data from form, otherwise use data passed in
    if len(args) != 2:
        # retrives email and password from the form in HTML homepage,

        email = request.form['projectFilepath1']
        password = request.form['projectFilepath2']

    else:
        email = args[0]
        password = args[1]


    # assign all relevant data to the session
    session["email"] = email
    session["password"] = password
    session["ID"] = dataBase.fetchUserID(session["email"])
    if session["ID"]:
        session["fName"], session["sName"] = dataBase.getName(session["ID"])
        session["admin"] = dataBase.isAdmin(session["ID"])
        session["salt"], session["hash"] = dataBase.fetchUserSaltAndHash(session["ID"])

    session["valid"] = dataBase.userDetailsValid(session["email"], session["password"], session["ID"])
    print(f"session['valid'] is:{session['valid']}")
    session["password"] = "DATA PURGED"

    # if the user details are valid, redirect to the homepage
    if session["valid"]:
        print("session data: ", session)

        return redirect("/homepage")

    else:
        session.clear()
        print("session data: ", session)
        return redirect("/")

# handles creation of a new user
@app.route("/handle_signup", methods=['POST'])
def handle_signup():
    fName = request.form['fName']
    sName = request.form['sName']
    lHanded = request.form['LHanded']
    email = request.form['email']
    password1 = request.form['password1']
    password2 = request.form['password2']

    if password1 != password2:
        print("Passwords do not match")
        return redirect("/")

    if lHanded.lower()[0] == "y":
        lHanded = True
    else:
        lHanded = False

    # adds user to DB and success = True if successful
    success = dataBase.signUp(email, password1, fName, sName, lHanded)

    if success:
        print("sign up successful")
        return handle_data(email, password1)
    else:
        print("sign up unsuccessful")
        return redirect("/")


@app.route("/handle_group_change", methods=['POST'])
def handle_group_change():

    item_selection = request.form.get('item_selection', '')
    groupName, targetID = item_selection.split(':')
    groupID = groupName.strip("()")

    # splits the inputted string on the comma, and takes the zeroth index (ID) as an int
    groupID = int(groupID.split(",")[0])


    print("ready to group change", groupName, targetID, groupID)
    dataBase.updateGroup(targetID, groupID)


    return redirect('/stats')



@app.route("/create_group", methods=['POST'])
def create_group():
    if not session["valid"]:
        return redirect('/')

    groupName = request.form['groupName']
    userID = session['ID']

    dataBase.createGroup(userID, groupName)

    return redirect('/stats')


@app.route("/handle_image", methods=['POST'])
def handle_image():
    if session["valid"]:

        # fetches image file
        imgFile = None
        if 'file' in request.files:
            imgFile = request.files['file']

        # saves image with name as the time timestamp for when it was added
        timestamp = time.time()
        print("timestamp", timestamp)
        imgFile.save(f"static/{timestamp}.jpg")

        # TODO work out how to not use absolute path or change when running on server

        # finds all files in static folder
        folderPath = "C://Users//georg//PycharmProjects//Magpi3//static"
        fileList = os.listdir(folderPath)

        # removes any files more than an hour old, so static wont fill with old files
        for file in fileList:
            if file != "targets":
                # gets file timestamp
                fileTS = float(file[:-4])
                if timestamp - 3600 > fileTS:
                    # deletes all files that are more than 3600 seconds (1hour) old
                    os.remove(folderPath + "//" + file)
                    print("deleted", fileTS, f", file was {timestamp - fileTS} s old")

        # process image and save processed image
        processedTimestamp = None
        dataStr = None
        try:
            vect, processedTimestamp = compVision.getAllVectors(f"static/{timestamp}.jpg", True)

            # for some reason the webpage does not like spaces in the array (maybe something to do with jinja?)
            # so i turned the array into a string and replaced every space with an "/",
            # idk why it does this, this is a stupidly hacky solution, but it works so whatever
            dataStr = ""
            for item in vect:
                dataStr += str(item[0]) + "/"
                dataStr += str(item[1]) + "/"
        except Exception as e:
            print("Error:", e)

        finally:
            if timestamp is None:
                timestamp = 0
            if processedTimestamp is None:
                processedTimestamp
            if dataStr is None:
                dataStr

        return render_template("magpi3ConfirmSubmitPage.html", imgTimestamp=timestamp,
                               processedTimestamp=processedTimestamp, polVects=dataStr)


@app.route("/homepage")
def homepage():
    # put data into dict and render either admin page or standard

    if not session["valid"]:
        return redirect("/")

    dataDict = {"fName": session["fName"], "sName": session["sName"], "admin": session["admin"]}

    if session["admin"]:
        return render_template("magpi3HomePageADMIN.html", data=dataDict)
    else:
        return render_template("magpi3HomePage.html", data=dataDict)


@app.route("/logout")
def logout():
    # clears session
    print(session)
    session.clear()
    print("Session cleared: ", session)
    # redirect to landing page
    return redirect("/")


@app.route("/handle_processing", methods=['POST'])
def handle_processing():
    if not session["valid"]:
        return redirect("/")

    score = request.form['score']
    score = int(score)
    if not score or score > 100 or score < 0:
        score = 0

    notes = request.form['userNotes']
    if not notes:
        notes = ""

    vectsStr = request.form['vects']


    # reset format of vect arr
    data = re.split('/', vectsStr)  # splits by '/'
    data = data[:-1]


    vectArr = []
    for i in range(int(len(data)/2)):  # reformats into 2d arr
        vectArr.append([data[i*2], data[(i*2)+1]])


    # add target to db
    dataBase.submitTarget(session["ID"], score, vectArr, notes)

    return render_template("magpi3ImgProcessing.html")


@app.route("/handle_delete", methods=['POST'])
# handles deletion of target
def handle_delete():
    if not session["valid"]:
        return redirect("/")

    data = request.get_json()
    targetID = data.get('targetId')

    dataBase.deleteTarget(targetID)

    return jsonify({'message': 'Target deleted successfully.'})


@app.route("/handle_user_delete", methods=['POST'])
# handles deletion of user
def handle_user_delete():
    if (not session["valid"]) or (not session["admin"]):
        return redirect("/")

    data = request.get_json()
    userID = data.get('userId')

    dataBase.deleteUser(session["admin"], userID)

    return jsonify({'message': 'Target deleted successfully.'})


@app.route("/handle_group_delete", methods=['POST'])
def handle_group_delete():
    if not session["valid"]:
        return redirect("/")

    data = request.get_json()
    groupID = int(data.get('groupId'))


    dataBase.deleteGroup(groupID)

    return jsonify({'message': 'Group deleted successfully.'})



@app.route("/stats")
def stats(*args):
    """args is ID for user (if accessed from admin acount)"""
    if not session["valid"]:
        return redirect("/")

    if len(args) != 0:  # if an ID has been passed in user that instead of the session ID
        sessionID = args[0]
        fName, sName = dataBase.getName(sessionID)
        accessedAsAdmin = True
    else:
        sessionID = session["ID"]
        fName = session["fName"]
        sName = session["sName"]
        accessedAsAdmin = False

    # fetch data through db wrap, return with HTML template

    lastN = -1
    targetIDs, avg, avg10of12, avg5of6, targetScores, targetDates, targetVectorsPol, notes = dataBase.fetchStats(sessionID, lastN)
    # convert vectors to cartesian for easy display
    targetVectorsCart = mathFunctions.vectArrPolarToCartesian(targetVectorsPol)

    avgVectors = []
    stdDev = []
    commentsArr = []
    for i in range(len(targetVectorsCart)):
        xAvg, yAvg = mathFunctions.cartesianVectorArrAverage(targetVectorsCart[i])
        avgVectors.append([xAvg, yAvg])

        xStd, yStd = mathFunctions.arrVectStdDev(targetVectorsCart[i])
        stdDev.append([xStd, yStd])

        # adds comments to arr
        comment = analysis.targetsOutlierStd(targetVectorsCart[i])
        comment += ", " + analysis.groupShape(targetVectorsCart[i])

        comment = comment.strip(" ,")
        if not comment:
            comment = "None"
        commentsArr.append(comment)

    targetsInGroup = []
    for ID in targetIDs:
        groupID = dataBase.groupFromTargetID(ID)
        if not groupID:
            groupIDTup = (0, "None")
        else:
            groupIDTup = (groupID, dataBase.groupName(groupID))
        targetsInGroup.append(groupIDTup)

    groups = [(0, "None")] + dataBase.userGroups(sessionID)

    if not avg:
        avg = 0
    if not avg10of12[0][0]:
        avg10of12 = [[0]]
    if not avg5of6[0][0]:
        avg5of6 = [[0]]

    # store data in a dict to be passed in to template
    dataDict = {"avg": round(avg, 2), "avg10of12": round(avg10of12[0][0], 3), "avg5of6": round(avg5of6[0][0], 3),
                "scores": targetScores, "dates": targetDates, "vectorsPol": targetVectorsPol,
                "vectorsCart": targetVectorsCart, "noOfTargets": len(targetVectorsCart),
                "avgVectors": avgVectors, "stdDevs": stdDev, "comments": commentsArr, "userNotes": notes,
                "targetIDs": targetIDs, "targetsInGroup": targetsInGroup, "groups": groups, "fName": fName,
                "sName": sName, "asAdmin": accessedAsAdmin, "ID": sessionID}


    return render_template("magpi3StatsPage.html", data=dataDict)




@app.route("/group_stats", methods=['POST'])
def group_stats():
    if not session["valid"]:
        return redirect("/")

    group_selection = request.form.get('group_selection')
    asAdmin = request.form['asAdmin']
    if asAdmin is None or asAdmin == "False":
        asAdmin = False
    else:
        asAdmin = True

    # if an admin get user details from given ID
    if asAdmin:
        accessedAsAdmin = True
        sessionID = request.form['ID']
    else:
        accessedAsAdmin = False
        sessionID = session['ID']
    fName, sName = dataBase.getName(sessionID)


    if group_selection is not None:
        group_selection = group_selection.strip("()")
        selectedGroupID = int(group_selection.split(",")[0])
        selectedGroupName = dataBase.groupName(selectedGroupID)
    else:
        selectedGroupID = 0
        selectedGroupName = "None"

    # fetch data through db wrap, return with HTML template

    lastN = -1
    targetIDs, avg, avg10of12, avg5of6, targetScores, targetDates, targetVectorsPol, notes = dataBase.fetchStats(sessionID, lastN)
    # convert vectors to cartesian for easy display
    targetVectorsCart = mathFunctions.vectArrPolarToCartesian(targetVectorsPol)

    avgVectors = []
    stdDev = []
    commentsArr = []
    for i in range(len(targetVectorsCart)):
        xAvg, yAvg = mathFunctions.cartesianVectorArrAverage(targetVectorsCart[i])
        avgVectors.append([xAvg, yAvg])

        xStd, yStd = mathFunctions.arrVectStdDev(targetVectorsCart[i])
        stdDev.append([xStd, yStd])

        # adds comments to arr
        comment = analysis.targetsOutlierStd(targetVectorsCart[i])
        comment += ", " + analysis.groupShape(targetVectorsCart[i])

        comment = comment.strip(" ,")
        if not comment:
            comment = "None"
        commentsArr.append(comment)

    targetsInGroup = []
    for ID in targetIDs:
        groupID = dataBase.groupFromTargetID(ID)
        if not groupID:
            groupIDTup = (0, "None")
        else:
            groupIDTup = (groupID, dataBase.groupName(groupID))
        targetsInGroup.append(groupIDTup)

    # array of just the ID (not the group name) for all targets
    targetPureGroupID = [int(item[0]) for item in targetsInGroup]

    groups = [(0, "None")] + dataBase.userGroups(sessionID)

    # store data in a dict to be passed in to template
    dataDict = {"avg": round(avg, 2), "avg10of12": round(avg10of12[0][0], 3), "avg5of6": round(avg5of6[0][0], 3),
                "scores": targetScores, "dates": targetDates, "vectorsPol": targetVectorsPol,
                "vectorsCart": targetVectorsCart, "noOfTargets": len(targetVectorsCart),
                "avgVectors": avgVectors, "stdDevs": stdDev, "comments": commentsArr, "userNotes": notes,
                "targetIDs": targetIDs, "targetsInGroup": targetsInGroup, "groups": groups,
                "targetPureGroupID": targetPureGroupID, "selectedGroupID": selectedGroupID,
                "selectedGroupName": selectedGroupName, "fName": fName, "sName": sName, "asAdmin": accessedAsAdmin,
                "ID": sessionID}

    return render_template("magpi3GroupStatsPage.html", data=dataDict)



@app.route("/breakdown", methods=['POST'])
def breakdown():
    if not session["valid"]:
        redirect("/")

    # try to retrieve 'lastN' if that fails default to -1
    try:
        lastN = int(request.form['lastN'])
        asAdmin = request.form['asAdmin']

        if lastN is None:
            lastN = -1
        if asAdmin is None or asAdmin == "False":
            asAdmin = False
        else:
            asAdmin = True


        # if an admin get user details from given ID
        if asAdmin:
            accessedAsAdmin = True
            sessionID = request.form['ID']
        else:
            accessedAsAdmin = False
            sessionID = session['ID']
        fName, sName = dataBase.getName(sessionID)

    except Exception as E:
        print("Error", E)
        lastN = -1
        accessedAsAdmin = False
        sessionID = 0
        fName = ""
        sName = ""


    targetIDs, avg, avg10of12, avg5of6, targetScores, targetDates, targetVectorsPol, notes = dataBase.fetchStats(sessionID, lastN)
    # convert vectors to cartesian for easy display
    targetVectorsCart = mathFunctions.vectArrPolarToCartesian(targetVectorsPol)

    numOfTargets = len(targetVectorsCart)

    # sort vectors by diagram, e.g. [[shots on diagram 1], [shots on diagram 2], etc...]
    cartVectorsByDiagram = mathFunctions.vectorsByDiagram(targetVectorsCart)

    # get average of vectors and stdDev
    stdDev = []
    avgVectors = []
    for i in range(len(cartVectorsByDiagram)):

        xAvg, yAvg = mathFunctions.cartesianVectorArrAverage(cartVectorsByDiagram[i])
        avgVectors.append([xAvg, yAvg])

        xStd, yStd = mathFunctions.arrVectStdDev(cartVectorsByDiagram[i])
        stdDev.append([xStd, yStd])

    avgMag, stdMag = dataBase.diagramMagnitudeInfo(sessionID, lastN)

    dataDict = {"vectors": cartVectorsByDiagram, "numOfTargets": numOfTargets, "avgVectors": avgVectors,
                "stdDevs": stdDev, "fName": fName, "sName": sName, "asAdmin": accessedAsAdmin, "ID": sessionID,
                "avgMag": avgMag, "stdMag": stdMag}

    print("BD DICT", dataDict)

    return render_template("magpi3BreakdownPage.html", data=dataDict)

@app.route("/settings")
def settings():
    if not session["valid"]:
        return redirect("/")

    IDs, groupNames, groupSizes, numOfTargets = dataBase.userGroupData(session['ID'])

    dataDict = {"IDs": IDs, "groupNames": groupNames, "groupSizes": groupSizes, "numOfTargets": numOfTargets}

    return render_template("magpi3SettingsPage.html", data=dataDict)


@app.route("/submit")
def submit():
    if not session["valid"]:
        return redirect("/")

    # render settings template page
    dataDict = {}

    return render_template("magpi3SubmissionPage.html", data=dataDict)


@app.route("/adminView")
def adminView():
    if (not session["valid"]) or (not session["admin"]):
        return redirect("/")

    # gather data for and render template of all users
    dataDict = {}

    userIDarr = dataBase.fetchAllUsersADMIN(session["admin"])
    for ID in userIDarr:
        fName, sName = dataBase.getName(ID)
        isAdmin = dataBase.isAdmin(ID)
        targetIDs, avg, avg5of6, avg10of12, targetScores, targetDates, targetVectors, notes = dataBase.fetchStats(ID, -1)
        isLeftHanded = dataBase.isLeftHanded(ID)

        if avg is None:
            avg = 0
        if avg5of6[0][0] is None:
            avg5of6 = [[0]]
        if avg10of12[0][0] is None:
            avg10of12 = [[0]]

        dataDict[int(ID)] = [fName, sName, round(avg, 3), round(avg5of6[0][0], 3), round(avg10of12[0][0], 3), isLeftHanded]


    return render_template("magpi3AdminOverview.html", data=dataDict)



@app.route("/statsADMIN", methods=['POST'])
def statsADMIN():
    if (not session["valid"]) or (not session["admin"]):
        return redirect("/")

    ID = request.form.get('ID')

    return stats(ID)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

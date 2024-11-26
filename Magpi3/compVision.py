
import cv2 as cv
import numpy as np
import os
import time

import mathFunctions


def locateDiagrams(file):
    # Loads an image
    src = cv.imread(file)
    # Check if image is loaded fine
    if src is None:
        raise Exception("No image file supplied to diagrams()")

    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 35)

    rows = gray.shape[0]
    # min and max radius calibrated to diagram outline
    circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, rows / 8,
                              param1=100, param2=30,
                              minRadius=250, maxRadius=400)

    circlesArr = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            # circle center
            cv.circle(src, center, 1, (0, 100, 100), 3)
            # circle outline
            radius = i[2]
            cv.circle(src, center, radius, (255, 0, 255), 3)

            circleData = [center, radius]
            circlesArr.append(circleData)

    # cv.imwrite(f'./static/targets/DiagramsDetected-{time.time()}.jpg', src) ############################################

    return circlesArr


def orderDiagrams(circleData):
    """orders centers based on diagram position, returns sorted arr
    pass in all circle data!"""

    # strips coOrds from data
    coOrdArr = []
    for i in range(len(circleData)):
        coOrdArr.append((circleData[i][0][0], circleData[i][0][1]))

    # sorts all co ords by y component, top to bottom
    coOrdArr = sorted(coOrdArr, key=lambda x: x[1], reverse=False)

    topRow = orderCentersByX(coOrdArr[0:4], False)
    middleRow = orderCentersByX(coOrdArr[4:6], True)
    bottomRow = orderCentersByX(coOrdArr[6:10], True)

    diagramsInOrder = []

    for item in topRow:
        diagramsInOrder.append(item)

    diagramsInOrder.append(middleRow[0])

    for item in bottomRow:
        diagramsInOrder.append(item)

    diagramsInOrder.append(middleRow[1])


    # loops through diagram locations in order and finds corresponding circle data item, adds the circle data to a
    # new arr in order of diagrams, does go through targets that have already been added which is a waste of
    # computational power, but it is not a computationally expensive operations so probably not a problem
    circleDataSorted = []
    for diagram in diagramsInOrder:
        for item in circleData:
            if diagram == item[0]:
                circleDataSorted.append(item)

    return circleDataSorted


def orderCentersByX(centers, reverse):
    return sorted(centers, key=lambda x: x[0], reverse=reverse)


def extractDiagramInfo(file, center, radius):
    """extracts diagram mask, locates shot, and gets center of shot"""

    img = cv.imread(file)
    # cv.imshow('Original', img)

    blank = np.zeros(img.shape[:2], dtype='uint8')

    center_coordinates = (center[0], center[1])

    mask = cv.circle(blank, center_coordinates, radius, 255, -1)

    masked = cv.bitwise_and(img, img, mask=mask)

    # cv.imshow('Output', masked)

    return locateShot(masked)



def locateShot(diagramMask):

    # blur target to reduce noise
    blur = cv.medianBlur(diagramMask, 19) # 19
    contrasted = cv.convertScaleAbs(blur, alpha=1.1, beta=0)  # 1.1
    # cv.imwrite(f'./static/targets/TEST-{time.time()}.jpg', blur) ############################################


    # Canny Edge Detection
    edges = cv.Canny(image=contrasted, threshold1=20, threshold2=20)  # 20 20

    recontrasted = cv.convertScaleAbs(edges, alpha=2, beta=0) # 2

    # blur edges slightly to decrease noise
    reblured = cv.stackBlur(recontrasted, (3,3))  # 9 9   3 3
    # cv.imwrite(f'./static/targets/TESTBLUR-{time.time()}.jpg', reblured) #################################


    # hough circle detection, detects shot holes
    rows = reblured.shape[0]
    circles = cv.HoughCircles(reblured, cv.HOUGH_GRADIENT, 1, rows / 8,
                              param1=100, param2=30,
                              minRadius=12, maxRadius=35) # 8, 40 prev

    circlesArr = []
    if circles is not None:

        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            # circle center
            cv.circle(diagramMask, center, 1, (0, 100, 100), 3)
            # circle outline
            radius = i[2]
            cv.circle(diagramMask, center, radius, (255, 0, 255), 3)

            circleData = [center, radius]
            circlesArr.append(circleData)


    else:
        center = (None, None)

    # cv.imwrite(f'./static/targets/TESTHOUGH-{time.time()}.jpg', diagramMask)

    return center


def increaseImgBrightness(img, value):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    h, s, v = cv.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    final_hsv = cv.merge((h, s, v))
    img = cv.cvtColor(final_hsv, cv.COLOR_HSV2BGR)
    return img



def resolveVector(diagramCenter, shotCenter):

    xVect = float(shotCenter[0]) - float(diagramCenter[0])
    yVect = float(shotCenter[1]) - float(diagramCenter[1])
    return (xVect, yVect)


def scaleVectors(polVector, diagramRadius):
    """Scale vector so that on the edge of the diagram is 100 and middle is 0"""

    scaledMagnitude = (polVector[1]/diagramRadius)*100

    if scaledMagnitude > 100:
        scaledMagnitude = 100

    return scaledMagnitude


def getAllVectors(file, createFile):
    """pass in location of a file, return arr of polar vectors of each shot and timestamp of drawn file in static
    """
    print("start fetch vectors")
    circleData = locateDiagrams(file)  # gets center and radius of each diagram
    circleData = orderDiagrams(circleData)  # orders them by diagram location

    shotVectors = []
    shotLocations = []
    for i, diagram in enumerate(circleData):
        print(f"diagram {i+1}")
        shotCenter = extractDiagramInfo(file, diagram[0], diagram[1])

        if shotCenter == (None, None): # if the shot is null then make the shot co-ords the center of the diagram
            shotCenter = diagram[0]

        shotLocations.append([shotCenter, 15])
        # adds shot location to array with fixed radius to array to be drawn onto image

        shotVectors.append(resolveVector(diagram[0], shotCenter))
        # print(shotVectors[i])


    circles = circleData + shotLocations # adds the diagram circle data and shot circle data to one array

    timestamp = 0


    if createFile:
        fileOut = cv.imread(file)
        if circles is not None:

            # draw circles on image and save with name and timestamp
            for i in circles:
                center = (i[0])
                # circle center
                cv.circle(fileOut, center, 1, (0, 100, 100), 3)
                # circle outline
                radius = i[1]
                cv.circle(fileOut, center, radius, (255, 0, 255), 3)

            timestamp = time.time()

            cv.imwrite(f'./static/{timestamp}.jpg', fileOut)
            print("file created")

    polShotVectors = mathFunctions.vectArrCartesianToPolar([shotVectors])[0]
    # data put in as 3d arr, just want 1 target tho so take first index [0]

    polShotVectorsScaled = []
    for i, vect in enumerate(polShotVectors):
        scaledMagnitude = scaleVectors(vect, circleData[i][1])
        polShotVectorsScaled.append((vect[0], scaledMagnitude))


    print("returning vectors")
    for v in polShotVectorsScaled:
        print(v)
    return polShotVectorsScaled, timestamp



if __name__ == "__main__":
    print("running compVision.py as __main__")

    folderPath = r'C:\Users\georg\PycharmProjects\Magpi3\static\targets'
    fileList = os.listdir(folderPath)




    """
    imgFiles = []
    for file in fileList:
        if file != "New folder" and file != "00000000_173227685_iOS.jpg":
            print(file)
            fileName = r'./static/targets/'+file
            imgFiles.append(fileName)

    print(imgFiles)
    startTime = time.time()
    for i, img in enumerate(imgFiles[:15]):
        print(f"------------------------------ TARGET {i+1} ------------------------------")
        getAllVectors(img)


    print("\n\nall done :)")
    print(f"time to run : {time.time()-startTime}")
    """

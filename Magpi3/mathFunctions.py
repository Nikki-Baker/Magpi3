import math
import random
import time

import numpy as np

from db import *

# this is custom maths functions n that
print("mathFunctions is running")


def arrRange(arr):
    """Pass in array, and it will return the range of the data"""
    try:
        if arr:
            arr.sort()
            listRange = arr[-1] - arr[0]
            return listRange
        else:
            return 0

    except Exception as e:
        print(f"error: {e}")


def meanAverage(arr):
    """works out the mean average of an array of data"""
    try:
        return sum(arr) / len(arr)
    except Exception as e:
        print(f"error: {e}")


def sumOfSquared(arr):
    """calculates the sum of the squared of the data (used in std dev)"""
    try:
        out = 0
        for i in range(len(arr)):
            out += arr[i] ** 2
        return out
    except Exception as e:
        print(f"error: {e}")


def standardDev(arr):
    """calculates the std dev of an array of data"""
    try:
        return math.sqrt((sumOfSquared(arr) / len(arr)) - (sum(arr) / len(arr)) ** 2)
    except Exception as e:
        print(f"error: {e}")


def numInStdDev(num, stdDev, mean):
    """See if num within standard deviation of a set of data
    Returns bool, True/False"""
    try:
        if num >= mean + stdDev or num <= mean - stdDev:
            within = False
        else:
            within = True
        return within

    except Exception as e:
        print(f"Error: {e}")


def polarToCartesian(angle, magnitude):
    """converts polar co-ords to cartesian co-ords
    returns data as 'x, y'"""
    try:
        # need to convert angle to rads
        radAngle = angle * (math.pi / 180)
        x = magnitude * math.cos(radAngle)
        y = magnitude * math.sin(radAngle)
        return x, y
    except Exception as e:
        print(f"error: {e}")


def cartesianToPolar(x, y):
    """converts cartesian co-ords to polar co-ords
    returns data as 'angle, magnitude'"""
    try:
        magnitude = math.sqrt(x ** 2 + y ** 2)
        if x != 0:  # if x = 0, div by 0 error, must correct for edge case
            radAngle = math.atan(y / x)  # answer returned in radians, must convert
            angle = (radAngle * 180) / math.pi  # converts rads to deg
        elif y > 0:  # if x=0 and y is +ve angle must be 90
            angle = 90
        elif y < 0:  # if x=0 and y is -ve angle must be 270
            angle = 270
        else:  # if x=0 and y=0 set angle to 0
            angle = 0

        # accounting for quadrants
        if x < 0:
            angle += 180

        # makes 0 =< angle < 360
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle -= 360

        return angle, magnitude

    except Exception as e:
        print(f"error: {e}")


def vectArrPolarToCartesian(vectArr):
    """converts an array of polar co-ords to an array of cartesian
    Data is processed as multiple targets so input data MUST be 3D arr, if only one target input [vectArr]"""
    try:
        cartVectArr = []
        for i in range(len(vectArr)):  # increments through targets
            cartVectArr2 = []  # second indexed vector arr (target)
            for j in range(0, 10):  # increments through shots
                polarAngle, polarMagnitude = vectArr[i][j][0], vectArr[i][j][1]  # sets defined vector to var
                cartX, cartY = polarToCartesian(polarAngle, polarMagnitude)  # converts to cartesian
                cartVectArr2.append([cartX, cartY])  # appends to array
            cartVectArr.append(cartVectArr2)
        return cartVectArr

    except Exception as e:
        print(f"Error {e}")


def vectArrCartesianToPolar(vectArr):
    """converts an array of cartesian co-ords to array of polar must be 3d arr"""
    try:
        polVectArr = []
        for i in range(len(vectArr)):  # increments through targets
            polVectArr2 = []
            for j in range(0, 10):  # increments through shots
                cartX, cartY = vectArr[i][j][0], vectArr[i][j][1]  # sets defined vector to var
                polarAngle, polarMagnitude = cartesianToPolar(cartX, cartY)  # converts to cartesian
                polVectArr2.append([polarAngle, polarMagnitude])  # appends to array
            polVectArr.append(polVectArr2)  # appends arr to arr
        return polVectArr

    except Exception as e:
        print(f"Error {e}")


def vectorsByDiagram(vectors):
    """Pass in 3dArr of targets and rearrange to ten arrays of vectors by diagram"""
    try:

        vectByDiagram = []

        # loop through diagrams
        for d in range(10):
            tempDiagram = []

            # loop through targets
            for t in range(len(vectors)):
                tempDiagram.append(vectors[t][d])
            vectByDiagram.append(tempDiagram)

        return vectByDiagram

    except Exception as e:
        print(f"Error: {e}")


def cartesianVectorArrAverage(vectArr):
    """calculates the average of all vectors in an array of cartesian co-ordinates
    returns data as 'xAvg, yAvg'"""
    try:
        xVectArr = []  # creates separate arrays for x and y vars
        yVectArr = []
        for i in range(len(vectArr)):  # increments through all vectors and appends them to relevant array
            xVectArr.append(vectArr[i][0])
            yVectArr.append(vectArr[i][1])
        xAvg = meanAverage(xVectArr)  # calc average of each arr
        yAvg = meanAverage(yVectArr)
        return xAvg, yAvg  # returns average

    except Exception as e:
        print(f"Error {e}")


def arrVectStdDev(arr):
    """calculates the standard deviation of an array of vectors (2d, input value as cartesian co-ord
    input data as '[(x1,y1),(x2,y2),(x3,y3)]'
    returns data as 'xStd, yStd'"""


    xArr = []
    yArr = []
    for i in range(len(arr)):
        xArr.append(arr[i][0])
        yArr.append(arr[i][1])
    # gets standard deviation of array
    xStd = standardDev(xArr)
    yStd = standardDev(yArr)

    return xStd, yStd




def peel2DArrIndex(arr, index):
    """peels index[:][n] from a 2D array"""
    try:
        peeledArr = []
        for i in range(len(arr)):
            peeledArr.append(arr[i][index])
        return peeledArr
    except Exception as e:
        print(f"Error: {e}")


def shotInStd(xStd, yStd, xAvg, yAvg, vectArr):
    """pass in vector array and stDev and Avg as cartesian and returns whether the vector is within the standard
    deviation, returns array of bools
    True if in Std, False if not in Std"""

    arrShotInStd = []
    for vect in vectArr:

        if xStd == 0 or yStd == 0:
            arrShotInStd.append(False)

        else:
            xShot = vect[0]
            yShot = vect[1]

            value = ((xShot - xAvg) ** 2 / xStd ** 2) + ((yShot - yAvg) ** 2 / yStd ** 2)
            # uses ellipsis equation to see if shot in standard deviation

            # converts to bool
            if value <= 1:
                shotIn = True
            else:
                shotIn = False

            arrShotInStd.append(shotIn)

    return arrShotInStd


def shotIsOutlier(xStd, yStd, xAvg, yAvg, vectArr):
    """pass in vector array and shot co-ords as cartesian and returns whether the vector is within
    the bounds for an outlier,
    returns array of bools
    True if Outlier, False if not Outlier"""

    outlierMultiplier = 1.5  # this may need to be changed to fine tune if a shot is an outlier or not,
    # shot flagged if more than 1.5 standard deviations away from midpoint

    arrShotInStd = []
    for vect in vectArr:

        if xStd == 0 or yStd == 0:
            arrShotInStd.append(False)

        else:
            xShot = vect[0]
            yShot = vect[1]

            value = ((xShot - xAvg) ** 2 / (xStd * outlierMultiplier) ** 2) + (
                    (yShot - yAvg) ** 2 / (yStd * outlierMultiplier) ** 2)
            # uses ellipsis equation to see if shot in standard deviation

            # converts to bool
            if value >= 1:
                shotIn = True
            else:
                shotIn = False

            arrShotInStd.append(shotIn)

    return arrShotInStd



def arrMagnitudeFromMiddle(arr):
    """Will get the magnitude from the midpoint (mean average) for each shot
    data returned as arr e.g. [313, 53, 56, 76]"""

    try:
        xMid, yMid = cartesianVectorArrAverage(arr)
        magnitudeArr = []

        for i in range(len(arr)):
            xVect, yVect = arr[i][0], arr[i][1]
            xDifference, yDifference = xVect - xMid, yVect - yMid  # calculates the difference (distance) between both
            magnitude = math.sqrt(xDifference ** 2 + yDifference ** 2)  # uses pythag to get sqrt
            magnitudeArr.append(magnitude)

        return magnitudeArr
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    print("running mathFunctions as main")



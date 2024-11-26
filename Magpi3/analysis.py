import cv2 as cv
import numpy as np
import math
import sys
import time

import mathFunctions
from db import *
from mathFunctions import *


def targetsOutlierStd(targetCartVectors):
	""" data MUST be passed in as 2d arr (one target)
    compares the standard deviation of shots that are in the std dev and shots that are not,
    if there is a small std of outliers they are all in the same place
    returns: commentString"""

	# puts x vectors and y vectors in separate arrays
	xVects, yVects = peel2DArrIndex(targetCartVectors, 0), peel2DArrIndex(targetCartVectors, 1)

	# get standard deviation and average of x and y vectors
	xStDev, yStDev = mathFunctions.standardDev(xVects), mathFunctions.standardDev(yVects)
	xAvg, yAvg = mathFunctions.meanAverage(xVects), mathFunctions.meanAverage(yVects)

	# finds out which shots are in the standard deviation and which are outliers
	shotsInStd = shotInStd(xStDev, yStDev, xAvg, yAvg, targetCartVectors)
	shotsIsOutlierArr = shotIsOutlier(xStDev, yStDev, xAvg, yAvg, targetCartVectors)

	# adds shots that are outliers to new arr
	xOutlierVect = []
	yOutlierVect = []
	for i in range(len(shotsIsOutlierArr)):
		if shotsIsOutlierArr[i]:
			xOutlierVect.append(targetCartVectors[i][0])
			yOutlierVect.append(targetCartVectors[i][1])

	# calculates the standard deviation of the outliers
	xOutlierStDev, yOutlierStDev = mathFunctions.standardDev(xOutlierVect), mathFunctions.standardDev(yOutlierVect)

	xRange, yRange = mathFunctions.arrRange(xVects), mathFunctions.arrRange(yVects)
	xOutlierRange, xOutlierRange = mathFunctions.arrRange(xOutlierVect), mathFunctions.arrRange(yOutlierVect)

	# Generate comment
	commentString = ""
	if not xOutlierStDev:
		xOutlierStDev = 0
	if not xStDev:
		xStDev = 0
	if not yOutlierStDev:
		yOutlierStDev = 0
	if not yStDev:
		yStDev = 0

	if (xOutlierStDev < xStDev) and (yOutlierStDev < yStDev):
		commentString = "Ouliers in Group"

	elif xOutlierStDev < xStDev:
		commentString = "Outliers in vertical group"

	elif yOutlierStDev < yStDev:
		commentString = "Outliers in horizontal group"

	return commentString


def groupShape(targetCartVectors):
	"""comments on trends in target shape, e.g. large relative vertical spread
	input: targetCartVectors(one target, 2D array)
	output: comment(string)"""

	xVects, yVects = peel2DArrIndex(targetCartVectors, 0), peel2DArrIndex(targetCartVectors, 1)
	xStDev, yStDev = mathFunctions.standardDev(xVects), mathFunctions.standardDev(yVects)

	comment = ""
	if yStDev > 2*xStDev:
		comment = "Large relative vertical spread"
	elif yStDev > 1.5*xStDev:
		comment = "Relative Vertical spread"
	elif yStDev > 1.25*xStDev:
		comment = "Mild relative vertical spread"
	elif xStDev > 2*yStDev:
		comment = "Large relative horizontal spread"
	elif xStDev > 1.5*yStDev:
		comment = "Relative horizontal spread"
	elif xStDev > 1.25*yStDev:
		comment = "Mild relative horizontal spread"

	return comment


if __name__ == "__main__":
	print("analysis running as __main__")



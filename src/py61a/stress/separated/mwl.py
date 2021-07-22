import numpy as np
from matplotlib import pyplot as plt
from py61a.cryst_utils.hkl import bragg


def createWeightedData(x, y, a):
	# check dimensions of values
	# if x.shape[0] != y.shape[0] or x.shape[1] != y.shape[1]:
	# 	if x.shape[0] == a.shape[0] and x.shape[1] == a.shape[1]:
	# 		# try to transpose data
	# 		if x.shape[0] == np.transpose(y).shape[0] and x.shape[1] == np.transpose(y).shape[1]:
	# 			y = np.transpose(y)
	# 	elif y.shape[0] == a.shape[0] and y.shape[1] == a.shape[1]:
	# 		# try to transpose data
	# 		if x.shape[0] == np.transpose(y).shape[0] and x.shape[1] == np.transpose(y).shape[1]:
	# 			y = np.transpose(y)
	# 			a = np.transpose(a)
	# check validity of weigths
	a[a < 0] = 1
	# create new data set according to weights
	minA = np.min(a)
	weights = np.ceil(a / minA)
	n = int(np.sum(weights))
	xNew = np.ones(n)
	yNew = np.ones(n)
	pos = 0
	for i in range(len(weights)):
		xNew[pos:pos + int(weights[i])] = x[i]
		yNew[pos:pos + int(weights[i])] = y[i]
		pos = pos + int(weights[i])
	return xNew, yNew

# Determine linear regression of given values
# parameters:
# values of both signals
# returns:
# increasing, constant offset, coefficient of determination, determined values
def linReg(x, y, fixParName='', fixPar=0):  # scipy.stats.linregress(x, y=None)
	n = len(x)
	x = np.array(x)
	y = np.array(y)
	# check dimensions of values
	# if x.shape[0] != y.shape[0] or x.shape[1] != y.shape[1]:
	# 	# try to transpose data
	# 	if x.shape[0] == np.transpose(y).shape[0] and x.shape[1] == np.transpose(y).shape[1]:
	# 		y = np.transpose(y)
	sumX = sum(x)
	sumY = sum(y)
	meanX = sumX/n
	meanY = sumY/n
	sumXY = sum(x * y)
	sumXX = sum(x ** 2)
	if fixParName == "b":
		b = fixPar
		m = (sumXY - b * sumX) / sumXX
	elif fixParName == "m":
		m = fixPar
		b = meanY - m * meanX
	else:
		m = (n * sumXY - sumX * sumY) / (n * sumXX - sumX**2)
		b = meanY - m * meanX
		#b = (sumXX * sumY - sumX * sumXY) / (n * sumXX - sumX**2)
		#m = (sumXY - b * sumX) / sumXX
	yD = m * x + b
	CoD = 1 - sum((y - yD) ** 2) / sum((y - meanY) ** 2)  # RuntimeWarning: invalid value encountered in double_scalars
	err = sum((y - yD) ** 2) / (n * (n - 1)) # variance
	mErr = err / sum((x - meanX)**2)
	bErr = err / n * sum(x**2) / sum((x - meanX)**2)
	return m, b, CoD, yD, err, mErr, bErr


# Determine linear regression of given values with accuracy
# parameters:
# values of both signals and accuracy of values
# returns:
# increasing, constant offset, coefficient of determination, determined values
def linRegWeighted(x, y, a, fixParName='', fixPar=0):
	xNew, yNew = createWeightedData(x, y, a)
	# linear regression with new data set
	m, b, CoD, yD, err, mErr, bErr = linReg(xNew, yNew, fixParName, fixPar)
	yD = m * x + b
	return m, b, CoD, yD, err, mErr, bErr



def sin2PsiAnalysis(data, maxPsi=None):
	# data: dVals, errVals, tauVals, phiVals, psiVals, hklVal, s1Val, hs2Val, ibVals???
	# extract needed data
	dVals = data['dVals']
	dErrVals = data['dErr']
	tauVals = data['tauVals']
	phiVals = data['phiVals']
	psiVals = data['psiVals']
	ibVals = data['ibVals']
	hklVal = data['hklVal']
	s1Val = data['s1Val']
	hs2Val = data['hs2Val']
	a0Val = data['a0Val'] if 'a0Val' in data else None
	# define derived values
	phiUni = np.sort(np.unique(phiVals))
	psiUni = np.unique(psiVals)
	psiUniWithoutZero = psiUni[psiUni != 0]
	psiSign = np.sign(psiUniWithoutZero[-1])  # sign of last psi value
	psiUni = psiUni[(np.sign(psiUni) == psiSign) | (psiUni == 0)]  # only negative or positive values
	if maxPsi is not None:
		psiUni = psiUni[(psiUni <= maxPsi) & (psiUni >= -maxPsi)]  # take only values smaller than or equal to |maxPsi°|
	maxUsedPsi = np.max(np.abs(psiUni))
	sinpsi2Uni = np.sin(np.radians(psiUni)) ** 2
	sin2psiUni = np.sin(np.radians(np.abs(2 * psiUni)))
	# define global regression values
	mVals = np.zeros(6)
	bVals = np.zeros(6)
	errVals = np.zeros(6)
	errValsStar = 0
	# perform linear regressions for one peak
	sinpsi2StarSingle = s1Val / hs2Val
	sinpsi2Star = -2 * s1Val / hs2Val
	sinpsi2Plus = 1 + s1Val / hs2Val
	dValsValid = (dVals > 0) & (np.isnan(dVals) == False)
	tauValsValid = (tauVals >= 0) & (tauVals < 1e6)
	ibValsValid = (ibVals > 0) & (ibVals < 1000)
	if maxPsi is None:
		tauMean = np.sum(tauVals[tauValsValid]) / len(tauVals[tauValsValid])
		# tauMean = (max(tauVals[tauValsValid]) + min(tauVals[tauValsValid])) / 2
	else:
		# take only values smaller than or equal to | maxPsi° |
		curTau = tauVals[(psiVals <= maxPsi) & (psiVals >= -maxPsi) & tauValsValid]
		tauMean = np.sum(curTau) / len(curTau)
		# tauMean = (max(curTau) + min(curTau)) / 2
	# determine mean values of IB
	valuesIb = np.zeros(len(phiUni))
	for j in range(len(phiUni)):
		if maxPsi is None:
			valuesIb[j] = np.mean(ibVals[phiVals == phiUni[j] & ibValsValid])
		else:
			valuesIb[j] = np.mean(ibVals[(phiVals == phiUni[j]) & (psiVals <= maxPsi) & (psiVals >= -maxPsi) & ibValsValid])
	# perform linear regression of all phi values
	valsAll = np.zeros((len(psiUni), 2))
	vals45 = np.zeros((len(psiUni), 2))
	vals0_180 = np.zeros((len(psiUni), 3))
	vals90_270 = np.zeros((len(psiUni), 3))
	for i in range(len(psiUni)):
		if np.max(np.isin(psiVals, psiUni[i])) and np.max(np.isin(psiVals, -psiUni[i])):
			# positive and negative psi values
			val0 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 0) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 0) & dValsValid]])
			val90 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 90) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 90) & dValsValid]])
			val180 = np.array([dVals[(psiVals == -psiUni[i]) & (phiVals == 0) & dValsValid],
				dErrVals[(psiVals == -psiUni[i]) & (phiVals == 0) & dValsValid]])
			val270 = np.array([dVals[(psiVals == -psiUni[i]) & (phiVals == 90) & dValsValid],
				dErrVals[(psiVals == -psiUni[i]) & (phiVals == 90) & dValsValid]])
		else:
			val0 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 0) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 0) & dValsValid]])
			val90 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 90) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 90) & dValsValid]])
			val180 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 180) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 180) & dValsValid]])
			val270 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 270) & dValsValid],
				dErrVals[(psiVals == psiUni[i]) & (phiVals == 270) & dValsValid]])
		val45 = np.array([dVals[(psiVals == psiUni[i]) & (phiVals == 45) & dValsValid],
			dErrVals[(psiVals == psiUni[i]) & (phiVals == 45) & dValsValid]])
		if val45.size > 0:
			vals45[i, :] = val45
		if val0.size > 0 and val180.size > 0:
			vals0_180[i, 0] = 0.5 * (val0[0] + val180[0])
			vals0_180[i, 1] = 0.5 * (val0[0] - val180[0])
			vals0_180[i, 2] = 0.5 * (val0[1] + val180[1])
		elif val0.size > 0:
			vals0_180[i, 0] = val0[0]
			vals0_180[i, 1] = 0
			vals0_180[i, 2] = val0[1]
		elif val180.size > 0:
			vals0_180[i, 0] = val180[0]
			vals0_180[i, 1] = 0
			vals0_180[i, 2] = val180[1]
		if val90.size > 0 and val270.size > 0:
			vals90_270[i, 0] = 0.5 * (val90[0] + val270[0])
			vals90_270[i, 1] = 0.5 * (val90[0] - val270[0])
			vals90_270[i, 2] = 0.5 * (val90[1] + val270[1])
		elif val90.size > 0:
			vals90_270[i, 0] = val90[0]
			vals90_270[i, 1] = 0
			vals90_270[i, 2] = val90[1]
		elif val270.size > 0:
			vals90_270[i, 0] = val270[0]
			vals90_270[i, 1] = 0
			vals90_270[i, 2] = val270[1]
		if vals0_180[i, 0] != 0 and vals90_270[i, 0] != 0:
			valsAll[i, :] = 0.5 * (vals0_180[i, [0, 2]] + vals90_270[i, [0, 2]])
	# check for validity
	# perform linear regression for all phi values
	usedIndex = np.array(range(len(psiUni)))
	used = usedIndex[valsAll[:, 0] != 0]
	if len(used) > 0:
		if np.all(valsAll[used, 1] != 0):
			[m, b, CoD, yD, err, err33, bErr] = linRegWeighted(sinpsi2Uni[used], valsAll[used, 0], 1 / valsAll[used, 1])
		else:
			[m, b, CoD, yD, err, err33, bErr] = linReg(sinpsi2Uni[used], valsAll[used, 0])
		mVals[5] = m
		bVals[5] = b
		errVals[5] = err33
		errValsStar = bErr
	# perform linear regression of phi values with phi = 45° (if exist)
	used12 = usedIndex[vals45[:, 0] != 0]
	if len(used12) > 0:
		if len(used) > 0:
			if np.all(vals45[used12, 1] != 0):
				[m12, b12, CoD12, yD12, err, err12, bErr] = linRegWeighted(sinpsi2Uni[used12], vals45[used12, 0],
					1 / vals45[used12, 1], 'b', b)
			else:
				[m12, b12, CoD12, yD12, err, err12, bErr] = linReg(sinpsi2Uni[used12], vals45[used12, 0], 'b', b)
		else:
			if np.all(vals45[used12, 1] != 0):
				[m12, b12, CoD12, yD12, err, err12, bErr] = linRegWeighted(sinpsi2Uni[used12], vals45[used12, 0],
					1 / vals45[used12, 1])
			else:
				[m12, b12, CoD12, yD12, err, err12, bErr] = linReg(sinpsi2Uni[used12], vals45[used12, 0])
			mVals[5] = m12
			bVals[5] = b12
		mVals[4] = m12
		bVals[4] = b12
		errVals[4] = err12
	# perform linear regression of phi values with phi = 0°/180°
	used1 = usedIndex[vals0_180[:, 0] != 0]
	if len(used1) > 0:
		if len(used) > 0:
			if np.all(vals0_180[used1, 2] != 0):
				[m1, b1, CoD1, yD1, err, err1, bErr] = linRegWeighted(sinpsi2Uni[used1], vals0_180[used1, 0],
					1 / vals0_180[used1, 2], 'b', b)
			else:
				[m1, b1, CoD1, yD1, err, err1, bErr] = linReg(sinpsi2Uni[used1], vals0_180[used1, 0], 'b', b)
		else:
			if np.all(vals0_180[used1, 2] != 0):
				[m1, b1, CoD1, yD1, err, err1, bErr] = linRegWeighted(sinpsi2Uni[used1], vals0_180[used1, 0],
					1 / vals0_180[used1, 2])
			else:
				[m1, b1, CoD1, yD1, err, err1, bErr] = linReg(sinpsi2Uni[used1], vals0_180[used1, 0])
			mVals[5] = m1
			bVals[5] = b1
		# [m1f, err1f] = lsqcurvefit(linM,m1,sinpsi2Uni(used1),vals0_180(used1,1));
		mVals[0] = m1
		bVals[0] = b1
		errVals[0] = err1
		if np.all(vals0_180[used1, 2] != 0):
			[m13, b13, CoD13, yD13, err, err13, bErr] = linRegWeighted(sin2psiUni[used1], vals0_180[used1, 1],
				1 / vals0_180[used1, 2], 'b', 0)
		else:
			[m13, b13, CoD13, yD13, err, err13, bErr] = linReg(sin2psiUni[used1], vals0_180[used1, 1], 'b', 0)
		# [m1f, err1f] = lsqcurvefit(linBase,m1,sin2psiUni(used1),vals0_180(used1,2));
		mVals[2] = m13
		bVals[2] = b13
		errVals[2] = err13
	# perform linear regression of phi values with phi = 90°/270°
	used2 = usedIndex[vals90_270[:, 0] != 0]
	if len(used2) > 0:
		if len(used) > 0:
			if np.all(vals90_270[used2, 2] != 0):
				[m2, b2, CoD2, yD2, err, err2, bErr] = linRegWeighted(sinpsi2Uni[used2], vals90_270[used2, 0],
					1 / vals90_270[used2, 2], 'b', b)
			else:
				[m2, b2, CoD2, yD2, err, err2, bErr] = linReg(sinpsi2Uni[used2], vals90_270[used2, 0], 'b', b)
		else:
			if np.all(vals90_270[used2, 2] != 0):
				[m2, b2, CoD2, yD2, err, err2, bErr] = linRegWeighted(sinpsi2Uni[used2], vals90_270[used2, 0],
					1 / vals90_270[used2, 2])
			else:
				[m2, b2, CoD2, yD2, err, err2, bErr] = linReg(sinpsi2Uni[used2], vals90_270[used2, 0])
			mVals[5] = m2
			bVals[5] = b2
		# [m2f, err2f] = lsqcurvefit(linM,m2,sinpsi2Uni(used2),vals90_270(used2,1));
		mVals[1] = m2
		bVals[1] = b2
		errVals[1] = err2
		if np.all(vals90_270[used2, 2] != 0):
			[m23, b23, CoD23, yD23, err, err23, bErr] = linRegWeighted(sin2psiUni[used2], vals90_270[used2, 1],
				1 / vals90_270[used2, 2], 'b', 0)
		else:
			[m23, b23, CoD23, yD23, err, err23, bErr] = linReg(sin2psiUni[used2], vals90_270[used2, 1], 'b', 0)
		# [m2f, err2f] = lsqcurvefit(linBase,m2,sin2psiUni(used2),vals90_270(used2,2));
		mVals[3] = m23
		bVals[3] = b23
		errVals[3] = err23
	# determine stresses
	dStarVal0 = mVals[0] * sinpsi2StarSingle + bVals[0]
	dStarVal90 = mVals[1] * sinpsi2StarSingle + bVals[1]
	dStarVal = mVals[5] * sinpsi2Star + bVals[5]
	dPlusVal = mVals[5] * sinpsi2Plus + bVals[5]
	dComVal = mVals[5] * 2 / 3 + bVals[5]
	s11_s33 = mVals[0] / (hs2Val * dStarVal)
	ds11 = 2 * errVals[0] ** 0.5 / (hs2Val * dStarVal)
	s22_s33 = mVals[1] / (hs2Val * dStarVal)
	ds22 = 2 * errVals[1] ** 0.5 / (hs2Val * dStarVal)
	s13 = mVals[2] / (hs2Val * dStarVal)
	ds13 = 2 * errVals[2] ** 0.5 / (hs2Val * dStarVal)
	s23 = mVals[3] / (hs2Val * dStarVal)
	ds23 = 2 * errVals[3] ** 0.5 / (hs2Val * dStarVal)
	if np.any((phiVals == 45) | (phiVals == -45) | (phiVals == 225)):
		s12 = mVals[4] / (hs2Val * dStarVal) - 0.5 * (s11_s33 + s22_s33)
	else:
		s12 = mVals[4] / (hs2Val * dStarVal)
	ds12 = 2 * errVals[4] ** 0.5 / (hs2Val * dStarVal)
	# aStarVal = conv.latticeDists2aVals2(dStarVal, hklVal)
	aStarVal = dStarVal * ((hklVal // 100) ** 2 + ((hklVal % 100) // 10) ** 2 + (hklVal % 10) ** 2) ** 0.5
	if a0Val is None or a0Val == 0:
		s33 = 0
		ds33 = 0
	else:
		s33 = (aStarVal / a0Val - 1) / (hs2Val + 3 * s1Val)
		ds33 = 2 * errVals[5] ** 0.5 / (hs2Val * dStarVal)
	# d0_1 = regVals(:,2) ./ (dekList(:,2) .* (s11_s33 + s22_s33) + s33 .* f33 + 1);
	#     [sMain, d0, quality] = stressesWithS33(dekList, dStarVals, [s11_s33 s22_s33 s12 s13 s23], ...
	#         [data(:,1) dVals error data(:,[7 8])], plotData);
	# combine results
	stresses = np.array([s11_s33, s22_s33, s13, s23, s12, s33])
	accuracy = np.array([ds11, ds22, ds13, ds23, ds12, ds33])
	# resData: tauMean, dStar, stresses, accuracy, mVals???, bVals???
	resData = {'tauMean': tauMean, 'dStar100': aStarVal, 'dStar100Err': 2 * errValsStar ** 0.5,
		'stresses': stresses, 'accuracy': accuracy, 'meanIB': valuesIb}
	plotData = {'dVals': data['dVals'], 'dErr': data['dErr'], 'phiVals': data['phiVals'],
		'psiVals': data['psiVals'], 'hklVal': hklVal, 'mVals': mVals, 'bVals': bVals, 'errVals': errVals,
		'sinpsi2Star': sinpsi2Star, 'meanVals': valsAll[used,:]}
	if len(used) > 0:
		plotData['xMean'] = sinpsi2Uni[used]
		plotData['yMean'] = yD
	if len(used12) > 0:
		plotData['x12'] = sinpsi2Uni[used12]
		plotData['y12'] = yD12
	if len(used1) > 0:
		plotData['x1'] = sinpsi2Uni[used1]
		plotData['y1'] = yD1
	if len(used2) > 0:
		plotData['x2'] = sinpsi2Uni[used2]
		plotData['y2'] = yD2
	return resData, plotData


def multiWavelengthAnalysis(data, maxPsi=None):
	prefixes = list(sorted(
		set(col.split('_')[0] for col in data.keys() if 'center' in col),
		key=lambda px: np.mean(data['_'.join((px, 'depth'))])))
	phiVals = data['phi']
	psiVals = data['psi']
	tauMean = np.zeros(len(prefixes))
	hklList = np.zeros(len(prefixes), dtype=np.int)
	s1Dec = np.zeros(len(prefixes))
	hs2Dec = np.zeros(len(prefixes))
	dStarVals = np.zeros(len(prefixes))
	dStarErrVals = np.zeros(len(prefixes))
	stresses = np.zeros((len(prefixes), 6))  # s11-33 s22-33 s13 s23 s12 s33
	accuracy = np.zeros((len(prefixes), 6))
	integralWidth = np.zeros((len(prefixes), 6))  # phi0 phi90 phi180 phi270 phi45 phi225
	plotData = dict()
	for p, prefix in enumerate(prefixes):  # perform this for all peaks
		ibVals = data[prefix + '_sigma']
		centerVals = data[prefix + '_center']
		centerErrVals = data[prefix + '_center_std']
		dMinVals = bragg(en=centerVals - centerErrVals, tth=data['tth'])['d'] / 10.
		dMaxVals = bragg(en=centerVals + centerErrVals, tth=data['tth'])['d'] / 10.
		dErrVals = np.abs(dMaxVals - dMinVals) / 2
		tauVals = data[prefix + '_depth']
		dVals = data[prefix + '_dspac'] / 10
		hVals = data[prefix + '_h']  # second version
		kVals = data[prefix + '_k']  # second version
		lVals = data[prefix + '_l']  # second version
		s1Vals = data[prefix + '_s1']  # second version
		hs2Vals = data[prefix + '_hs2']  # third version
		hklList[p] = hVals[0] * 100 + kVals[0] * 10 + lVals[0]
		s1Dec[p] = s1Vals[0]
		hs2Dec[p] = hs2Vals[0]
		curData = {
			'dVals': dVals, 'dErr': dErrVals, 'tauVals': tauVals, 'phiVals': phiVals, 'psiVals': psiVals,
			'hklVal': hklList[p], 's1Val': s1Dec[p], 'hs2Val': hs2Dec[p], 'ibVals': ibVals, 'a0Val': data['a0Val']
		}

		# perform sin2psi analysis for current peak data
		curResData, curPlotData = sin2PsiAnalysis(curData, maxPsi)
		# remember results
		tauMean[p] = curResData['tauMean']
		dStarVals[p] = curResData['dStar100']
		dStarErrVals[p] = curResData['dStar100Err']
		stresses[p] = curResData['stresses']
		accuracy[p] = curResData['accuracy']
		curMeanIB = curResData['meanIB']
		integralWidth[p, 0:len(curMeanIB)] = curMeanIB
		plotData[str(hklList[p])] = curPlotData
	# resData: hklList, s1Dec, hs2Dec, tauMean, aStar, aStarErr, stresses, accuracy, mVals???, bVals???
	sort_idx = np.argsort(tauMean)
	resData = {'hklList': hklList[sort_idx], 's1Dec': s1Dec[sort_idx], 'hs2Dec': hs2Dec[sort_idx], 'tauMean': tauMean[sort_idx], 'dStar100': dStarVals[sort_idx],
		'dStar100Err': dStarErrVals[sort_idx], 'stresses': stresses[sort_idx], 'accuracy': accuracy[sort_idx], 'integralWidth': integralWidth[sort_idx]}
	return resData, plotData


########################################################################################################################


def universalPlotAnalysis(data, maxPsi=None, minDistPsiStar=0.15, minValPsiNormal=0.08,
		minValPsiShear=0.8):
	# extract needed data
	# a0Val = bf.getDictValOrDef(data, 'a0Val')
	a0Val = data['a0Val'] if 'a0Val' in data else None
	psiUni = data['psiUni']
	sin2psiUni = data['sin2psiUni']
	sinpsi2Uni = data['sinpsi2Uni']
	psiVals = data['psiVals']
	phiVals = data['phiVals']
	dVals = data['dVals']
	dErrVals = data['dErrVals']
	tauVals = data['tauVals']
	hklVal = data['hklVal']
	s1Val = data['s1Val']
	hs2Val = data['hs2Val']
	phi4 = data['phi4']
	dValsValid = (dVals > 0) & (np.isnan(dVals) == False)
	tauValsValid = (tauVals >= 0) & (tauVals < 1e6)
	# define needed variables
	sinpsi2Star = -2 * s1Val / hs2Val
	psiStar = np.degrees(np.arcsin(sinpsi2Star ** 0.5))
	valsAll = np.zeros((len(psiUni), 3))
	fplus = np.zeros((len(psiUni), 3))
	fminus = np.zeros((len(psiUni), 3))
	f13 = np.zeros((len(psiUni), 3))
	f23 = np.zeros((len(psiUni), 3))
	stresses = np.zeros((len(psiUni), 4))
	errVals = np.zeros((len(psiUni), 4))
	tauRes = np.zeros(len(psiUni))
	resData = dict()
	validCounter = 0
	for i in range(len(psiUni)):
		if phi4:
			cond0 = (psiVals == psiUni[i]) & (phiVals == 0) & dValsValid
			cond90 = (psiVals == psiUni[i]) & (phiVals == 90) & dValsValid
			cond180 = (psiVals == psiUni[i]) & (phiVals == 180) & dValsValid
			cond270 = (psiVals == psiUni[i]) & (phiVals == 270) & dValsValid
		else:
			cond0 = (psiVals == psiUni[i]) & (phiVals == 0) & dValsValid
			cond90 = (psiVals == psiUni[i]) & (phiVals == 90) & dValsValid
			cond180 = (psiVals == -psiUni[i]) & (phiVals == 0) & dValsValid
			cond270 = (psiVals == -psiUni[i]) & (phiVals == 90) & dValsValid
		val0 = np.concatenate((dVals[cond0], dVals[cond0] - dErrVals[cond0],
			dVals[cond0] + dErrVals[cond0]))
		val90 = np.concatenate((dVals[cond90], dVals[cond90] - dErrVals[cond90],
			dVals[cond90] + dErrVals[cond90]))
		val180 = np.concatenate((dVals[cond180], dVals[cond180] - dErrVals[cond180],
			dVals[cond180] + dErrVals[cond180]))
		val270 = np.concatenate((dVals[cond270], dVals[cond270] - dErrVals[cond270],
			dVals[cond270] + dErrVals[cond270]))
		if len(val0) > 0 and len(val90) > 0 and len(val180) > 0 and len(val270) > 0:
			fplus[i, :] = val0 + val90 + val180 + val270
			fminus[i, :] = (val0 + val180) - (val90 + val270)
			f13[i, :] = val0 - val180
			f23[i, :] = val90 - val270
			valsAll[i, :] = 0.25 * fplus[i, :]
			tauRes[i] = np.mean(tauVals[(psiVals == psiUni[i]) & tauValsValid])
			validCounter += 1
	# perform linear regression for all phi values to get dstar
	used = valsAll[:, 0] != 0
	if len(valsAll[used, 0]) > 1:
		if maxPsi is not None:
			usedReg = (sinpsi2Uni <=np.sin(np.radians(maxPsi)) ** 2) & used
		else:
			usedReg = used
		[m, b, CoD, yD, err, mErr, bErr] = linRegWeighted(sinpsi2Uni[usedReg], valsAll[usedReg, 0],
			1 / valsAll[usedReg, 1])
		dStarVal = m * sinpsi2Star + b
		# calculate fplus
		denom = hs2Val * sinpsi2Uni[used] + 2 * s1Val
		fplus[used, 0] = (0.25 * fplus[used, 0] / dStarVal - 1) / denom
		fplus[used, 1] = (0.25 * fplus[used, 1] / dStarVal - 1) / denom
		fplus[used, 2] = (0.25 * fplus[used, 2] / dStarVal - 1) / denom
		# indicate or correct invalid values
		if minDistPsiStar is not None:
			invalidVals = used & (np.abs(sinpsi2Uni - sinpsi2Star) <= minDistPsiStar)  # around psiStar
			fplus[invalidVals, 0] = np.NAN
			fplus[invalidVals, 1] = np.NAN
			fplus[invalidVals, 2] = np.NAN

		# calculate fminus
		fminus[used, 0] = 0.25 * (fminus[used, 0] / dStarVal) / (hs2Val * sinpsi2Uni[used])
		fminus[used, 1] = 0.25 * (fminus[used, 1] / dStarVal) / (hs2Val * sinpsi2Uni[used])
		fminus[used, 2] = 0.25 * (fminus[used, 2] / dStarVal) / (hs2Val * sinpsi2Uni[used])
		# indicate invalid values
		if minValPsiNormal is not None:
			invalidVals = used & (sinpsi2Uni <= minValPsiNormal)  # small psi values
			fminus[invalidVals, 0] = np.NAN
			fminus[invalidVals, 1] = np.NAN
			fminus[invalidVals, 2] = np.NAN
		# calculate f13 and f23
		f13[used, 0] = 0.5 * (f13[used, 0] / dStarVal) / (hs2Val * sin2psiUni[used])
		f13[used, 1] = 0.5 * (f13[used, 1] / dStarVal) / (hs2Val * sin2psiUni[used])
		f13[used, 2] = 0.5 * (f13[used, 2] / dStarVal) / (hs2Val * sin2psiUni[used])
		f23[used, 0] = 0.5 * (f23[used, 0] / dStarVal) / (hs2Val * sin2psiUni[used])
		f23[used, 1] = 0.5 * (f23[used, 1] / dStarVal) / (hs2Val * sin2psiUni[used])
		f23[used, 2] = 0.5 * (f23[used, 2] / dStarVal) / (hs2Val * sin2psiUni[used])
		# indicate invalid values
		if minValPsiShear is not None:
			invalidVals = used & (sin2psiUni <= minValPsiShear)  # small and high psi values
			f13[invalidVals, 0] = np.NAN
			f13[invalidVals, 1] = np.NAN
			f13[invalidVals, 2] = np.NAN
			f23[invalidVals, 0] = np.NAN
			f23[invalidVals, 1] = np.NAN
			f23[invalidVals, 2] = np.NAN
		# determine stresses
		stresses[used, 0] = fplus[used, 0] + fminus[used, 0]
		stresses[used, 1] = fplus[used, 0] - fminus[used, 0]
		stresses[used, 2] = f13[used, 0]
		stresses[used, 3] = f23[used, 0]
		# determine error values
		errVals[used, 0] = np.abs((fplus[used, 2] + fminus[used, 2]) - (fplus[used, 1] + fminus[used, 1])) / 2
		errVals[used, 1] = np.abs((fplus[used, 2] - fminus[used, 2]) - (fplus[used, 1] - fminus[used, 1])) / 2
		errVals[used, 2] = np.abs(f13[used, 2] - f13[used, 1]) / 2
		errVals[used, 3] = np.abs(f23[used, 2] - f23[used, 1]) / 2
		# also determine s33
		# minVal, minPos = bf.min(abs(psiVals[tauValsValid] - psiStar))
		minPos = np.argmin(abs(psiVals[tauValsValid] - psiStar))
		tauS33 = np.mean(tauVals[minPos])  # tau equivalent to condition at psiStar
		# leftVal, leftPos = bf.max(psiVals[psiVals < psiStar])
		# rightVal, rightPos = bf.min(psiVals[psiVals > psiStar])
		# tauS33 = np.interp(psiStar, [leftVal, rightVal], [tauVals[leftPos], tauVals[rightPos]])
		# aStarVal = conv.latticeDists2aVals2(dStarVal, hklVal)
		aStarVal = dStarVal * ((hklVal // 100) ** 2 + ((hklVal % 100) // 10) ** 2 + (hklVal % 10) ** 2) ** 0.5
		if a0Val is None or a0Val == 0:
			s33 = 0
			ds33 = 0
		else:
			s33 = (aStarVal / a0Val - 1) / (s1Val + 3 * hs2Val)
			ds33 = 2 * mErr ** 0.5 / (hs2Val * dStarVal)
		resData = {'tauRes': tauRes, 'stresses': stresses, 'errVals': errVals, 'validCounter': validCounter,
			'tauS33': tauS33, 'dStar100': aStarVal, 'dStar100Err': 2 * bErr ** 0.5, 's33': s33, 'dev_s33': ds33}
	return resData


def multiUniversalPlotAnalysis(data, maxPsi=None, minDistPsiStar=0.15,
		minValPsiNormal=0.08, minValPsiShear=0.8):
	# keyList = bf.getKeyList(data)
	# peakCount = int(bf.replace(keyList[-1].split('_')[0], 'pv')) + 1  # must be adapted in further versions!!!
	prefixes = list(sorted(
		set(col.split('_')[0] for col in data.keys() if 'center' in col),
		key=lambda px: np.mean(data['_'.join((px, 'center'))])))
	tthVal = data['tth']
	phiVals = data['phi']
	psiVals = data['psi']
	psiUni = np.unique(psiVals)
	psiUni = psiUni[psiUni != 0]  # no zero value
	psiSign = np.sign(psiUni[-1])  # sign of last psi value
	psiUni = psiUni[np.sign(psiUni) == psiSign]  # only negative or positive values
	sinpsi2Uni = np.sin(np.radians(psiUni)) ** 2
	sin2psiUni = np.sin(np.radians(np.abs(2 * psiUni)))
	tauRes = np.zeros((len(prefixes), len(psiUni)))
	hklRes = np.zeros((len(prefixes), len(psiUni)))
	psiRes = np.zeros((len(prefixes), len(psiUni)))
	stresses = np.zeros((len(prefixes), len(psiUni), 4))
	errVals = np.zeros((len(prefixes), len(psiUni), 4))
	tauS33 = np.zeros(len(prefixes))
	aStarVals = np.zeros(len(prefixes))
	aStarErrVals = np.zeros(len(prefixes))
	s33 = np.zeros(len(prefixes))
	dev_s33 = np.zeros(len(prefixes))
	hklList = np.zeros(len(prefixes))
	phi4 = len(np.unique(phiVals)) == 4
	validCounter = 0
	for p, prefix in enumerate(prefixes):  # for all peaks create one plot
		centerVals = data[prefix + '_center']
		centerErrVals = data[prefix + '_center_std']
		# dMinVals = conv.energies2latticeDists(centerVals - centerErrVals, tthVal)
		# dMaxVals = conv.energies2latticeDists(centerVals + centerErrVals, tthVal)
		dMinVals = bragg(en=centerVals - centerErrVals, tth=tthVal)['d'] / 10.
		dMaxVals = bragg(en=centerVals + centerErrVals, tth=tthVal)['d'] / 10.
		dErrVals = np.abs(dMaxVals - dMinVals) / 2
		tauVals = data[prefix + '_depth']
		dVals = data[prefix + '_dspac'] / 10  # in nm
		hVals = data[prefix + '_h']  # second version
		kVals = data[prefix + '_k']  # second version
		lVals = data[prefix + '_l']  # second version
		s1Vals = data[prefix + '_s1']  # second version
		hs2Vals = data[prefix + '_hs2']  # third version
		hklVal = hVals[0] * 100 + kVals[0] * 10 + lVals[0]
		hklList[p] = hklVal
		hklRes[p] = hklVal * np.ones(len(psiUni))
		psiRes[p] = psiUni
		s1Val = s1Vals[0]
		#hs2Val = hs2Vals[0] * 0.5  # test valid for first and second version!!!!!
		hs2Val = hs2Vals[0]
		curData = {'tauVals': tauVals, 'dVals': dVals, 'dErrVals': dErrVals, 'psiVals': psiVals,
			'phiVals': phiVals, 'psiUni': psiUni, 'sin2psiUni': sin2psiUni, 'sinpsi2Uni': sinpsi2Uni, 'phi4': phi4,
			'hklVal': hklVal, 's1Val': s1Val, 'hs2Val': hs2Val}
		curData['a0Val'] = data['a0Val']
		# perform universal plot analysis for current peak data
		curResData = universalPlotAnalysis(curData, maxPsi, minDistPsiStar,
			minValPsiNormal, minValPsiShear)
		# remember results
		tauRes[p] = curResData['tauRes']
		stresses[p] = curResData['stresses']
		errVals[p] = curResData['errVals']
		aStarVals[p] = curResData['dStar100']
		aStarErrVals[p] = curResData['dStar100Err']
		tauS33[p] = curResData['tauS33']
		s33[p] = curResData['s33']
		dev_s33[p] = curResData['dev_s33']
		validCounter += curResData['validCounter']
	# reshape data
	tauRes = np.reshape(tauRes, np.prod(tauRes.shape))
	hklRes = np.reshape(hklRes, np.prod(hklRes.shape))
	psiRes = np.reshape(psiRes, np.prod(psiRes.shape))
	stresses = np.reshape(stresses, (np.shape(stresses)[0] * np.shape(stresses)[1], np.shape(stresses)[2]))
	errVals = np.reshape(errVals, (np.shape(errVals)[0] * np.shape(errVals)[1], np.shape(errVals)[2]))
	# remove values with tau = 0
	hklRes = hklRes[tauRes > 0]
	psiRes = psiRes[tauRes > 0]
	stresses = stresses[tauRes > 0]
	errVals = errVals[tauRes > 0]
	tauRes = tauRes[tauRes > 0]
	# sort data concerning increasing information depth
	hklRes = hklRes[np.argsort(tauRes)]
	psiRes = psiRes[np.argsort(tauRes)]
	stresses = stresses[np.argsort(tauRes)]
	errVals = errVals[np.argsort(tauRes)]
	tauRes = tauRes[np.argsort(tauRes)]
	resData = {'tauVals': tauRes, 'stresses': stresses, 'accuracy': errVals, 'hklVals': hklRes,
		'psiVals': psiRes, 'validCount': validCounter}
	sort_idx = np.argsort(tauS33)
	resDataS33 = {'tauMean': tauS33[sort_idx], 'dStar100': aStarVals[sort_idx], 'dStar100Err': aStarErrVals[sort_idx], 's33': s33[sort_idx],
		'dev_s33': dev_s33[sort_idx], 'hklList': hklList[sort_idx]}
	return resData, resDataS33


########################################################################################################################


def plotSin2Psi(data, showErr=True):
	symbols = ['s', '^', 'p', 'd', 'v', 'o', '+', 'x', '*', 'h', '<', '>', '.']
	colors = ['r', 'g', 'b', 'c', 'm', 'y', 'r', 'g', 'b', 'c', 'm']
	# extract relevant data
	dVals = data['dVals']
	dErrVals = data['dErr']
	phiVals = data['phiVals']
	psiVals = data['psiVals']
	hklVal = data['hklVal']
	mVals = data['mVals']
	bVals = data['bVals']
	errVals = data['errVals']
	valsAll = data['meanVals']
	sinpsi2Star = data['sinpsi2Star']
	# define derived values
	phiUni = np.sort(np.unique(phiVals))
	sinpsi2 = np.sin(np.radians(psiVals)) ** 2
	psiUni = np.unique(psiVals)
	psiUniWithoutZero = psiUni[psiUni != 0]
	psiSign = np.sign(psiUniWithoutZero[-1])  # sign of last psi value
	psiUni = psiUni[(np.sign(psiUni) == psiSign) | (psiUni == 0)]  # only negative or positive values
	maxUsedPsi = np.max(np.abs(psiUni))
	sinpsi2Distr = np.arange(0, 1.001, 0.01)
	t = plt.figure()
	for i in range(len(phiUni)):  # for each phi value plot data points
		used = phiVals == phiUni[i]
		if showErr:
			# plt.errorbar(sinpsi2[used], dVals[used], dErrVals[used], fmt=colors[i] + symbols[i], ecolor='k')
			plt.errorbar(sinpsi2[used], dVals[used], dErrVals[used], fmt=colors[i] + symbols[i],
				label='Phi=' + str(phiUni[i]) + '°')
		else:
			plt.plot(sinpsi2[used], dVals[used], colors[i] + symbols[i], label='Phi=' + str(phiUni[i]) + '°')
	# plot regression results
	if mVals[5] != 0 or bVals[5] != 0:  # mean
		xMean = data['xMean']
		if showErr:
			# plt.errorbar(xMean, valsAll[:, 0], valsAll[:, 0] * valsAll[:, 1],
			# fmt=colors[4] + symbols[4], ecolor='k')
			plt.errorbar(xMean, valsAll[:, 0], valsAll[:, 0] * valsAll[:, 1], fmt=colors[4] + symbols[4],
				label='mean values')
		else:
			plt.plot(xMean, valsAll[:, 0], colors[4] + symbols[4], label='mean values')
		plt.plot(xMean, data['yMean'], 'k.')
	if mVals[4] != 0 or bVals[4] != 0:  # s12
		plt.plot(data['x12'], data['y12'], 'k.')
	if mVals[0] != 0 or bVals[0] != 0:  # s11
		plt.plot(data['x1'], data['y1'], 'k.')
	if mVals[1] != 0 or bVals[1] != 0:  # s22
		plt.plot(data['x2'], data['y2'], 'k.')
	if mVals[5] != 0 or bVals[5] != 0:  # mean
		plt.plot([0, 1], [bVals[5], mVals[5] + bVals[5]], 'k-')
	if mVals[4] != 0 or bVals[4] != 0:  # s12
		plt.plot([0, 1], [bVals[4], mVals[4] + bVals[4]], 'k-')
	if mVals[0] != 0 or bVals[0] != 0:  # s11
		plt.plot([0, 1], [bVals[0], mVals[0] + bVals[0]], 'k-')
	if mVals[1] != 0 or bVals[1] != 0:  # s22
		plt.plot([0, 1], [bVals[1], mVals[1] + bVals[1]], 'k-')
	if mVals[5] != 0 or bVals[5] != 0:  # mean
		plt.plot(sinpsi2Distr, mVals[0] * sinpsi2Distr + mVals[2] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[5], 'k:')
		plt.plot(sinpsi2Distr, mVals[0] * sinpsi2Distr - mVals[2] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[5], 'k:')
		plt.plot(sinpsi2Distr, mVals[1] * sinpsi2Distr + mVals[3] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[5], 'k:')
		plt.plot(sinpsi2Distr, mVals[1] * sinpsi2Distr - mVals[3] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[5], 'k:')
	else:
		if mVals[0] != 0 or bVals[0] != 0:  # s11
			plt.plot(sinpsi2Distr,
				mVals[0] * sinpsi2Distr + mVals[2] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[0], 'k:')
			plt.plot(sinpsi2Distr,
				mVals[0] * sinpsi2Distr - mVals[2] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[0], 'k:')
		if mVals[1] != 0 or bVals[1] != 0:  # s22
			plt.plot(sinpsi2Distr,
				mVals[1] * sinpsi2Distr + mVals[3] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[1], 'k:')
			plt.plot(sinpsi2Distr,
				mVals[1] * sinpsi2Distr - mVals[3] * 2 * (sinpsi2Distr * (1 - sinpsi2Distr)) ** 0.5 + bVals[1], 'k:')
	# plot line at sin2psiStar
	# plt.vlines(bf.ones(2, 1) * sinpsi2Star, np.min(dVals), np.max(dVals), 'k', 'dashed')
	plt.grid()
	plt.xlabel('sin^2 psi')
	plt.ylabel('d in nm')
	plt.legend()
	plt.title('sin^2 psi curve for (' + str(hklVal) + ') peak')
	plt.tight_layout()  # layout without overlapping
	plt.show()  # saveas(gcf,[pathName,'Auswertung\Sin2Psi_',num2str(p),'.fig'])


def plotMultiWavelength(data, showErr=True):
	hklNames = list(data.keys())
	for hkl in hklNames:
		plotSin2Psi(data[hkl], showErr)


def plotErrData(y, yErr, x=None, lineSpec="ro-", gridState="on", xLabel="", yLabel="", titleTxt="", ecol=None):
	h = plt.figure()
	if x is None:
		x = np.array(range(len(y)))
	if ecol is None:
		plt.errorbar(x, y, 2 * yErr, fmt=lineSpec, capsize=3)
	else:
		plt.errorbar(x, y, 2 * yErr, fmt=lineSpec, capsize=3, ecolor=ecol)
	plt.grid(gridState == "on")
	plt.xlabel(xLabel)
	plt.ylabel(yLabel)
	plt.title(titleTxt)
	plt.tight_layout()  # layout without overlapping
	plt.show()
	return h


def plotData(y, x=None, lineSpec="r.-", gridState="on", xLabel="", yLabel="", titleTxt="", figInst=None):
	if figInst is None:
		h = plt.figure()
	else:
		h = figInst
	if x is None:
		x = np.array(range(len(y)))
	plt.plot(x, y, lineSpec)
	plt.grid(gridState == "on")
	plt.xlabel(xLabel)
	plt.ylabel(yLabel)
	plt.title(titleTxt)
	plt.tight_layout()  # layout without overlapping
	plt.show()
	return h


def plotStrainFreeLatticeSpacing(data, showErr=True):
	hklList = data['hklList']  # perhaps used to plot as text at each data point
	tauMean = data['tauMean']
	aStarVals = data['dStar100']
	if showErr:
		aStarErrVals = data['dStar100Err']
		# pg.plotErrData(aStarVals, aStarErrVals, tauMean, 'ro-', 'on', 'Information depths in um',
		# 	'a* in nm', 'k')
		plotErrData(aStarVals, aStarErrVals, tauMean, 'ro-', 'on', 'Information depths in um',
			'a* in nm')
	else:
		plotData(aStarVals, tauMean, 'ro-', 'on', 'Information depths in um', 'a* in nm')


def plotStresses(data, showErr=True):
	hklList = data['hklList']
	tauMean = data['tauMean']
	stresses = data['stresses'] if 'stresses' in data else None
	accuracy = data['accuracy'] if 'accuracy' in data else None
	stressNames = ['s11-s33', 's22-s33', 's13', 's23', 's12', 's33']
	if stresses is not None and accuracy is not None:
		for i in range(stresses.shape[1]):
			curStresses = np.round(stresses[:, i])
			if sum(curStresses) != 0 or max(curStresses) != 0 or min(curStresses) != 0:
				if showErr:
					# pg.plotErrData(curStresses, np.round(accuracy[:, i]), tauMean, 'ro-', 'on', 'Information depths in um',
					# 	'Residual stresses in MPa', 'Residual stresses ' + stressNames[i], 'k')
					plotErrData(curStresses, np.round(accuracy[:, i]), tauMean, 'ro-', 'on',
						'Information depths in um', 'Residual stresses in MPa',
						'Residual stresses ' + stressNames[i])
				else:
					plotData(curStresses, tauMean, 'ro-', 'on', 'Information depths in um',
						'Residual stresses in MPa', 'Residual stresses ' + stressNames[i])
	else:
		for stressName in stressNames:
			stressVals = data[stressName] if stressName in data else None
			accuracyVals = data['dev_' + stressName] if ('dev_' + stressName) in data else None
			if stressVals is not None and accuracyVals is not None:
				if sum(stressVals) != 0 or max(stressVals) != 0 or min(stressVals) != 0:
					if showErr:
						# pg.plotErrData(np.round(stressVals), np.round(accuracyVals), tauMean, 'ro-', 'on', 'Information depths in um',
						# 	'Residual stresses in MPa', 'Residual stresses ' + stressName, 'k')
						plotErrData(np.round(stressVals), np.round(accuracyVals), tauMean,
							'ro-', 'on', 'Information depths in um', 'Residual stresses in MPa',
							'Residual stresses ' + stressName)
					else:
						plotData(np.round(stressVals), tauMean, 'rp-', 'on', 'Information depths in um',
							'Residual stresses in MPa', 'Residual stresses ' + stressName)


def plotUniversalPlot(data, showErr=True):
	symbols = ['s', '^', 'p', 'd', 'v', 'o', '+', 'x', '*', 'h', '<', '>', '.']
	colors = ['r', 'g', 'b', 'c', 'm', 'y', 'r', 'g', 'b', 'c', 'm']
	# extract relevant data
	tauVals = data['tauVals']
	psiVals = data['psiVals']
	stresses = data['stresses']
	accuracy = data['accuracy']
	stressNames = ['s11-s33', 's22-s33', 's13', 's23']
	if stresses is not None and accuracy is not None:
		for i in range(stresses.shape[1]):
			curStresses = np.round(stresses[:, i])
			if sum(curStresses) != 0 or max(curStresses) != 0 or min(curStresses) != 0:
				if showErr:
					# pg.plotErrData(curStresses, np.round(accuracy[:, i]), tauVals, 'rp', 'on', 'Information depths in um',
					# 	'Residual stresses in MPa', 'Residual stresses ' + stressNames[i], 'k')
					plotErrData(curStresses, np.round(accuracy[:, i]), tauVals, 'rp', 'on', 'Information depths in um',
						'Residual stresses in MPa', 'Residual stresses ' + stressNames[i])
				else:
					plotData(curStresses, tauVals, 'rp', 'on', 'Information depths in um',
						'Residual stresses in MPa', 'Residual stresses ' + stressNames[i])
	else:
		for stressName in stressNames:
			stressVals = data[stressName]
			accuracyVals = data['dev_' + stressName]
			if stressVals is not None and accuracyVals is not None:
				if sum(stressVals) != 0 or max(stressVals) != 0 or min(stressVals) != 0:
					if showErr:
						# pg.plotErrData(np.round(stressVals), np.round(accuracyVals), tauVals, 'rp', 'on', 'Information depths in um',
						# 	'Residual stresses in MPa', 'Residual stresses ' + stressName, 'k')
						plotErrData(np.round(stressVals), np.round(accuracyVals), tauVals, 'rp', 'on',
							'Information depths in um', 'Residual stresses in MPa',
							'Residual stresses ' + stressName)
					else:
						plotData(np.round(stressVals), tauVals, 'rp', 'on', 'Information depths in um',
							'Residual stresses in MPa', 'Residual stresses ' + stressName)
import mkidcalculator as mc
import numpy as np
import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.signal import find_peaks, peak_widths

import pulseanalysis.data as mkid

# expected energy peaks in eV
e_high = 6490
e_low = 5900
e_cutoff = 6250
e_peaks = np.array([e_low, e_high])

#loop = mc.Loop.from_pickle(directory + "/analysis/loop_combined.p")
#traces = loop.pulses[0].p_trace

def benchmarkEnergies(traces=None):
	
	if not isinstance(traces, (np.ndarray)):
		print("benchmarkEnergies(): No traces given, getting default traces...")
		traces = mkid.loadTraces()
	
	# calculate pulse energies here
	values = np.sum((traces - np.median(traces, axis=1, keepdims=True)), axis=1)

	return distToEV(values)

def getDoublePeak_fe55(data, drawPlot=False):
	cutoff = getCutoffs(data, 2)
	print(cutoff)

	doublepeak = data[data<cutoff]

	if drawPlot:
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.hist(doublepeak, bins='auto')
		ax.set_xlabel("Energy [eV]")
		ax.set_ylabel("Counts")
		ax.set_title("Fe55 5.9 keV Double Peak")
		plt.show()
	
	return doublepeak


def resolveDoublePeak(data=None, peak1=5888, peak2=5899, A=0.5, B=0.5, bw=None, samples=1000):
	
	if data is None:
		data = getDoublePeak_fe55(benchmarkEnergies())

	x = np.linspace(np.amin(data), np.amax(data), samples)
	_, gx = getFWHM(data, bw=bw, samples=samples)
	
	if True:
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.hist(data, bins='auto', density=True)
		ax.plot(x, gx)
		plt.show()

	## STUB
	raise NotImplementedError

	return False

def distToEV(values, peaks=e_peaks, drawPlot=False):
	value_space  = np.linspace(np.amin(values), np.amax(values), 1000)
	kernel = stats.gaussian_kde(values)
	values_dist = kernel(value_space)
	peak_indices, properties = find_peaks(values_dist, prominence=0, height=0)
	heights = properties["peak_heights"]

	# conversions from value space to energy space
	e_scale = np.abs((e_peaks[1] - e_peaks[0])/(value_space[peak_indices[0]] - value_space[peak_indices[1]]))
	
	
	if heights[0] > heights[1]:
		e_first = e_peaks[0] - (value_space[peak_indices[0]] * e_scale)
	else:
		e_scale = -e_scale
		e_first = e_peaks[1] - (value_space[peak_indices[0]] * e_scale)

	energies = values*e_scale + e_first

	if drawPlot:
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.hist(energies, bins='auto')
		ax.set_xlabel("Energy [eV]")
		ax.set_ylabel("Counts")
		ax.set_title("Distribution of Energies")
		plt.show()

	return energies

def testBW(data, desc=""):
	
	scale = 1

	x = np.linspace(np.amin(data), np.amax(data), 1000)
	kernel = stats.gaussian_kde(data)
	bw_scott = kernel.factor
	print("Scott BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))	

	dist1 = scale*kernel(x)
	
	kernel.set_bandwidth(bw_method='silverman')
	bw_silverman = kernel.factor	
	print("Silverman BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))	
	dist2 = scale*kernel(x)

	kernel.set_bandwidth(bw_method=.05)
	print("Const BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))	
	dist3 = scale*kernel(x)

	kernel.set_bandwidth(bw_method=.1)
	print("Const BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))
	dist4 = scale*kernel(x)

	kernel.set_bandwidth(bw_method=.15)
	print("Const BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))
	dist5 = scale*kernel(x)

	kernel.set_bandwidth(bw_method=.3)
	print("Const BW: {} Peaks: {}".format(kernel.factor, find_peaks(kernel(x))[0].size))
	dist6 = scale*kernel(x)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.hist(data, bins='auto', density=True)
	ax.plot(x, dist1, label='Scott (default) {:.4f}'.format(bw_scott))
	ax.plot(x, dist2, label='Silverman {:.4f}'.format(bw_silverman))
	ax.plot(x, dist3, label='Const .05', linestyle='dashed', linewidth=2)
	ax.plot(x, dist4, label='Const .10', linestyle='dashed', linewidth=2)
	ax.plot(x, dist5, label='Const .15', linestyle='dashed', linewidth=2)
	ax.plot(x, dist6, label='Const .30', linestyle='dashed', linewidth=2)
	ax.legend()
	
	title = "BW Comparison"
	if not desc == "":
		title = title + ": " + desc
	
	ax.set_title(title)
	
	plt.show()
	
def getFWHM(data, npeaks=None, bw=None, samples=1000, desc="", xlabel="", drawPlot=False):
	'''
	Takes in distribution data, number of samples used to resolve the fit, and
	drawPlot. Outputs array containing fwhm for each peak and the kde distribution
	containing "samples" number of data points.
	'''

	# find peaks in data
	x = np.linspace(np.amin(data), np.amax(data), samples)
	kernel = stats.gaussian_kde(data)

	if bw is not None:
		kernel.set_bandwidth(bw_method=bw)

	bw = kernel.factor

	dist = kernel(x)
	peak_indices, properties = find_peaks(dist, prominence=0, height=0)
	npeaks = peak_indices.size	
	
	#TODO: Set npeaks using npeaks input parameter

	# calculate half-max height as percentage relative to prominence for each peak
	prominences = properties["prominences"]
	heights = properties["peak_heights"]
	halfmax_adj = 1-(((0.5*heights)-(heights-prominences))/prominences)

	# conversion from samples to eV
	slope = np.abs(x[1] - x[0])

	# create array to fill with fwhm data
	#wshape = np.vstack(peak_widths(energies_dist, peak_indices, rel_height=halfmax_adj[0])).shape
	widths = np.zeros(shape = (4, npeaks))

	# compute fwhm
	for i in range(npeaks):
		widths[:,i] = np.vstack(peak_widths(dist, np.array([peak_indices[i]]), rel_height=halfmax_adj[0]))[:,0]
	
	# compute variance
	fwhm = slope*widths[0]
	
	if drawPlot:
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.hist(data, bins='auto', density=True)
		ax.plot(x, dist, label="BW: {:.4f}".format(bw))
		ax.plot(x[peak_indices], dist[peak_indices], "x")
		ax.hlines(widths[1], widths[2]*slope+x[0], widths[3]*slope+x[0], color="C2")
		title = "KDE"
		if not desc == "":
			title = title + ": " + desc
		if not xlabel == "":
			ax.set_xlabel(xlabel)
		plt.show()

	return fwhm, dist

def getCutoffs(data, npeaks, samples=1000):

	# find minima
	x = np.linspace(np.amin(data), np.amax(data), samples)
	kernel = stats.gaussian_kde(data)
	dist = kernel(x)
	cutoff_indices, cutoff_properties = find_peaks(-dist, prominence=0)
	
	# get most prominent minima
	k = npeaks-1
	cutoff_prominences = cutoff_properties["prominences"]
	idx = np.argsort(cutoff_prominences)[-k:]
	cutoff_indices_filtered = np.sort(np.take(cutoff_indices, idx))

	# points at which we will split the data
	cutoffs = x[cutoff_indices_filtered]
	cutoffs = np.sort(cutoffs)
	
	return cutoffs
	
def getFWHM_separatePeaks(data, npeaks=None, bw_list=None, samples=1000, desc="", xlabel="",  drawPlot=True):
	
	x = np.linspace(np.amin(data), np.amax(data), samples)
	kernel = stats.gaussian_kde(data)
	dist = kernel(x)

	peak_indices, peak_properties = find_peaks(dist, height=0)
	npeaks_total = peak_indices.size
	
	# ensure npeaks is valid
	if npeaks is None:
		npeaks = npeaks_total
	elif not isinstance(npeaks, int):
		raise ValueError("Number of peaks must be an integer value.")
	elif not npeaks > 0:
		raise ValueError("Number of peaks  must be greater than 0.")
	elif (npeaks > npeaks_total):
		print("Can only find {0} peaks in the data. Assuming {0} peaks instead of {1}.".format(npeaks_total, npeaks))
		npeaks = npeaks_total

	if bw_list is not None:
		if not (len(bw_list) == npeaks):
			raise ValueError("Bandwidth list must match number of peaks.")

	else:
		bw_list = []
		for i in range(npeaks):
			bw_list.append(None)

	# get npeaks greatest peak heights
	peak_heights = peak_properties["peak_heights"]
	idx = np.argsort(peak_heights)[-npeaks:]
	peak_indices_filtered = np.sort(np.take(peak_indices, idx))
	peak_heights_filtered = dist[peak_indices_filtered]
	rel_peak_heights = peak_heights_filtered/np.sum(peak_heights_filtered)	

	# get most prominent minimums
	cutoffs = getCutoffs(data, npeaks, samples)	
	cutoffs = np.append(cutoffs, [np.amin(data)-1, np.amax(data)+1])
	cutoffs = np.sort(cutoffs)
	# split the data into peaks
	data_split = []
	fwhm_list = []
	dist_list = []

	for i in range(cutoffs.size - 1):
		data_split.append(data[(data>cutoffs[i]) & (data<=cutoffs[i+1])])
		fwhm, dist = getFWHM(data_split[i], bw=bw_list[i], samples=samples, drawPlot=False)
		fwhm_list.append(fwhm)
		dist_list.append(dist)

	if drawPlot:
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.hist(data, bins='auto', density=True)
		for i, (sdata, dist, height) in enumerate(zip(data_split, dist_list, rel_peak_heights)):
			x = np.linspace(np.amin(sdata), np.amax(sdata), samples)
			if bw_list[i] is None:
				bw_str = "Default"
			else:
				bw_str = str(bw_list[i])
			ax.plot(x, dist*height, label="BW: " + bw_str)
			
			if not xlabel=="":
				ax.set_xlabel(xlabel)
			
			title = "Split KDE"
			if not desc=="":
				title = title + ": " + desc
			
			ax.set_title(title)

			ax.legend(loc='upper right')
		plt.show()

	return np.array(fwhm_list)

def compareDist(data1, data2, nbin=300, drawPlot='True'):
	fwhm1 = getFWHM(data1)
	fwhm2 = getFWHM(data2)	
	
	print("Data1:")
	print("Estimated FWHM of Peak #1: {:.4f} Units".format(fwhm1[0]))
	print("Estimated FWHM of Peak #2: {:.4f} Units".format(fwhm1[1]))
	print("\nData2:")
	print("Estimated FWHM of Peak #1: {:.4f} Units".format(fwhm2[0]))
	print("Estimated FWHM of Peak #2: {:.4f} Units".format(fwhm2[1]))

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.hist(data1, nbin, alpha=0.5, label="FWHMs: [{:.4f}, {:.4f}]".format(*fwhm1))
	ax.hist(data2, nbin, alpha=0.5, label="FWHMs: [{:.4f}, {:.4f}]".format(*fwhm2))
	ax.legend(loc='upper right')
	
	plt.show()
	


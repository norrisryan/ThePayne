# #!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import numpy as np
import h5py
from scipy import constants
speedoflight = constants.c / 1000.0
from scipy.interpolate import UnivariateSpline,NearestNDInterpolator

from ..predict.predictspec import PayneSpecPredict
from ..utils.pullspectra import pullspectra

class TestSpec(object):
	"""
	Class for testing a Payne-learned NN using a testing dataset 
	different from training spectra
	"""
	def __init__(self, NNfilename):
		# user inputed neural-net output file
		self.NNfilename = NNfilename

		# initialize the Payne Predictor
		self.PP = PayneSpecPredict(self.NNfilename)

		# define wavelength range of trained network
		self.waverange = [self.PP.NN['wavelength'].min(),self.PP.NN['wavelength'].max()]


	def runtest(self,**kwargs):
		'''
		Function to run the testing on an already trained network
		'''
		if 'testnum' in kwargs:
			testnum = kwargs['testnum']
		else:
			# test with equal number of spectra as training
			testnum = len(self.PP.NN['labels'].T)

		if 'resolution' in kwargs:
			resolution = kwargs['resolution']
		else:
			# default resolution is the native resolution of NN
			resolution = self.PP.NN['resolution']

		# pull training spectra
		self.pullspectra = pullspectra()

		self.spectra_train,self.labels_train,self.wavelength_train = self.pullspectra.selspectra(
			self.PP.NN['labels'].T,
			resolution=resolution,
			waverange=self.waverange)

		# pull testing spectra
		self.spectra_test,self.labels_test,self.wavelength_test = self.pullspectra(
			testnum,
			resolution=resolution,
			waverange=self.waverange,
			excludelabels=self.PP.NN['labels'],
			Teff=[10.0**self.PP.NN['x_min'][0],10.0**self.PP.NN['x_max'][0]],
			logg=[self.PP.NN['x_min'][1],self.PP.NN['x_max'][1]],
			FeH= [self.PP.NN['x_min'][2],self.PP.NN['x_max'][2]],
			aFe= [self.PP.NN['x_min'][3],self.PP.NN['x_max'][3]],
			)

		# generate predicted spectra at each of the testing spectra labels
		outspecdict = {}
		outspecdict['WAVE'] = self.wavelength_test
		outspecdict['TRAINLABLES'] = self.labels_train
		outspecdict['TESTLABELS'] = self.labels_test
		outspecdict['trainspec'] = {}
		outspecdict['testspec'] = {}

		for ii,pars,trainspec in zip(range(len(self.labels_train)),self.labels_train,self.spectra_train):
			modwave_i,modflux_i = self.PP.getspec(
				logt=pars[0],logg=pars[1],feh=pars[2],afe=pars[3])
			outspecdict['trainspec'][ii] = {'train':trainspec,'predict':modflux_i}

		for ii,pars,testspec in zip(range(len(self.labels_test)),self.labels_test,self.spectra_test):
			modwave_i,modflux_i = self.PP.getspec(
				logt=pars[0],logg=pars[1],feh=pars[2],afe=pars[3])
			outspecdict['testspec'][ii] = {'test':testspec,'predict':modflux_i}

		outspecdict['medarr_test'] = np.ones(len(outspecdict['WAVE']))
		outspecdict['medarr_train'] = np.ones(len(outspecdict['WAVE']))

		for ii in range(len(outspecdict['medarr_test'])):
			outspecdict['medarr_test'][ii] = np.median(
				[np.abs(outspecdict['testspec'][x]['test'][ii]-
					outspecdict['testspec'][x]['predict'][ii]) 
				for x in outspecdict['testspec']])

			outspecdict['medarr_train'][ii] = np.median(
				[np.abs(outspecdict['trainspec'][x]['train'][ii]-
					outspecdict['trainspec'][x]['predict'][ii]) 
				for x in outspecdict['trainspec']])

		return outspecdict
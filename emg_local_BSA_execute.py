# Runs a local BSA analysis (see emg_local_BSA.py) on one trial of EMG data. Runs on the HPC

# Import stuff
import numpy as np
import easygui
import os

# Read blech.dir, and cd to that directory. 
f = open('blech.dir', 'r')
dir_name = []
for line in f.readlines():
	dir_name.append(line)
f.close()
os.chdir(dir_name[0][:-1])

# Read the data files
env = np.load('env.npy')
sig_trials = np.load('sig_trials.npy')

# cd to emg_BSA_results
os.chdir('emg_BSA_results')

# Get SGE_TASK_ID # - this will determine the taste+trial to be looked at
task = int(os.getenv('SGE_TASK_ID'))
taste = (task-1)/sig_trials.shape[-1]
trial = (task-1)%sig_trials.shape[-1]

# Import R related stuff - use rpy2 for Python->R and pandas for R->Python
import readline # Needed for the next line to work on Anaconda
import rpy2.robjects as ro
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()
from rpy2.robjects.packages import importr
import pandas.rpy.common as com

# Fire up BaSAR on R
basar = importr('BaSAR')

# Make the time array and assign it to t on R
T = (np.arange(7000) + 1)/1000.0
t_r = ro.r.matrix(T, nrow = 1, ncol = 7000)
ro.r.assign('t_r', t_r)
ro.r('t = c(t_r)')

# Make arrays to store the posterior probabilities and frequencies of analysis
p = np.zeros((7000, 20))
omega = np.zeros(20)

# Run BSA on trial 'trial' of taste 'taste' and assign the results to p and omega.
Br = ro.r.matrix(env[taste, trial, :], nrow = 1, ncol = 7000)
ro.r.assign('B', Br)
ro.r('x = c(B[1,])')
ro.r('r_local = BaSAR.local(x, 0.1, 1, 20, t, 0, 300)') # x is the data, we scan periods from 0.1s (10 Hz) to 1s (1 Hz) in 20 steps. Window size is 300ms. There are no background functions (=0)
p_r = com.load_data('r_local')
r_p = np.array(p_r['p'])
p[:, :] = r_p[:, :]
omega = np.array(p_r['omega'])/(2.0*np.pi) 

# Save p and omega by taste and trial number
np.save('taste%i_trial%i_p.npy' % (taste, trial), p)
np.save('taste%i_trial%i_omega.npy' % (taste, trial), omega)




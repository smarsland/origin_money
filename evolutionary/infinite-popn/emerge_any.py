from helper_funcs_any import *
import numpy as np
import numpy.random as rng
from pytest import approx
import pylab as pl
import sys, pickle
import matplotlib.cm as cm
np.set_printoptions(precision=2)
#rng.seed(0)
import argparse

VERBOSE = False

parser = argparse.ArgumentParser()
parser.add_argument('-n','--nsl', metavar='NUM', action="store", type=int, default=5, help='number of signal levels')
#parser.add_argument('-d','--donoronly', action="store_true", help='include if only want search among the signal dynamics that do NOT change the RECVR')
parser.add_argument('-i','--itns', metavar='NUM', action="store", type=int, default=25, help='the number of iterations of interaction, per generation')
parser.add_argument('-b','--BETA', metavar='FLOAT', action='store', type=float, default=0.5, help='probability agent able to help, ie. Pr(h>0)')
parser.add_argument('-t','--tag', metavar='STR', action="store", type=str, default=None, help='optional tag string: will write a file of results, with this name')
parser.add_argument('-g','--ignores',  action="store_true", help='set this if you want to search handshakes that ignore S')
args = parser.parse_args()
#=====================================================
# Order of indices will always be (h,s) unless obviously otherwise.
if args.tag:
    outfile = args.tag+'.txt'
    fp = open(outfile,'w')
    print('Writing results to ',outfile)
else:
    fp = sys.stdout



# set an initial distribution of Signals
w_init = np.zeros(args.nsl,dtype=float)
# ---------------------------------------------------------------
## Options, options. Pick just one:
#w_init = rng.rand(args.nsl)  ## OR...
w_init[:2]=1.0               ## OR...
#w_init = (0.5**np.arange(args.nsl))#.reshape(args.nsl,1) # each is half the one below
## OR...
#w_init = np.ones(args.nsl,dtype=float)  ## OR...
#k=1
#w_init[0], w_init[k] = .5, .5 # Give everyone either nil or k dollars!... 
# IF cash/agent=$1 exactly, strategy=Trader scores should settle into halvings...
# To try this, set w_init[0] and w_init[2] to .5, and all others zero.
# ---------------------------------------------------------------
w_init = w_init / w_init.sum() # ie. normalised so it's a distribution

IGNORE_S = args.ignores
# This is just a verbose way to compile a list of all sensible strategies!! 
# (ie. all proposals)
all_strats = []
all3, just2 = [-1,0,1],  [0,1]
count=0
for dh01 in just2:  # note h can't go down from zero so -1 is left out.
    for dh11 in all3:
        for dsSelf01 in all3:
            for dsSelf11 in all3:
                for dsOther01 in all3: 
                    for dsOther11 in all3: 
                    
                        if IGNORE_S is False:
                            for dh00 in just2: # ditto h can't go down.
                                for dh10 in all3:
                                    for dsSelf00 in just2: # ditto - s can't go down from zero, so leave out the -1 option.
                                        for dsSelf10 in all3:
                                            for dsOther00 in just2: # ditto - s can't go down.
                                                for dsOther10 in all3:
                                    
                                                    dhPropose = np.array([[dh00,dh01],[dh10,dh11]])
                                                    dsSelfPropose = np.array([[dsSelf00,dsSelf01],[dsSelf10,dsSelf11]])
                                                    dsOtherPropose = np.array([[dsOther00,dsOther01],[dsOther10,dsOther11]])
                                                    all_strats.append( Strategy(count, dhPropose, dsSelfPropose, dsOtherPropose) )
                                                    count += 1
                                    """
                                    # Or don't! THIS (below) SHOULD GIVE IDENTICAL RESULT TO EMERGE.PY 
                                    # because Self ALWAYS matches OTHER in find_agreed_changes()
                                    dhPropose = np.array([[dh00,dh01],[dh10,dh11]])
                                    dsSelfPropose = np.array([[dsSelf00,dsSelf01],[dsSelf10,dsSelf11]])
                                    dsOtherPropose = -1 * np.copy(dsSelfPropose)
                                    all_strats.append( Strategy(count, dhPropose, dsSelfPropose, dsOtherPropose) )
                                    count += 1
                                    """
                        else:  # ie. if IGNORE_S is True, so we can avoid those loops.
                            dh00 = dh01
                            dh10 = dh11
                            dsSelf00 = dsSelf01
                            dsSelf10 = dsSelf11
                            dsOther00 = dsOther01
                            dsOther10 = dsOther11
                                    
                            dhPropose = np.array([[dh00,dh01],[dh10,dh11]])
                            dsSelfPropose = np.array([[dsSelf00,dsSelf01],[dsSelf10,dsSelf11]])
                            dsOtherPropose = np.array([[dsOther00,dsOther01],[dsOther10,dsOther11]])
                            all_strats.append( Strategy(count, dhPropose, dsSelfPropose, dsOtherPropose) )
                            count += 1

countHelp = 0
countESS = 0
THRESHOLD = 0.05
# Low: strategies that achieve even less self-help than this just aren't interesting.

B, C = 5, 1 # costs and benefits
fp.write('considering {0} possible strategies \n'.format(len(all_strats)))

"""
Thought: there are too many. We only care about the uninvadeable ones.
The most likely invader is probably UpDown..? Or some defector that still accepts
donations.
We should put those two possibilities first in the queue to be tested.
And then it should be a WHILE loop, jumping out at the first failure, not continuing on!!
"""

import copy
stratsCopy = copy.copy(all_strats)

ESSs = {}
tried = 0
for commonStrat in all_strats:
    tried += 1
    print('\r  Tried {0}'.format(tried),end='')
    helpingRate_common, helpedRate_common, w_common, w_seq_common = run_strategy(commonStrat, w_init, args, VERBOSE)   
    fitness_common = B * helpedRate_common - C * helpingRate_common
    
    if helpedRate_common > THRESHOLD:
        countHelp += 1
        print('.  Found {0}-th one that self-helps: testing for ESS...'.format(countHelp))
        # it would be good to say whether this is 
        # invadeable by a rare alternative
        # Q1: what's the payoff currently for a strat player?
        # A1: I guess it's the (b-c)*helpRate
        # Q2: what's the payoff to a given rare alt?
        # A2: ... we figure out how often it will help a strat
        uninvadeable = True
        diff = -999.0
        j=0
        swapHere = 0
        while j<len(all_strats) and uninvadeable:
            rareStrat = stratsCopy[j]
            print('j: {0}\r'.format(j),end='')
            if rareStrat.name != commonStrat.name:
            
                ### Here's where the action happens ####################
                helpingRate_rare, helpedRate_rare, w_rare, w_seq_rare = run_rare_strategy_amongst_common(rareStrat, commonStrat, w_common, args)
                ########################################################
                
                fitness_rare = B * helpedRate_rare - C * helpingRate_rare
                if fitness_rare >= fitness_common:
                    uninvadeable = False
                    # move whoever beat this strategy to near the start of stratsCopy list,
                    # so it'll be found quickly by later tests too.
                    tmp = copy.copy(rareStrat)
                    stratsCopy[j] = copy.copy(stratsCopy[swapHere])
                    stratsCopy[swapHere] = tmp
                    swapHere += 1
            j += 1
            
        if uninvadeable:
            countESS += 1 
            fp.write('***YES:\t{0} self-helps {1:.3f} fitness {2:.3f}\n'.format(commonStrat.name, helpedRate_common, fitness_common))
#            print('{0} self-helps {1:.3f} fitness {2:.3f}\n'.format(commonStrat.name, helpedRate_common, fitness_common))
            ESSs[commonStrat.name] = [helpingRate_common, fitness_common]
        else: 
            fp.write('  nope, {0} helps {1:.3f} but loses to (eg) {2} ({3})\n'.format(commonStrat,helpingRate_common,j-1,rareStrat))
fp.write('\nOut of {0} proposals, {1} had self-help rate at least {2}, {3} was/were ESS.\n'.format(len(all_strats),countHelp,THRESHOLD, countESS))
fp.write('\n Here are the ESS strategies:\n\n')
for strat in ESSs.keys():
    fp.write('{0} \t self-helps at rate {1:.3f} \t fitness {2:.3f}\n'.format(strat, ESSs[strat][0], ESSs[strat][1]))
    
fp.close()


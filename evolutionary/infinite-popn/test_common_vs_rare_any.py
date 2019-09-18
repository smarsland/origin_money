from helper_funcs_any import *
import numpy as np
import numpy.random as rng
from pytest import approx
import pylab as pl
import sys, pickle
import matplotlib.cm as cm
np.set_printoptions(precision=3)
import argparse

VERBOSE = False
parser = argparse.ArgumentParser()
parser.add_argument('-n','--nsl', metavar='NUM', action="store", type=int, default=5, help='number of signal levels')
parser.add_argument('-i','--itns', metavar='NUM', action="store", type=int, default=25, help='the number of iterations of interaction, per generation')
parser.add_argument('-b','--BETA', metavar='FLOAT', action='store', type=float, default=0.5, help='probability agent able to help, ie. Pr(h>0)')
parser.add_argument('-t','--tag', metavar='STR', action="store", type=str, default='', help='optional tag string')
args = parser.parse_args()

# set an initial distribution of Signals
w_init = np.zeros(args.nsl,dtype=float)
# ---------------------------------------------------------------
## Options, options. Pick just one:
#w_init = rng.rand(args.nsl)  ## OR...
#w_init[:2]=1.0               ## OR...
#w_init = np.zeros(args.nsl,dtype=float)
k=1
w_init[0], w_init[k] = .5, .5 # Give everyone either nil or k dollars!... 
#w_init = (0.5**np.arange(args.nsl))#.reshape(args.nsl,1) # each is half the one below
w_init = w_init / w_init.sum() # ie. normalised so it's a distribution
# ---------------------------------------------------------------
B, C = 5, 1 # costs and benefits


# [  0  1 -1 -1][  1 -1  1  1][  1  1 -1 -1] 
# [  0  1 -1  0][  1 -1  1  1][  1  1 -1  1] 
#############  HERE IS WHERE WE ACTUALLY SPECIFY THE TWO STRATEGIES ###########
#dhPropose, dsPropose = np.array([[1,1],[0,-1]]), np.array([[1,1],[0,-1]])
# NOW the order is always going to be h,s_self,s_other
#dhPropose, dsSelfPropose, dsOtherPropose = np.array([[1,1],[1,1]]), np.array([[1,1],[1,1]]), np.array([[-1,-1],[-1,-1]])
dh00, dsSelf00, dsOther00 =  0, 1, 1
dh01, dsSelf01, dsOther01 =  1,-1, 1
dh10, dsSelf10, dsOther10 = -1, 1,-1
dh11, dsSelf11, dsOther11 = -1, 1,-1
dhPropose = np.array([[dh00,dh01],[dh10,dh11]])
dsSelfPropose = np.array([[dsSelf00,dsSelf01],[dsSelf10,dsSelf11]])
dsOtherPropose = np.array([[dsOther00,dsOther01],[dsOther10,dsOther11]])
#dhPropose, dsSelfPropose, dsOtherPropose = np.array([[0,1],[-1,-1]]), np.array([[1,-1],[1,1]]), np.array([[1,1],[-1,-1]])
commonStrat = Strategy(0, dhPropose, dsSelfPropose, dsOtherPropose)

dhPropose, dsSelfPropose, dsOtherPropose = np.array([[0,1],[-1,-1]]), np.array([[0,-1],[1,1]]), np.array([[0,1],[-1,-1]])
rareStrat = Strategy(0, dhPropose, dsSelfPropose, dsOtherPropose)
###############################################################################
# maybe swap them around and try that too, like this:
#commonStrat, rareStrat = rareStrat, commonStrat

helpingRate_common, helpedRate_common, w_common, w_seq_common = run_strategy(commonStrat, w_init, args, VERBOSE)
print("help given to common individuals: ",helpedRate_common)
print("distribution of score in common: ",w_common)
fitness_common = B * helpedRate_common - C * helpingRate_common
print('fitness of common: {0:.3f}'.format(fitness_common))
print()

helpingRate_rare, helpedRate_rare, w_rare, w_seq_rare = run_rare_strategy_amongst_common(rareStrat, commonStrat, w_common, args)
print("help given to rareStrat individuals when rare amongst common: ",helpedRate_rare)
print("distribution of score in rareStrat individuals: ",w_rare)
fitness_rare = B * helpedRate_rare - C * helpingRate_rare
print('fitness of rare: {0:.3f}'.format(fitness_rare))


# how about an informative picture?
fig = pl.figure("visualisation",figsize=(8., 8.), dpi=200) #, font(20, "Courier"))
axLeft  = pl.subplot2grid((2,2), (0, 0))  # the common strategy.
axRight = pl.subplot2grid((2,2), (0, 1), sharex=axLeft) #, sharey=axLeft) # the rare strategy.
axLeft.axis('equal')
proposalword = {-1:'donate',0:'no',1:'request'}
altproposalword = {-1:r'$\downarrow$',0:'no',1:r'$\uparrow$'}
wordalpha = {-1:1.,0:.1,1:1.}
ha, va = {0:'left',1:'right'}, {0:'bottom',1:'top'}
ypos = [.2,1]
axes = [axLeft,axRight]
strats = [commonStrat, rareStrat]
popularityword = ['Common','Rare']
alpha = .75
for i in range(2):
    axes[i].axis([0,1,0,1])
    axes[i].plot([.5,.5],[0,1],':k',[0,1],[.5,.5],':k')
    axes[i].plot([0,0,1,1],[0,1,0,1],'.k',alpha=0.)
    for h in [0,1]:
        for s in [0,1]:
            axes[i].text(h,ypos[s],proposalword[strats[i].dh_prop[h,s]]+' help', color='green', 
                ha=ha[h], va=va[s],alpha=wordalpha[strats[i].dh_prop[h,s]])
            axes[i].text(h,ypos[s]-.1,altproposalword[strats[i].dsSelf_prop[h,s]]+' Self score', 
                color='blue', ha=ha[h], va=va[s],alpha=wordalpha[strats[i].dsSelf_prop[h,s]])
            axes[i].text(h,ypos[s]-.2,altproposalword[strats[i].dsOther_prop[h,s]]+' Other score', 
                color='blue', ha=ha[h], va=va[s],alpha=wordalpha[strats[i].dsOther_prop[h,s]])
    axes[i].set_xticks([0,1])
    axes[i].set_xticklabels(['no','yes'],color='green',alpha=alpha) 
    axes[i].set_yticks([0,1])
    axes[i].set_yticklabels(['no','yes'],color='blue',alpha=alpha)
    if i==1: axes[i].set_yticklabels(['no','yes'],color='blue',alpha=0)
    axes[i].set_xlabel('ability to help',color='green',alpha=alpha)
    if i == 0: axes[i].set_ylabel(r'score $\geq 1$',color='blue',alpha=alpha)
    axes[i].set_ylim([-.2,1.2])
    axes[i].set_title('{0}:{1}'.format(popularityword[i],strats[i].name))


axLowLeft  = pl.subplot2grid((2,2), (1, 0))  # the common strategy.
axLowLeft.imshow(np.array(w_seq_common).T,origin='lower',cmap='Blues')
print('common scores start  is {0}, mean {1:.3f}'.format(w_seq_common[0],np.dot(w_seq_common[0],range(args.nsl))))
print('common scores at end is {0}, mean {1:.3f}'.format(w_seq_common[-1],np.dot(w_seq_common[-1],range(args.nsl))))
axLowLeft.text(0,args.nsl+0.0,'helped fraction = {0:.3f}'.format(helpedRate_common))
axLowLeft.text(0,args.nsl+1.,'helping fraction= {0:.3f}'.format(helpingRate_common))
axLowLeft.text(0,args.nsl+2.0,'(final) fitness = {0:.3f}'.format(fitness_common))
axLowLeft.text(-2,0,'score',ha='right',va='bottom',rotation=90)
for i in range(args.nsl):
    axLowLeft.text(-1,i-.2,i,ha='right',va='center')
axLowLeft.text(0,-2,r'# interactions $\longrightarrow$')
for i in range(args.itns+1):
    axLowLeft.text(i,-1,i,ha='center',va='center')
axLowLeft.axis('off')

axLowRight = pl.subplot2grid((2,2), (1, 1), sharex=axLowLeft, sharey=axLowLeft) # the rare strategy.
axLowRight.imshow(np.array(w_seq_rare).T,origin='lower',cmap='Blues')
axLowRight.text(0,args.nsl+0.0,'helped fraction = {0:.3f}'.format(helpedRate_rare))
axLowRight.text(0,args.nsl+0.5,'helping fraction= {0:.3f}'.format(helpingRate_rare))
axLowRight.text(0,args.nsl+1.0,'(final) fitness = {0:.3f}'.format(fitness_rare))
axLowRight.axis('off')



pl.tight_layout()
if args.tag == '':
    outfile = 'Common_{0}_Rare_{1}.png'.format(commonStrat.name,rareStrat.name)
else:
    outfile = '{0}.png'.format(args.tag)
pl.savefig(outfile)
print('Wrote ',outfile)

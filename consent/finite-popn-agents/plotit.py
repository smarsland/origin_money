import numpy as np
import numpy.random as rng
#import pylab as pl
import matplotlib.pyplot as plt # new
import matplotlib.patches as patches
import matplotlib.colors as colors
import seaborn
from matplotlib.font_manager import FontProperties


plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

seaborn.set(style='ticks')
NUMINTROLINES = 3 # from the bespoke format of the .txt data files we are reading.

##########################################################################

import argparse
import copy
np.set_printoptions(precision=3)


IGNORES = True  # set true if the agents were ignoring self s.
# This will give smaller "cards" describing the strategy.

parser = argparse.ArgumentParser()
parser.add_argument('filename',  help='the data filename')
args = parser.parse_args()
from matplotlib import rc
#rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## OR for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)

font0 = FontProperties()
font0.set_size('small')
font0.set_family('sans-serif')
font0.set_weight('bold')


# Lay out the overall figure
fig, ax1 = plt.subplots(
        figsize=(7.,4.),
        dpi=600,
        nrows=2, ncols=1, sharex=True, sharey=False, 
        gridspec_kw={'height_ratios':[2,1]}
        )
axTop, axBottom = ax1[0], ax1[1]


# read in a file of data
gens_data = []
score_data = []
payoff_data = []

print("Reading {0}".format(args.filename))
f = open(args.filename, 'r')
lines = f.readlines()
f.close()
 
# the first few lines are ignored, and the last are the score distribution, 
# preceded by the word "SCORE".
finalScoreCounts = []
for line in lines[NUMINTROLINES:]:
    words = ' '.join(line.split()).split() # splits it up
    if words[0] == 'SCORE': 
        print('SCORE {0} NUM {1}'.format(words[1], words[2]))
        finalScoreCounts.append(int(words[2]))
    else:
        gens_data.append(int(words[0]))
        score_data.append(float(words[1]))
        payoff_data.append(float(words[2]))

payoff_data = np.array(payoff_data)
gens_data = np.array(gens_data)

#SCALE = 1.0 #gens_data[-1] / 10. 
# HACK: scale up payoffs, just so the images look okay!! :(
#print("HORRIBLE SCALE hack is ",SCALE)   ## FFS!! Why need to do this?
#for i,pay in enumerate(payoff_data):
#    payoff_data[i] = pay*SCALE


alpha = 0.85
# do the top plot, of payoffs
axTop.fill_between(gens_data, -0.05, payoff_data, interpolate=True,color='darkred',alpha=0.25)
axTop.plot(gens_data, payoff_data, '-',color='darkred',markersize=3,alpha=alpha)
axTop.set_ylabel('Mean Payoff')
#axTop.set_yticklabels(["","0","1","2"]) # no! that's not where the ticks are!
axTop.set_yticks([0.0,0.2,0.4,0.6,0.8]) # no! that's not where the ticks are!
axTop.axis([0,np.max(gens_data),-0.05,0.8])

#axTop.set(ylim=(0., 1.))
#print(axTop.axis())
#axTop.axis([np.min(gens_data), np.max(gens_data), np.min(payoff_data), np.max(payoff_data)])

# do the bottom plot, of average score levels
axBottom.plot(gens_data, score_data,'o-k',markersize=2,color='k',alpha=1.)
#axBottom.plot(gens_data, score_data, '-',color='lightsteelblue',markersize=1,alpha=alpha)
axBottom.set_ylabel('Mean Score')

# Now put labels on, whenever the lead strategy changes
increment = 0.035 # height increment between successive lines of text
boxwidth = gens_data[-1]/15.
boxheight = 5
hlo,hhi,vlo,vhi = axTop.axis()
dispx, gapx, dispy, gapy = hhi/80,hhi/30,vhi/4,vhi/2

#\definecolor{need}{rgb}{0.25, 0.60, 0.95}
#\definecolor{surplus}{rgb}{0.0, 0.73, 0.84}
bluepill = 'cornflowerblue' #(0.3, 0.4, 0.9)
bluepill_interior = (.8,.8,.8)


#prev_dh, prev_dsSelf, prev_dsOther = None, None, None

#moneycolor = 'teal' #'cornflowerblue'
#colours = ['salmon','goldenrod','y','turquoise','lightsteelblue','saddlebrown','darkmagenta','slateblue','dimgray','indianred','green'] # nb. no blue, as reserved for Money-like
#colourindex=0
prev_offer = 'nothing'

for i,line in enumerate(lines[NUMINTROLINES:]):
    #words = ' '.join(line.split()).split()
    words = line.split()
    if words[0] == 'SCORE': continue  # ie. just skip those lines
    gen= int(words[0])
    pay = float(words[2])
    offer = words[3]
    
    # has there been a change?
    if (i % int(len(gens_data)/5) == 1) and (i>10) and (offer != prev_offer): # and (pay > 0.1):  
        
        print("showing at iteration {0} \t".format(gen), offer)

        axTop.plot([gen,gen+dispx-gapx],[pay+dispy/3,pay+dispy],
            '-',linewidth=2,color=bluepill)
        # blob at the end of that line, near the true point of origin.
        axTop.plot([gen],[pay+dispy/3],
            'o',linewidth=3,color=bluepill,alpha=1.)

        font = FontProperties()
        font.set_family('Helvetica')
        #font.set_style('normal')
        axTop.text(gen+dispx-4*gapx, pay+dispy, 
            offer.replace('|',r'$\,\mid\,$').replace('-',r'$-$').replace('+',r'$+$'),
            bbox=dict(boxstyle="round,pad=0.2,rounding_size=0.85",
                   ec=bluepill,
                   fc=bluepill_interior,
                   lw=2.0
                   ), fontproperties=font)


        prev_offer = offer

# Add an "inset" box to the bottom axes.
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
axinsert = inset_axes(axBottom, width="20%", height="100%",  #loc=8,
                    bbox_to_anchor=(.515, 0.1, .5, .85),
                    bbox_transform=axBottom.transAxes)
axinsert.tick_params(length=.5,labelsize=7)
scorevals = range(len(finalScoreCounts))
axinsert.barh(scorevals, finalScoreCounts, alpha=0.5,fc=bluepill,ec=bluepill)
axinsert.set_yticks(scorevals)#[::2])
axinsert.set_xticks([])
axinsert.tick_params(axis="y",direction="in", pad=-7)
#axinsert.text(-2,max(finalScoreCounts)+4,'score distribution',
#    va='bottom',ha='left',fontsize=10,color='black')
#axinsert.axis('off')
axinsert.set_title('scores')
#axinsert.set_facecolor(bluepill)

axTop.set_xticks([])
seaborn.despine(ax=axTop,bottom=True,offset=-0.1) # the important part here
seaborn.despine(ax=axBottom, offset=0) # the important part here


outfile = args.filename.strip('.txt') + '.png'
plt.savefig(outfile)
print("Wrote {0}".format(outfile))

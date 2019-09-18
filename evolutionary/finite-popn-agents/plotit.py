import numpy as np
import numpy.random as rng
import pylab as pl
import matplotlib.patches as patches
import matplotlib.colors as colors
import seaborn
from matplotlib.font_manager import FontProperties

seaborn.set(style='ticks')

def offer_to_wd(partialOffer):
    chars = list(partialOffer)
    wd = ''
    
    if chars[1]=='-': wd = wd+'$-$'
    elif chars[1]=='0': wd = wd+'$0\;$'
    elif chars[1]=='+': wd = wd+'$\\uparrow\;$'
    
    if chars[0]=='-': wd = wd+'$D\;$'
    elif chars[0]=='0': wd = wd+'$0\;$'
    elif chars[0]=='+': wd = wd+'$R\;$'

    if chars[2]=='-': wd = wd+'$\\downarrow\;$'
    elif chars[2]=='0': wd = wd+'$0\;$'
    elif chars[2]=='+': wd = wd+'$\\uparrow\;$'
    return (wd)                    

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
fig = pl.figure("timeseries visualisation",figsize=(8., 4.), dpi=300)
axTop    = pl.subplot2grid((3,1), (0, 0), rowspan=2)  
axBottom = pl.subplot2grid((3,1), (2, 0))#, sharex=axTop)  

# read in a file of data
gens_data = []
score_data = []
payoff_data = []

print("Reading {0}".format(args.filename))
f = open(args.filename, 'r')
lines = f.readlines()
f.close()

newline = []
# the first two lines are ignored
for line in lines[2:]:
    words = ' '.join(line.split()).split() # splits it up
    newline.append(words)
    gens_data.append(int(words[0]))
    score_data.append(float(words[1]))
    payoff_data.append(float(words[2]))



alpha = 0.85
# do the top plot, of payoffs
axTop.fill_between(gens_data, -0.05, payoff_data, interpolate=True,color='lightsteelblue',alpha=1.)
axTop.plot(gens_data, payoff_data, '-',color='lightsteelblue',markersize=3,alpha=alpha)
axTop.set_ylabel('Mean Payoff')

# do the bottom plot, of average score levels
axBottom.plot(gens_data, score_data,'o-k',markersize=2,color='k',alpha=1.)
#axBottom.plot(gens_data, score_data, '-',color='lightsteelblue',markersize=1,alpha=alpha)
axBottom.set_ylabel('Mean Score')

# Now put labels on, whenever the lead strategy changes
increment = 0.035 # height increment between successive lines of text
boxwidth = gens_data[-1]/15.
boxheight = .09
dispx, dispy = boxwidth/3,boxheight/1.2

#\definecolor{need}{rgb}{0.25, 0.60, 0.95}
#\definecolor{surplus}{rgb}{0.0, 0.73, 0.84}
ccc = {0:[0.25, 0.60, 0.95],1:[0.0, 0.73, 0.84]}


prev_dh, prev_dsSelf, prev_dsOther = None, None, None
moneycolor = 'teal' #'cornflowerblue'
seen = {} # empty dict

colours = ['salmon','goldenrod','y','turquoise','lightsteelblue','saddlebrown','darkmagenta','slateblue','dimgray','indianred','green'] # nb. no blue, as reserved for Money-like
colourindex=0
offer = [['',''],['','']]
str_prev_offer = 'dumb'

for i,line in enumerate(lines[2:]):
    words = ' '.join(line.split()).split()
    gen= int(words[0])
    pay = float(words[2])
    offer[0][0] = words[3]
    offer[1][0] = words[4]
    offer[0][1] = words[5]
    offer[1][1] = words[6]
    # has there been a change?
    
    if (i % int(len(gens_data)/5) == 1) and (str(offer) != str_prev_offer): # and (pay > 0.1):  
        # have we seen this (new) one ever before? What was its color?    

        # give it a colour, if it's the first time.
        if (str(offer) not in seen.keys()):
            #first, special colour for UpDown so it is identifiable across runs.
            SAMEBOTHSvals = (offer[0][1] == offer[0][0]) and (offer[1][1] == offer[1][0]) # offers are the same whether self's score=0 or score>=1
            ISMONEYLIKE = (offer[0][1] == '+-+') and (offer[1][0] == '-+-') and (offer[1][1] == '-+-') # it's money!!!
            if ISMONEYLIKE:
                seen[str(offer)] = moneycolor
            # Otherwise give it a different colour and move the colour cycle along by one.
            else:
                seen[str(offer)] = colours[colourindex]
                colourindex = (colourindex+1) % len(colours)
        

        # show the strategy of offers, as a "card"
        cc = seen[str(offer)]
        faded = cc #[0.3+0.7*c/2 for c in colors.to_rgb(cc)]
        
        if ISMONEYLIKE: 
            alf, faded = 1.0, cc  # don't fade the colour for money
        else: alf = 1.0 #was 0.3
        if SAMEBOTHSvals == False:  # show the BIG box....
            for h in [0,1]:
                for S in [0,1]:
                    wd = offer_to_wd(offer[h][S]) # figure out what the string to show is
                    axTop.text(gen+dispx+h*(1.07*boxwidth), pay+dispy+S*(1.2*boxheight), 
                             r'{0}'.format(wd),fontproperties=font0, 
                             ha="left", va="bottom",alpha=alf,
                             bbox=dict(boxstyle="round",ec=ccc[h],fc=ccc[h],alpha=alf)
                             )
                    



        if SAMEBOTHSvals == True:  # show the SMALL box....
            for h in [0,1]:
                S = 0
                wd = offer_to_wd(offer[h][S]) # figure out what the string to show is
                axTop.text(gen+dispx+h*(1.07*boxwidth), pay+dispy+S*(1.2*boxheight), 
                         r'{0}'.format(wd),fontproperties=font0, 
                         ha="left", va="bottom",alpha=alf,
                         bbox=dict(boxstyle="round",ec=ccc[h],fc=ccc[h],alpha=alf)
                         )
                    
                         
        # connector line from the box's lower left corner to the actual point of origin
        axTop.plot([gen,gen+dispx],[pay+dispy/3,pay+dispy],'-',linewidth=1+1*ISMONEYLIKE,color=ccc[0])
        # blob at the end of that line, near the true point of origin.
        axTop.plot([gen],[pay+dispy/3],'.',linewidth=1+2*ISMONEYLIKE,color=ccc[0],alpha=1.)
        str_prev_offer = str(offer)
    
    axTop.set_xticks([])
    seaborn.despine(ax=axTop,bottom=True,offset=-0.1) # the important part here
    seaborn.despine(ax=axBottom, offset=0) # the important part here

outfile = args.filename.strip('.txt') + '.png'
pl.savefig(outfile)
print("Wrote {0}".format(outfile))

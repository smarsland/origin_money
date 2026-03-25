import matplotlib
#matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as PathEffects
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d import Axes3D
import string, math
from scipy.spatial.distance import hamming
from matplotlib.patches import Rectangle
from matplotlib import font_manager as fm
fixed_width_font = fm.FontProperties(family="Monospace")
        
plt.rcParams['text.usetex'] = False   # sadly, latex modes for mpl conflict with unicode, which I want more.

# Row count thresholds for different plot features
SMALL_DATASET_THRESHOLD = 50    # For horizontal lines, L* labels, detailed features
ROW_COUNT_DISPLAY_THRESHOLD = 50  # For showing row count text  
DENSE_RENDERING_THRESHOLD = 200   # For switching to imshow instead of rectangles

whiteish  = [1, 1, .92]

def setStrategyInfo():   
    strategy_info = {} # empty dictionary
    # Initialize the nested dictionaries for each strategy key
    def get_nickname(s):
        m = {('0', '0'): "AllD", 
             ('0', 'g'): "Disc",
             ('g', '0'): "Anti", 
             ('g', 'g'): "AllC" }
        # Parse the input string
        a, b, c, d = s.split('|')[0].split(',') + s.split('|')[1].split(',')
        # Generate the nickname using the mapping
        return f"{m[(a, c)]}-{m[(b, d)]}"
    
    # these are their own antis
    for s in ['0,0|0,0', '0,g|g,0', 'g,0|0,g', 'g,g|g,g']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♠', 'color':(0.4, 0.1, 0.2, 1)} 
        
    # asymmetric, with just one 'g'
    for s in ['g,0|0,0', '0,0|0,g', '0,g|0,0', '0,0|g,0']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♣', 'color':(0.4, 0.1, 0.2, 1)} 

    # asymmetric, with two 'g' entries  
    for s in ['g,0|g,0', '0,g|0,g', 'g,g|0,0', '0,0|g,g']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♦', 'color':(0.4, 0.1, 0.2, 1)} 

    # asymmetric, with three 'g'
    for s in ['g,g|0,g', 'g,0|g,g', 'g,g|g,0', '0,g|g,g']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♥', 'color':(0.4, 0.1, 0.2, 1)} 

    #some options: ☎★✢⚙  ♠♣♦♥  ♟♞♝♜♛♚
    #  ⊞⊟⊠⊡  ⊘  ⊕⊖⊗⊙ ⊚ △◬◭◮▲  ⊡□◫◧◨◾  ⬗⬖◆◇ ⋈⧑⧒⧓

    return strategy_info

def checkConservation(CN,NC):
    i=0
    while i<8:
        if ((CN[i] == '0') & (NC[i] == '0')):
            i+=1
        elif (((CN[i] == '+') & (NC[i] == '-')) | ((CN[i] == '-') & (NC[i] == '+'))):
            i+=1
        else:
            return False
    return True

def getSymmsgIfSame(d):
    print(len(d))
    todrop=[]
    d['first'] = d['CmeetsN'].str.split(pat='',n=2,expand=True)[1]
    d['symmCN'] = d['CmeetsN'].apply(lambda x:makeSymm(x))
    d['symmNC'] = d['NmeetsC'].apply(lambda x:makeSymm(x))
    # These are the symmetric strategies, so don't need this
    #d['symmStrat'] = d['Strategy'].apply(lambda x:makeSymmStrat(x))
    for i in range(len(d)): 
        if i%10000 == 0:
            print(i)
        symmInd = np.where((d['CmeetsN']==d['symmCN'].iloc[i]) & (d['NmeetsC']==d['symmNC'].iloc[i]) & (d['Strategy']==d['Strategy'].iloc[i]))[0]
        if len(symmInd)>0:
            symmInd=np.squeeze(symmInd[0])
            # Self-symmetry
            if symmInd == i:
                continue
            else:
                if i in todrop or symmInd in todrop:
                    continue
                else:
                    if d['first'].iloc[i] == '-':
                        # Drop negative starts
                        todrop.append(i)
                    else:
                        # Get rid of + and 0 starts indiscriminantly
                        todrop.append(symmInd)
    return todrop

def getSymmsgIfSame_old(d):
    todrop=[]
    for i in d['CmeetsN']:
        if len(np.where(d['CmeetsN'] == makeSymm(i))[0])>0:
            if i[0] == '-':
                if i not in todrop:
                    todrop.append(i)
            else:
                # Get rid of + and 0 starts indiscriminantly
                if makeSymm(i) not in todrop and i not in todrop:
                    todrop.append(makeSymm(i))
    return todrop

def removeScoresSymmetries(d):
    todrop=['g,g|0,0','g,0|0,0','g,g|0,g','0,0|g,0','g,0|g,0','g,g|g,0']
    d = d[~d['Strategy'].isin(todrop)].copy()
    symmStrat= ['0,0|0,0','0,g|g,0','g,0|0,g','g,g|g,g']
    symm = d[d['Strategy'].isin(symmStrat)].copy()
    symm.reset_index(drop=True, inplace=True)
    d = d[~d['Strategy'].isin(symmStrat)].copy()
    todrop=getSymmsgIfSame(symm)
    #symm.drop(symm[symm['CmeetsN'].isin(todrop)].index,inplace=True)    
    symm.drop(index=todrop,inplace=True)
    symm.drop(['first','symmCN','symmNC'],axis=1,inplace=True)
    d = pd.concat([d,symm])
    d.reset_index(drop=True,inplace=True)
    return d

def makeSymm(x):
    b = x[5] + x[4] + x[7] + x[6] + x[1] + x[0] + x[3] + x[2]           
    b=b.replace('+','a')
    b=b.replace('-','+')
    b=b.replace('a','-')
    return b

def makeSymmStrat(x):
    return x[-1::-1]

def convert_old2new_format_bbstub(x):
    return x[0] + x[4] + x[1] + x[5] + x[2] + x[6] + x[3] + x[7]

def removeBinarySymmetries(sortedDF,NmeetsC):
    # here 'sortedDF' is a dataframe containing results in the usual format
    # This does so for both Donor and Recipient parts of the rule.
    print("Removing symmetries...")

    # Make the symmetries in new columns
    sortedDF['symmCN'] = sortedDF['CmeetsN'].apply(lambda x:makeSymm(x))
    # If NmeetsC isn't used, don't make the symmetries, otherwise do
    if NmeetsC:
        sortedDF['symmNC'] = sortedDF['NmeetsC'].apply(lambda x:makeSymm(x))
    else:
        # In this case they will all be zero, but just copy them
        sortedDF['symmNC'] = sortedDF['NmeetsC'].apply(lambda x:makeSymm(x))
    sortedDF['symmStrat'] = sortedDF['Strategy'].apply(lambda x:makeSymmStrat(x))

    todelete = []
    for row in range(len(sortedDF)):
        # Find the symmetry
        symmInd = np.where((sortedDF['CmeetsN']==sortedDF['symmCN'][row]) & (sortedDF['NmeetsC']==sortedDF['symmNC'][row]) & (sortedDF['Strategy']==sortedDF['symmStrat'][row]))[0]
    
        # If the symmetry exists
        if len(symmInd)>0: 
            symmInd=np.squeeze(symmInd[0])
            # If it's a self-symmetry:
            if symmInd == row:
                continue
            else:
                # If one has already been listed for deletion;
                if row in todelete or symmInd in todelete:
                    continue
                else:
                    # Decide which one to delete, i or symmInd
                    # First thing: if the last bit of the strategy is g in only one of them, keep that one
                    if sortedDF['Strategy'][row][-1]=='g' and sortedDF['Strategy'][symmInd][-1]!='g':
                        todelete.append(symmInd)
                    elif sortedDF['Strategy'][row][-1]!='g' and sortedDF['Strategy'][symmInd][-1]=='g':
                        todelete.append(row)
                    else:
                        # Second thing: if the second bit of the strategy is g in only one of them, keep the other
                        if sortedDF['Strategy'][row][2]=='g' and sortedDF['Strategy'][symmInd][2]!='g':
                            todelete.append(row)
                        elif sortedDF['Strategy'][row][2]!='g' and sortedDF['Strategy'][symmInd][2]=='g':
                            todelete.append(symmInd)
                        else:
                            # Third thing: if there is a + in the fourth bit of CmeetsN, keep that
                            if sortedDF['CmeetsN'][row][3]=='+' and sortedDF['CmeetsN'][symmInd][3]!='+':
                                todelete.append(symmInd)
                            elif sortedDF['CmeetsN'][row][3]!='+' and sortedDF['CmeetsN'][symmInd][3]=='+':
                                todelete.append(row)
                            else:
                                # Fourth thing: errm
                                if sortedDF['CmeetsN'][row][-1]=='-' and sortedDF['CmeetsN'][symmInd][-1]!='-':
                                    todelete.append(symmInd)
                                elif sortedDF['CmeetsN'][row][-1]!='-' and sortedDF['CmeetsN'][symmInd][-1]=='-':
                                    todelete.append(row)
                                else:
                                    print(row,symmInd,"oops")
                                    print(sortedDF.iloc[row])
                                    print(sortedDF.iloc[symmInd])

    #print(todelete)
    sortedDF.drop(index=todelete,inplace=True)
    sortedDF.drop(['symmCN','symmNC','symmStrat'],axis=1,inplace=True)
    print("Done removing symmetries.")

    return sortedDF

def plotGridW1vals(df, base_tag, outdirectory):
    import matplotlib.pyplot as plt
    strategy_info = setStrategyInfo()
    
    fig, ax = plt.subplots(4,4,sharex=True, sharey=True, figsize=(10,10))
    Strategies = [k for k in strategy_info]

    counti = 0
    countj = 0
    for s in Strategies:
        symb = strategy_info[s]['symbol']
        colr = strategy_info[s]['color']
        nick = strategy_info[s]['nickname']        
        
        s1 = df[df.Strategy==s].copy()
        s1['wn'] = 1 - s1['w0'] - s1['w1']
        axx = ax[countj,counti] # this subplot
        if len(s1) > 0:
            axx.set_xlabel(r'$w_1$')
            axx.set_ylabel(r'$w_{>1}$')
            
            #make scatter plot            
            d = s1.groupby(['w1','wn','fit'],as_index=False)['CmeetsN'].count()
            for j in range(len(d)):
                # plot as a single point, whose transparency indicates the fitness.
                r, g, b, alf = colr
                alfa = min(d['fit'].iloc[j],1)
                x, y = float(d['w1'].iloc[j]), float(d['wn'].iloc[j])
                axx.plot([x], [y], 'o',
                            color=(r,g,b,alfa),markersize=10)#, edgecolor=(r,g,b,1-.5*(1-alf)))
                # annotate with the number of BBs giving equivalant w and fitnesses.
                # Rotate the position of these annotations, so they overlap less.
                axx.annotate(str(d['CmeetsN'].iloc[j]), 
                             xy=(x, y), 
                             xytext=(12*math.sin(j*math.pi/4),8*math.cos(j*math.pi/4)), 
                             textcoords='offset points', 
                             fontsize=6, ha='center', va='center', alpha=math.sqrt(alfa))
            
            axx.set_title(s+symb+nick,color=colr,fontsize=11, ha='center', va='center') 
            
            axx.set_aspect('equal', 'box')
            axx.plot([0,1], [1,0], linewidth=1, color=(0,0,0,.3))
            axx.set_xlim(-0.1,1.1)
            axx.set_ylim(-0.1,1.1)
            axx.set_xticks([0,.5,1])
            axx.set_yticks([0,.5,1])
            
        else:
            axx.axis('off')

        counti+=1
        if counti==4:
            countj+=1
            counti=0
    fig.tight_layout()

    

    # Finishing touches and save the plot
    tagline = 'grid_w1wn_' + base_tag
    #plt.title(tagline.replace('_',' '))
    outfile = outdirectory + '/' + tagline + '.png'
    plt.savefig(outfile,dpi=300)
    print('Saved plot to ' + outfile)
    outfile = outdirectory + '/' + tagline + '.pdf'
    plt.savefig(outfile)
    print('Saved plot to ' + outfile)
    plt.close()
    return

def plotGridWvals(df, base_tag, outdirectory):
    import matplotlib.pyplot as plt
    strategy_info = setStrategyInfo()
    
    fig, ax = plt.subplots(4,4,sharex=True, sharey=True, figsize=(10,10))
    Strategies = [k for k in strategy_info]

    counti = 0
    countj = 0
    for s in Strategies:
        symb = strategy_info[s]['symbol']
        colr = strategy_info[s]['color']
        nick = strategy_info[s]['nickname']        
        
        s1 = df.loc[(df.Strategy==s)]
        axx = ax[countj,counti] # this subplot
        if len(s1) > 0:
            axx.set_xlabel(r'$w_0$')
            axx.set_ylabel(r'$w_1$')
            
            #make scatter plot            
            d = s1.groupby(['w0','w1','fit'],as_index=False)['CmeetsN'].count()
            for j in range(len(d)):
                # plot as a single point, whose transparency indicates the fitness.
                r, g, b, alf = colr
                alfa = d['fit'].iloc[j]
                x, y = float(d['w0'].iloc[j]), float(d['w1'].iloc[j])
                axx.plot([x], [y], 'o',
                            color=(r,g,b,alfa),markersize=10)#, edgecolor=(r,g,b,1-.5*(1-alf)))
                # annotate with the number of BBs giving equivalant w and fitnesses.
                # Rotate the position of these annotations, so they overlap less.
                axx.annotate(str(d['CmeetsN'].iloc[j]), 
                             xy=(x, y), 
                             xytext=(12*math.sin(j*math.pi/4),8*math.cos(j*math.pi/4)), 
                             textcoords='offset points', 
                             fontsize=6, ha='center', va='center', alpha=math.sqrt(alfa))
            
            axx.set_title(s+symb+nick,color=colr,fontsize=11, ha='center', va='center') 
            
            axx.set_aspect('equal', 'box')
            axx.plot([0,1], [1,0], linewidth=1, color=(0,0,0,.3))
            axx.set_xlim(-0.1,1.1)
            axx.set_ylim(-0.1,1.1)
            axx.set_xticks([0,.5,1])
            axx.set_yticks([0,.5,1])
            
        else:
            axx.axis('off')

        counti+=1
        if counti==4:
            countj+=1
            counti=0
    fig.tight_layout()

    

    # Finishing touches and save the plot
    tagline = 'grid_w0w1_' + base_tag
    #plt.title(tagline.replace('_',' '))
    outfile = outdirectory + '/' + tagline + '.png'
    plt.savefig(outfile,dpi=300)
    print('Saved plot to ' + outfile)
    outfile = outdirectory + '/' + tagline + '.pdf'
    plt.savefig(outfile)
    print('Saved plot to ' + outfile)
    plt.close()
    return

def plotGridABCvals(a, base_tag, outdirectory):# Create a 4x4 grid of subplots
    import matplotlib.pyplot as plt
    strategy_info = setStrategyInfo()
    fig, axes = plt.subplots(4, 4, figsize=(12, 12), subplot_kw={'projection': '3d'})
    Strategies = [k for k in strategy_info]
    
    # Loop through the subplots and customize them
    for i, ax in enumerate(axes.flat):

        s = Strategies[i]
        symb = strategy_info[s]['symbol']
        colr = strategy_info[s]['color']
        nick = strategy_info[s]['nickname']        
        s1 = a.loc[(a.Strategy==s)]
        if len(s1) > 0:
            #make scatter plot            
            d = s1.groupby(['a','b','c','fit'],as_index=False)['CmeetsN'].count()
            for j in range(len(d)):
                r, g, b, alf = colr
                alf = d['fit'].iloc[j]
                ax.plot([d['a'].iloc[j], d['a'].iloc[j]],  
                        [d['b'].iloc[j], d['b'].iloc[j]],  
                        [d['c'].iloc[j], 0],
                        color=(r,g,b,math.sqrt(alf)), linestyle='dotted', linewidth=0.5)
                ax.scatter([d['a'].iloc[j]],[d['b'].iloc[j]],[d['c'].iloc[j]],
                           color=(r,g,b,alf),  s=60)
                
            #for index, row in s1.iterrows():
            #    fit = row['fit']
            #    ax.text(row['a'],row['b'],row['c'], s=symb, color=colr, alpha=0.5, fontsize=32*fit, ha='center', va='center')
            ax.set_title(s+symb+nick,color=colr,fontsize=12, ha='center', va='center') 
            ax.set_xlim(0, 1)  
            ax.set_ylim(1, 0)  # Set y limits   NOTE!!!!! HACKY WAY TO PLACE ORIGIN SENSIBLY
            ax.set_zlim(0, 1)  
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_zticks([])
            #ax.set_xlabel(r'$\alpha$')
            #ax.set_ylabel(r'$\beta$')
            #ax.set_zlabel(r'$\gamma$')
            ax.text(1.1,0,0,r'$\alpha$',fontsize=18, ha='center', va='center')
            ax.text(0,1.1,0,r'$\beta$', fontsize=18, ha='center', va='center')
            ax.text(0,0,1.1,r'$\gamma$',fontsize=18, ha='center', va='center')
            # Set aspect ratio
            extents = ax.get_w_lims()
            ax.auto_scale_xyz(*[[0, 1]]*3)
            #ax.plot_box([0, 1, 0, 1, 0, 1])
        else:
            ax.axis('off')

    plt.tight_layout()

    # Finishing touches and save the plot
    tagline = 'grid_abc_' + base_tag
    #plt.title(tagline.replace('_',' '))
    #plt.draw()
    outfile = outdirectory + '/' + tagline + '.png'
    plt.savefig(outfile,dpi=400)
    print('Saved plot to ' + outfile)
    outfile = outdirectory + '/' + tagline + '.pdf'
    plt.savefig(outfile)
    print('Saved plot to ' + outfile)
    plt.close()
    return

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
def mapScoresRuleToBinary(CmeetsN):
    """
    take any CmeetsN and turn it into the rule that would be equivalent if 
    scores were thresholded
    """
    assert len(CmeetsN) == 8
    # Turn any '-' in the "even" indexed characters (ie Donor S=0) into '0' 
    evens = CmeetsN[::2].replace('-', '0')
    # Turn any '+' in the "odd" index characters (where Donor's S=1) into '0'
    odds = CmeetsN[1::2].replace('+', '0')
    result = evens[0] + odds[0] + evens[1] + odds[1] + evens[2] + odds[2] + evens[3] + odds[3] 
    return result

def createLeading8(): 
    """
    This is a copy, but in python, of the same function in ../helper_funcs.jl (in julia).
    """
    leading8 = dict()
    
    base_colors = {
        'red': np.array([1.0, 0.0, 0.0]),
        'green': np.array([0.0, 1.0, 0.0]),
        'blue': np.array([0.0, 0.0, 1.0]),
        'yellow': np.array([0.9, 0.9, 0.0]),
        'cyan': np.array([0.0, 0.9, 0.9]),
        'magenta': np.array([0.9, 0.0, 0.9]),
        'orange': np.array([1.0, 0.5, 0.0]),
        'purple': np.array([0.5, 0.0, 0.5])
    }
    variety = [1.0, 1.0, 0.3]  # 1.0 is full color, lower nums are darker varieties

    humble = "g,0|g,g"  # The first TWO members of leading 8 have this as ESS
    disc = "0,0|g,g"  # The other SIX members of leading 8 have this as ESS
    NmeetsC  = "00000000"
    
    # L1
    base_color = base_colors['red']
    binaryCmeetsN  = '00+00-+0' #  was"0+0+00-0"
    strat = humble
    leading8["L1binary"] = {"nick":"L1", 
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]}    
    
    leading8["L1binary_symm"] = {"nick":"L1 s", 
                    "CmeetsN":'+00-000-', #was "+0000-0-",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    
    
    # L2
    base_color = base_colors['green']
    binaryCmeetsN  = '00+-0-+0' #was "0+0+0--0"
    strat = humble
    leading8["L2binary"] = {"nick":"L2", #Consistent Standing  
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]} 

    leading8["L2binary_symm"] = {"nick":"L2 s", 
                    "CmeetsN":'+00-00+-', #was"+00+0-0-",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    


    # L3
    base_color = base_colors['blue']
    binaryCmeetsN  = '+0+00-+0' #was"++0+00-0"
    strat = disc
    leading8["L3binary"] = {"nick":"L3", #Simple Standing  
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]} 
    
    leading8["L3binary_symm"] = {"nick":"L3 s", 
                    "CmeetsN": '+00-0-0-', #was "+0000---",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    

    
    # L4    
    base_color = base_colors['yellow']
    binaryCmeetsN  = '+0000-+0' #was "+00+00-0"
    leading8["L4binary"] = {"nick":"L4", 
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]}  
    
    leading8["L4binary_symm"] = {"nick":"L4 s", 
                    "CmeetsN":'+00-0-00', #was "+0000--0",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    
    
    # L5
    base_color = base_colors['cyan']
    binaryCmeetsN  = '+0+-0-+0' #was "++0+0--0"
    leading8["L5binary"] = {"nick":"L5", 
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]} 
    leading8["L5binary_symm"] = {"nick":"L5 s", 
                    "CmeetsN":'+00-0-+-', #was "+00+0---",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    
    
    # L6
    base_color = base_colors['magenta']
    binaryCmeetsN  = '+00-0-+0'#was "+00+0--0"
    leading8["L6binary"] = {"nick":"L6", #Stern Judging  
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]} 
    leading8["L6binary_symm"] = {"nick":"L6 s", 
                    "CmeetsN":'+00-0-+0', #was "+00+0--0",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    
    
    
    # L7
    base_color = base_colors['orange']
    binaryCmeetsN  = '00000-+0' #was "000+00-0"
    leading8["L7binary"] = {"nick":"L7", #Staying  
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]} 
    leading8["L7binary_symm"] = {"nick":"L7 s", 
                    "CmeetsN":'+00-0000', # was "+0000-00",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}  
    
    
    # L8
    base_color = base_colors['purple']
    binaryCmeetsN  = '000-0-+0' #was "000+0--0" 
    leading8["L8binary"] = {"nick":"L8", 
                    "CmeetsN":binaryCmeetsN, 
                    "NmeetsC":NmeetsC, 
                    "strategy":strat, "color":base_color * variety[1]}

    leading8["L8binary_symm"] = {"nick":"L8 s", 
                    "CmeetsN":'+00-00+0', #was "+00+0-00",
                    "NmeetsC":NmeetsC, 
                    "strategy":makeSymmStrat(strat), 
                    "color":base_color * variety[2]}    
    

    # MONEY!.............  $¢
    leading8["Money"] = {"nick":"$", 
                         "CmeetsN":"000000++", 
                         "NmeetsC":"000000--", 
                         "strategy":disc, 
                         "color":np.zeros(3)} 

    return leading8


##########################################################################
##########################################################################
def get_ordinal(n):
    """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
    if n == 0:
        return "Start"
    elif n == 1:
        return "1st"
    elif n == 2:
        return "2nd"
    elif n == 3:
        return "3rd"
    else:
        return f"{n}th"

##########################################################################
##########################################################################
def plotFigure(DF, base_tag, outdirectory, doSort=True, royal_road=False, show_bb_labels=False, show_cons=False):
    """
    Generalized plotting function with dynamic figure width based on BB columns.
    """

    if doSort:
        DF = DF.sort_values(['fit', 'Strategy'], ascending=[True, True], ignore_index=True)
        print("Sorting applied in reverse order.")
    else:
        print("Original order retained.")

    # Determine BB columns BEFORE royal road processing to preserve original logic
    BB_col_names = ['CmeetsN'] # take this one, every time (and even if it's all zeros)
    for part in ['NmeetsC', 'NmeetsN']:
        if part in DF:
            # Create a string of zeros the same length as the first element in the column
            zeros_str = '0' * len(DF[part].iloc[0])
            # Check if the entire column is not all zeros
            if not np.all(DF[part] == zeros_str):
                BB_col_names.append(part)

    # Insert blank rows for royal road visualization
    if royal_road:
        print("Royal road mode: inserting blank rows between data rows.")
        # Create blank rows with same structure but filled with zeros/empty strings
        blank_rows = []
        for i in range(len(DF)):  # Create blank row for each data row
            data_row = DF.iloc[i].copy()
            blank_row = data_row.copy()
            
            # Set BB columns to special blank marker
            for col in ['CmeetsN', 'NmeetsC', 'NmeetsN']:
                if col in blank_row:
                    blank_row[col] = 'B' * len(str(data_row[col]))  # Use 'B' for blank
            
            # Set other fields to neutral/empty values
            blank_row['Strategy'] = ''
            blank_row['fit'] = 0.0
            if 'count' in blank_row:
                blank_row['count'] = 0
            if 'SelfSelf' in blank_row:
                blank_row['SelfSelf'] = '0' * len(str(data_row['NmeetsN'])) if 'NmeetsN' in data_row else ''
            
            blank_rows.append(blank_row)
        
        # Interleave blank rows with data rows, starting with a blank row
        new_rows = []
        for i, row in DF.iterrows():
            new_rows.append(blank_rows[i])  # Add blank row first
            new_rows.append(row)            # Then add data row
        
        DF = pd.DataFrame(new_rows).reset_index(drop=True)

    N = len(DF)
    DF['count'] = 0
    if 'NmeetsN' in DF.columns:
        DF['SelfSelf'] = DF['NmeetsN']
    else:
        DF['SelfSelf'] = ''

    strategy_info = setStrategyInfo()

    # Create Leading 8 detection once and share between plotting functions
    lead8 = createLeading8()
    lead8_indices = set()  # Set of row indices that are Leading 8
    money_indices = set()  # Set of row indices that are Money
    
    for k, v in lead8.items():
        match_view = DF[
            (DF['Strategy'] == v['strategy']) &
            (DF['CmeetsN'].apply(mapScoresRuleToBinary) == v['CmeetsN'])
        ]
        v['indices'] = match_view.index.tolist()
        
        # Collect indices for color override
        if 'Money' in k:
            money_indices.update(v['indices'])
        else:
            lead8_indices.update(v['indices'])

    # Adjust figure width dynamically based on BB columns
    base_width = 3.5  # Minimum width for essential elements
    bb_column_width = 1.5  # Width added per BB column
    fig_width = base_width + len(BB_col_names) * bb_column_width

    # Adjust figure height
    if N <= 30:
        fig_height = N * 0.2
        print(f"Small dataset: Scaling height to {fig_height:.2f}.")
        show_lead8 = True
    else:
        fig_height = fig_width * 1.5
        print(f"Large dataset: Fixed height set to {fig_height:.2f}.")
        show_lead8 = False
                
    # TEMPORARILY......    
    #show_cons = False #True
    #show_lead8  = False
    
    # Create figure
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)

    # Create axes
    axs_BB, ax_L8, ax_cons, ax_ESS = create_axes(fig, fig_width, fig_height, BB_col_names, show_lead8=show_lead8, show_cons=show_cons)

    # Plot BB columns
    if 'inary' in base_tag or 'tokens' in base_tag.lower() or 'road' in base_tag.lower():
        show_labels=True
    else:
        show_labels=False

    plot_bb_columns(axs_BB, DF, BB_col_names, show_labels and show_bb_labels, royal_road)
    
    # Add labels below BB column groups (only if there are multiple groups)
    if len(BB_col_names) > 1:
        label_map = {'CmeetsN': 'donor change', 'NmeetsC': 'recvr change', 'NmeetsN': 'other'}
        for i, part in enumerate(BB_col_names):
            if part in label_map:
                ax = axs_BB[i]
                label_text = label_map[part]
                # Position label below the axis
                ax.text(0.5, -0.02, label_text, transform=ax.transAxes,
                       ha='center', va='top', fontsize=10, color='black', weight='bold')

    # Plot Lead8 column
    if show_lead8:
        plot_lead8_column(ax_L8, DF, strategy_info, lead8, lead8_indices, money_indices)

    # Plot conservative column
    if show_cons:
        plot_cons_column(ax_cons, DF)

    # Plot ESS pane
    plot_ess_pane(ax_ESS, DF, strategy_info, lead8_indices, money_indices)

    # Save figure
    suffix = "" if doSort else "_as_is"
    base_tag = base_tag.removesuffix(".txt")
    outfile = f"{outdirectory}/{base_tag}{suffix}.png"
    plt.savefig(outfile, dpi=600, bbox_inches="tight")
    print(f'Saved plot to: {outfile}')
    outfile = f"{outdirectory}/{base_tag}{suffix}.pdf"
    plt.savefig(outfile, bbox_inches="tight")
    print(f'Saved plot to: {outfile}')
    plt.close(fig)
###########
####################

def plot_bb_columns(axs_BB, DF, BB_col_names, show_labels=True, royal_road=False):
    """
    Plot the Big Brother (BB) columns and dynamically add the header above the "CmeetsN" column.
    """
    # Add royal road progression labels on the left side
    if royal_road and len(axs_BB) > 0:
        leftmost_ax = axs_BB[0]  # Get leftmost BB column axis
        data_row_count = 0
        
        for row_idx in range(len(DF)):
            strategy = DF['Strategy'].iloc[row_idx]
            if strategy != '':  # This is a data row
                label = get_ordinal(data_row_count)
                # Position label to the left of the leftmost BB column
                leftmost_ax.text(-0.8, row_idx, label, 
                                ha='right', va='center', fontsize=8,
                                color='black', weight='bold')
                data_row_count += 1
            else:  # This is a blank row
                # Add downward arrow for all blank rows except the very first one (row 0)
                if row_idx > 0:
                    leftmost_ax.text(-1.2, row_idx, '↓', 
                                    ha='center', va='center', fontsize=10,
                                    color='gray')
    # Locate the index of 'CmeetsN' for alignment
    if 'CmeetsN' in BB_col_names:
        cmeetsn_index = BB_col_names.index('CmeetsN')
        cmeetsn_ax = axs_BB[cmeetsn_index]  # Relevant axes for alignment
        fig = cmeetsn_ax.figure  # Get the figure object

        # Create a header aligned with "CmeetsN", with consistent absolute height and gap
        header_abs_height = 0.5  # Fixed height in inches
        header_gap = 0.01         # Fixed gap between BB grid and header (in inches)
        dpi = fig.get_dpi()

        # Convert fixed gap and height to relative figure size
        header_height = header_abs_height / fig.get_figheight()
        header_gap_rel = header_gap / fig.get_figheight()

        header_ax = fig.add_axes([
            cmeetsn_ax.get_position().x0,    # Align horizontally with "CmeetsN"
            cmeetsn_ax.get_position().y1 + header_gap_rel, # Gap above BB grid
            cmeetsn_ax.get_position().width, # Same width as "CmeetsN"
            header_height                    # Fixed height
        ])
        cell_size = cmeetsn_ax.get_position().width / 8  # Adjust cell size dynamically
        plot_matrix_header(header_ax, cell_size, True)  # Always show REC/ACT/DON labels


    for i, part in enumerate(BB_col_names):
        ax = axs_BB[i]
        for spine in ax.spines.values(): spine.set(linewidth=0, color='gray') # no borders
        color_map = {'+': [0.64, 0.90, 0.21],  # Green
                     '-': [0.3, 0.6, 1.0],     # Blue
                     '0': [0.85, 0.85, 0.85]}  # Light gray

        # Build and plot the color matrix for the main content
        strings = DF[part].values
        
        # NEW APPROACH: Individual rectangles (can be reverted to imshow if needed)
        # Old imshow approach commented out:
        # color_matrix = np.array([
        #     np.array([color_map[char] for char in s], dtype=float) for s in strings
        # ])
        # ax.imshow(color_matrix, aspect='auto', interpolation='nearest', origin='upper')
        
        # New individual rectangle approach with variable widths:
        from matplotlib.patches import Rectangle
        ax.set_xlim(-0.5, len(strings[0]) - 0.5)
        ax.set_ylim(-0.5, len(strings) - 0.5)
        ax.invert_yaxis()  # Match imshow's origin='upper'
        
        # For CmeetsN, determine which columns are common vs rare
        # (Removing the global common_columns logic - need to do this per row)
        
        for row_idx, s in enumerate(strings):
            # For CmeetsN, determine which columns are common (have tick marks) for this specific row
            common_columns_this_row = set()
            if part in ['CmeetsN','NmeetsC']:
                strat = DF['Strategy'].iloc[row_idx]
                # Skip processing for blank rows (empty strategy)
                if strat and '|' in strat:
                    n0, n1 = strat.split('|')
                    actions = n0.split(',') + n1.split(',')
                    slots = [0,1,4,5]
                    for counter, act in enumerate(actions):
                        if act == '0':  # Common case - gets tick mark
                            common_columns_this_row.add(slots[counter])
                        elif act == 'g':  # Common case - gets tick mark  
                            common_columns_this_row.add(slots[counter] + 2)
                        if act == '0':  # Common case - gets tick mark
                            common_columns_this_row.add(slots[counter])
                        elif act == 'g':  # Common case - gets tick mark  
                            common_columns_this_row.add(slots[counter] + 2)
            
            for col_idx, char in enumerate(s):
                # Skip drawing for blank rows (marked with 'B')
                if char == 'B':
                    continue
                    
                # Parameter for narrow column width (adjust as needed)
                narrow_width = 0.33  # Width for rare cases (1/3 of normal)
                normal_width = 0.80   # Width for common cases
                
                # Narrow width for rare columns (no tick marks), normal width for common ones (with tick marks)
                if ((part == 'CmeetsN') or (part == 'NmeetsC')) and col_idx not in common_columns_this_row:
                    rect_width = narrow_width  # Narrow for rare cases (no tick marks)
                else:
                    rect_width = normal_width  # Normal width for common cases (with tick marks)
                
                rect_height = 1.0
                
                # Center the rectangle at the grid position
                rect_x = col_idx - rect_width/2
                rect_y = row_idx - rect_height/2
                
                color = color_map[char]
                rect = Rectangle((rect_x, rect_y), rect_width, rect_height, 
                               facecolor=color, edgecolor='none')
                ax.add_patch(rect)

        # Set labels and remove ticks
        if show_labels:  # Only show labels if flag is True
            if part=='CmeetsN' : 
                label='Donor\'s change:'
                show_symbols = True
            elif part=='NmeetsC' : 
                label='Receiver\'s change'
                show_symbols = False
            else: 
                label='random encounters'
                show_symbols = False
            ax.set_xlabel(label, fontsize=11, labelpad=10, ha='center', va='top')  # Center-align for consistency
        else:
            show_symbols = False  # Don't show symbols when labels are hidden
        ax.set_xticks([])
        ax.set_yticks([])

        # Add plus/minus symbols only for CmeetsN (Donor's change)
        if show_symbols:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            bbox = ax.xaxis.get_label().get_window_extent(renderer=renderer)
            bbox_axes = ax.transAxes.inverted().transform(bbox)
            label_right_edge = bbox_axes[1, 0]  # Right edge of actual rendered text
            label_center_y = (bbox_axes[0, 1] + bbox_axes[1, 1]) / 2
            
            # Position symbols starting from the right edge of the text
            txt = ax.text(label_right_edge + 0.02,  label_center_y, '+', transform=ax.transAxes,
                  color='black', fontsize=8, ha='left', va='center',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor=color_map['+'], edgecolor='none', pad=2))
            txt = ax.text(label_right_edge + 0.09, label_center_y, '0', transform=ax.transAxes,
                  color='black', fontsize=8, ha='left', va='center',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor=color_map['0'], edgecolor='none', pad=2))
            txt = ax.text(label_right_edge + 0.16, label_center_y, '\u2212', transform=ax.transAxes,
                  color='black', fontsize=8, ha='left', va='center',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor=color_map['-'], edgecolor='none', pad=2))

#        txt = ax.text(label_right + 0.1, label_center, '\u229E', transform=ax.transAxes,   
#                color='black', fontsize=11, ha='right', va='center')
#        txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground=color_map['+'])])
#        txt = ax.text(label_right + 0.12, label_center, '\u229F', transform=ax.transAxes,
#              color='black', fontsize=11, ha='left', va='center')
#        txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground=color_map['-'])])
        
        
#        xlabel_obj = ax.xaxis.get_label()
#        x, y = xlabel_obj.get_position()
#        ax.text(x, y, '+', transform=ax.transAxes, color=(0.64, 0.90, 0.21), fontsize=11, ha='left')
#        ax.text(0.57, -0.12, '-', transform=ax.transAxes, color=(0.3, 0.6, 1.0), fontsize=11, ha='left')
        
        # TICK MARKS (commented out - now using narrow columns to indicate rare vs common cases)
        # if part == 'CmeetsN':
        #     for row, strat in enumerate(DF['Strategy'].values):
        #         n0, n1 = strat.split('|')
        #         actions = n0.split(',') + n1.split(',')
        #         slots = [0,1,4,5]
        #         for counter, act in enumerate(actions):
        #             if act == '0': # no help given, both parties S0
        #                 ax.text(slots[counter] - 0.2, row, '\u2713', color='red', ha='center', va='center', fontsize=10)
        #             if act == 'g': # help given, both parties S0  
        #                 ax.text(slots[counter]+2 - 0.2, row, '\u2713', color='red', ha='center', va='center', fontsize=10)
                
        # End of tick marks
        # if part == 'CmeetsN':
        #     for row, strat in enumerate(DF['Strategy'].values):
        #         n0, n1 = strat.split('|')
        #         actions = n0.split(',') + n1.split(',')
        #         slots = [0,1,4,5]
        #         for counter, act in enumerate(actions):
        #             if act == '0': # no help given, both parties S0
        #                 ax.text(slots[counter] - 0.2, row, '\u2713', color='black', ha='center', va='center', fontsize=10)
        #             if act == 'g': # help given, both parties S0  
        #                 ax.text(slots[counter]+2 - 0.2, row, '\u2713', color='black', ha='center', va='center', fontsize=10)
                
                
        # Vertical lines commented out
        # if part in ['CmeetsN','NmeetsC']:
        #     # Vertical lines between every column (not just every 2nd column)
        #     for col in range(1, 8):  # Lines between columns 0-1, 1-2, 2-3, etc.
        #         ax.axvline(x=col - 0.5, color='gray', linewidth=0.5, alpha=0.5)
        
        # Add horizontal lines under each row for small datasets
        if len(DF) < SMALL_DATASET_THRESHOLD:
            for row in range(len(DF) - 1):  # Don't draw line after last row
                ax.axhline(y=row + 0.5, color='gray', linewidth=0.5, alpha=0.5)
        else:
            for col_pair in range(1,2):
                ax.axvline(x=2 * col_pair - 0.5, color='gray', linewidth=0.5, alpha=0.5)

#####################################

def plot_cons_column(ax_cons, DF):
    """
    Plots the conservation column.
    """
    ax_cons.set_xlabel('Cons', fontsize=11, rotation=0, labelpad=10, va='top')
    ax_cons.text(0.0, -1, '', fontsize=7)

    #DF['Conservative'] = DF.apply(lambda x: checkConservation(x['CmeetsN'], x['NmeetsC']), axis=1)
    rows = DF.index[DF['Conservative']==True].tolist()
    #print(rows)
    #rows = np.where(DF['Conservative']==True)
    for i in rows:
        # Should check strategy too...
        if ((DF['CmeetsN'].iloc[i] == '000000++') & (DF['NmeetsC'].iloc[i] == '000000--')):
            ax_cons.text(0.9, i, '\u0024', color='red', ha='center', va='center', fontsize=10)
        else:
            ax_cons.text(0.9, i, '\u2713', color='black', ha='center', va='center', fontsize=10)

    ax_cons.set_xticks([])
    ax_cons.spines[['left', 'right', 'bottom']].set_visible(False)

#####################################

def plot_lead8_column(ax_L8, DF, strategy_info, lead8, lead8_indices, money_indices):
    """
    Plots the Lead8 column with strategy names and gray annotations.
    """
    #ax_L8.set_xlabel('Strategy', fontsize=11, rotation=0, labelpad=10, va='top')
    #ax_L8.text(0.0, -1, '\u2713\u2713     \u2713\u2713', fontsize=7)
    ax_L8.text(0.0, -1, r'ESS strategy', fontsize=7)

    # Use the shared Leading 8 detection (passed from plotFigure)

    # Plot strategy names with ditto marks for repetition
    previous_non_blank_strategy = None
    for row, strat in enumerate(DF['Strategy'].values):
        # Simple color scheme: black for Leading 8 combinations, dark gray for others
        if row in lead8_indices:
            text_color = (0.0, 0.0, 0.0, 1.0)  # Black for Leading 8 combinations
        else:
            text_color = (0.4, 0.4, 0.4, 1.0)  # Dark gray for other combinations
        
        # Use ditto mark if strategy is same as previous non-blank strategy
        if strat == '' or strat not in strategy_info:
            display_text = ''  # Blank for empty rows
        elif previous_non_blank_strategy is not None and strat == previous_non_blank_strategy:
            display_text = '″'  # Double quote ditto mark
        else:
            display_text = strategy_info[strat]['nickname']
            
        ax_L8.text(0.0, row, display_text,
                   color=text_color, 
                   ha='left', va='center', fontsize=8,
                   fontproperties=fixed_width_font)
        
        # Update previous_non_blank_strategy only for actual strategies (not blanks)
        if strat != '' and strat in strategy_info:
            previous_non_blank_strategy = strat
    
    # Plot Lead8 annotations ('L1' and so on) - moved to cooperation bars
    # for k, v in lead8.items():
    #     for i in v['indices']:
    #         ax_L8.text(0.9, i, v['nick'], 
    #                    color='black', ha='left', va='center', fontsize=6, 
    #                    bbox=dict(facecolor=whiteish, 
    #                          edgecolor=(1.0, 0.5, 0.0),  # Orange border for Leading 8 consistency
    #                          linewidth=2.0))
    
    ax_L8.set_xticks([])
    ax_L8.spines[['left', 'right', 'bottom']].set_visible(False)

#####################################

def plot_ess_pane(ax_ESS, DF, strategy_info, lead8_indices, money_indices):
    """
    Plots the ESS pane showing fitness lines and cooperation levels.
    """
    # Calculate line width based on actual available space per row
    fig_height_inches = ax_ESS.figure.get_figheight()
    dpi = ax_ESS.figure.get_dpi()
    fig_height_points = fig_height_inches * dpi
    
    # Use about 70% of available vertical space per row for the line width
    space_per_row_points = fig_height_points / len(DF)
    line_width = max(0.1, min(10, 0.7 * space_per_row_points))  # 70% of space, with sensible bounds
    
    # Plot ESS fitness lines - use adaptive rendering based on data density
    num_rows = len(DF)
    
    if num_rows > DENSE_RENDERING_THRESHOLD:  # Use imshow for dense data to avoid rendering artifacts
        import numpy as np
        
        # Create data array for imshow - each row represents fitness values
        cooperation_data = np.zeros((num_rows, 100))  # 100 x-resolution for smooth bars
        colors_data = np.ones((num_rows, 100, 3))  # RGB color array, initialized to white (1,1,1)
        
        for rank, (fit, strat) in enumerate(zip(DF['fit'][::-1], DF['Strategy'][::-1])):
            # Skip blank rows
            if strat == '':
                continue
                
            row_index = len(DF) - 1 - rank  # Convert rank back to original DF index
            if row_index in lead8_indices:
                color = np.array([0.0, 0.0, 0.0])  # Black for Leading 8
            else:
                color = np.array([0.4, 0.4, 0.4])  # Dark gray for others
            
            # Fill the cooperation bar up to the fitness level
            x_end = int(fit * 100)
            cooperation_data[rank, :x_end] = 1.0
            colors_data[rank, :x_end] = color
            
            # Handle zero or near-zero fitness case with small visible bar
            if x_end == 0:  # Catches both 0.0 and values that round to 0
                colors_data[rank, :2] = color  # 2% width for visibility
        
        # Plot as image
        ax_ESS.imshow(colors_data, aspect='auto', extent=[0, 1, 0, num_rows], 
                     interpolation='nearest', origin='lower')
        
    else:  # Use rectangles for smaller datasets to maintain crisp edges
        from matplotlib.patches import Rectangle
        for rank, (fit, strat) in enumerate(zip(DF['fit'][::-1], DF['Strategy'][::-1])):
            # Skip blank rows
            if strat == '':
                continue
                
            # Simple color scheme: black for Leading 8 combinations, dark gray for others
            row_index = len(DF) - 1 - rank  # Convert rank back to original DF index
            if row_index in lead8_indices:
                colr = (0.0, 0.0, 0.0, 1.0)  # Black for Leading 8 combinations
            else:
                colr = (0.4, 0.4, 0.4, 1.0)  # Dark gray for other combinations
            
            # Use rectangles for clean rendering
            bar_height = 0.9  # Height in data coordinates (90% of row space)
            rect = Rectangle((0, rank + 0.5 - bar_height/2), fit, bar_height, 
                            facecolor=colr, edgecolor=colr, linewidth=0)
            ax_ESS.add_patch(rect)
            
            if fit < 0.01:  # Small visible bar for zero or near-zero fitness
                # Small rectangle for zero-fitness cases
                rect_zero = Rectangle((0, rank + 0.5 - bar_height/2), 0.02, bar_height,
                                    facecolor=colr, edgecolor=colr, linewidth=0)
                ax_ESS.add_patch(rect_zero)

    # Add L* labels directly on Leading 8 cooperation bars (only if not too many rows)
    if len(DF) <= SMALL_DATASET_THRESHOLD:
        # We need to recreate lead8 here or pass it as parameter
        lead8 = createLeading8()
        for k, v in lead8.items():
            match_view = DF[
                (DF['Strategy'] == v['strategy']) &
                (DF['CmeetsN'].apply(mapScoresRuleToBinary) == v['CmeetsN'])
            ]
            v['indices'] = match_view.index.tolist()
            
            for i in v['indices']:
                # Convert from DF index to plot rank (reversed)
                plot_rank = len(DF) - 1 - i
                # Place label at left side of bar, vertically centered
                ax_ESS.text(0.05, plot_rank + 0.5, v['nick'], 
                           color='white', ha='left', va='center', fontsize=7, 
                           weight='bold')


    # Configure the ESS axis
    ax_ESS.xaxis.set_ticks_position('top')
    ax_ESS.xaxis.set_label_position('top')  # Move label to top
    ax_ESS.set_xlim(0.0, 1.0)
    ax_ESS.set_xlabel('Cooperation level', fontsize=11, labelpad=10)

    ax_ESS.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_ESS.set_yticks([])
    ax_ESS.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
    ax_ESS.set_ylim(0, len(DF))
    ax_ESS.spines[['left', 'right', 'bottom']].set_visible(False)

    # Adjust xtick label size
    ax_ESS.tick_params(axis='x', labelsize=8)  # Smaller font size for xtick labels

    # Show row count only for larger datasets and position it 1/4 down from top
    if len(DF) > ROW_COUNT_DISPLAY_THRESHOLD:
        y_position = len(DF) * 0.75  # 1/4 down from top (since y-axis is reversed)
        ax_ESS.text(0.45, y_position, f'{len(DF)} rows in all',  
                    color='gray', ha='left', va='center', fontsize=10,
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='white', linewidth=0.5))

####################################

from matplotlib.gridspec import GridSpec

def create_axes(fig, fig_width, fig_height, BB_col_names, show_lead8=True, show_cons=True, ess_ratio=3, header_height_factor=0.06, cell_height=None):
    """
    Creates axes for the BB columns, optional Lead8 column, ESS pane, and header.
    The `cell_height` ensures consistent absolute height for the header matrix cells.
    """
    bot, top = 0.1, 0.93  # Main plot height bounds
    xcurrent = 0.05
    axs_BB = []
    lead8_width = 0.8
    cons_width = 0.05

    # Add BB column axes
    for part in BB_col_names:
        if part in ["CmeetsN","NmeetsC"]:
            axs_BB.append(fig.add_axes([xcurrent, bot, 2 / fig_width, top - bot]))
            xcurrent += (2 + 0.6) / fig_width
        else:
            axs_BB.append(fig.add_axes([xcurrent, bot, 1 / fig_width, top - bot]))
            xcurrent += (1 + 0.6) / fig_width
        
    # Add Lead8 column axis if needed
    ax_L8 = None
    if show_lead8:
        ax_L8 = fig.add_axes([xcurrent, bot, lead8_width / fig_width, top - bot], yticklabels=[], sharey=axs_BB[0])
        xcurrent += (lead8_width + 0.22) / fig_width

    # Add conservative column axis if needed
    ax_cons = None
    if show_cons:
        ax_cons = fig.add_axes([xcurrent, bot, cons_width / fig_width, top - bot], yticklabels=[], sharey=axs_BB[0])
        xcurrent += (cons_width + 0.22) / fig_width

    # Add ESS pane axis
    ax_ESS = fig.add_axes([xcurrent, bot, ess_ratio / fig_width, top - bot], yticklabels=[])

    return axs_BB, ax_L8, ax_cons, ax_ESS


######################################
def plot_matrix_header(ax, cell_size,show_labels):
    """
    Plots a 3x8 matrix at the top of the BB columns.
    `matrix` should be a 3x8 list of values or colors.
    `cell_size` determines the size of each cell.
    """
    NOHELP = '\u00B7' #'\u2639' # \u2639 is a frown emoji. Other options: '0' or an x: '\u02e3'
    HELPED = '\u263A' 
    labels = [[0,1,0,1,0,1,0,1], [NOHELP,HELPED,NOHELP,HELPED],  [0,1]]
    row_label = ['Donor ', 'Action ', 'Recvr ']
    ax.set_xlim(0, 8 * cell_size)  # Align with BB column width
    ax.set_ylim(0, 3 * cell_size)  # Height based on cell size
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')  # Hide default axes

    i=1
    for row in range(3):
        wid = cell_size*i
        for col in range(int(8/i)):
            rect = plt.Rectangle(
                (col * wid, row * cell_size),  # Bottom-left corner
                wid, cell_size,               # Width, height
                edgecolor='gray', facecolor='white'
            )
            ax.add_patch(rect)
            character = str(labels[row][col])
            ax.text(
                (col + 0.5) * wid, (row+0.5) * cell_size,
                character, ha='center', va='center', color='gray', 
                fontsize=8)
        i *= 2
        if show_labels:
            ax.text((0.0) * cell_size, (row+0.5) * cell_size,
                row_label[row], ha='right', va='center', color='gray',
                fontsize=8)
    return
########################################

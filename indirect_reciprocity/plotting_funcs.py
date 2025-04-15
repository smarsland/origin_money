import matplotlib
#matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d import Axes3D
import string, math
from scipy.spatial.distance import hamming
from matplotlib.patches import Rectangle
from matplotlib import font_manager as fm
fixed_width_font = fm.FontProperties(family="Monospace")

plt.rcParams['text.usetex'] = False
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
        'symbol':'♠', 'color':(0, 0, .5, 1)} 
        
    # asymmetric, with just one 'g'
    for s in ['g,0|0,0', '0,0|0,g', '0,g|0,0', '0,0|g,0']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♣', 'color':(.5, 0, 0, 1)} 

    # asymmetric, with two 'g' entries
    for s in ['g,0|g,0', '0,g|0,g', 'g,g|0,0', '0,0|g,g']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♦', 'color':(0, .45, 0, 1)} 

    # asymmetric, with three 'g'
    for s in ['g,g|0,g', 'g,0|g,g', 'g,g|g,0', '0,g|g,g']:
        strategy_info[s] = {'nickname': get_nickname(s), 
        'symbol':'♥', 'color':(.4, .35, 0, 1)} 

    #some options: ☎★✢⚙  ♠♣♦♥  ♟♞♝♜♛♚
    #  ⊞⊟⊠⊡  ⊘  ⊕⊖⊗⊙ ⊚ △◬◭◮▲  ⊡□◫◧◨◾  ⬗⬖◆◇ ⋈⧑⧒⧓

    return strategy_info

def getSymmsgIfSame(d):
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
    todrop=['g,g|0,0','g,0|0,0','g,g|0,g','0,0|g,0','g,0|g,0','g,g|g,0','g,g|0,g']
    d = d[~d['Strategy'].isin(todrop)]
    todrop=getSymmsgIfSame(d)
    d.drop(d[(d['Strategy']=='g,0|0,g') & (d['CmeetsN'].isin(todrop))].index,inplace=True)
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
def plotFigure(DF, base_tag, outdirectory, doSort=True):
    """
    Generalized plotting function with dynamic figure width based on BB columns.
    """
    if doSort:
        DF = DF.sort_values(['fit', 'Strategy'], ascending=[True, True], ignore_index=True)
        print("Sorting applied in reverse order.")
    else:
        print("Original order retained.")

    N = len(DF)
    DF['count'] = 0
    DF['SelfSelf'] = DF['NmeetsN']

    # Determine BB columns
    possible_parts_of_BB_to_display = ['CmeetsN', 'NmeetsC', 'NmeetsN']
    BB_col_names = [
        part for part in possible_parts_of_BB_to_display
        if part in DF and not np.all(DF[part] == '0' * len(DF[part].iloc[0]))
    ]
    #!!!!!!!!
    BB_col_names = ['CmeetsN', 'NmeetsC']

    strategy_info = setStrategyInfo()

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
    #show_lead8  = False
    
    
    # Create figure
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)

    # Create axes
    axs_BB, ax_L8, ax_ESS = create_axes(fig, fig_width, fig_height, BB_col_names, show_lead8=show_lead8)

    # Plot BB columns
    if 'inary' in base_tag:
        show_labels=True
    else:
        show_labels=False

    plot_bb_columns(axs_BB, DF, BB_col_names,show_labels)

    # Plot Lead8 column
    if show_lead8:
        plot_lead8_column(ax_L8, DF, strategy_info)

    # Plot ESS pane
    plot_ess_pane(ax_ESS, DF, strategy_info)

    # Save figure
    suffix = "" if doSort else "_as_is"
    base_tag = base_tag.removesuffix(".txt")
    outfile = f"{outdirectory}/{base_tag}{suffix}.png"
    plt.savefig(outfile, dpi=600, bbox_inches="tight")
    print(f'Saved plot to: {outfile}')
    plt.close(fig)
###########
####################

def plot_bb_columns(axs_BB, DF, BB_col_names,show_labels=True):
    """
    Plot the Big Brother (BB) columns and dynamically add the header above the "CmeetsN" column.
    """
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
        plot_matrix_header(header_ax, cell_size,show_labels)  # Call header plotting function


    for i, part in enumerate(BB_col_names):
        ax = axs_BB[i]
        for spine in ax.spines.values(): spine.set(linewidth=2.0, color='gray') # thick borders
        color_map = {'+': [0.64, 0.90, 0.21],  # Green
                     '-': [0.3, 0.6, 1.0],     # Blue
                     '0': whiteish}            # White

        # Build and plot the color matrix for the main content
        strings = DF[part].values
        color_matrix = np.array([
            np.array([color_map[char] for char in s], dtype=float) for s in strings
        ])
        ax.imshow(color_matrix, aspect='auto', interpolation='nearest', origin='upper')

        # Set title and remove ticks
        if part=='CmeetsN' : label='Donor\'s change'
        elif part=='NmeetsC' : label='Receiver'
        else: label='random encounters'
        ax.set_xlabel(label, fontsize=11, labelpad=10, ha='center', va='top')
        # ax.set_title(part, fontsize=9, rotation=0)
        ax.set_xticks([])
        ax.set_yticks([])

        # Add tick marks for specific columns
        if part == 'CmeetsN':
            for row, strat in enumerate(DF['Strategy'].values):
                n0, n1 = strat.split('|')
                actions = n0.split(',') + n1.split(',')
                slots = [0,1,4,5]
                for counter, act in enumerate(actions):
                    if act == '0': # no help given, both parties S0
                        ax.text(slots[counter], row, '\u2713', color='black', ha='center', va='center', fontsize=10)
                    if act == 'g': # no help given, both parties S0
                        ax.text(slots[counter]+2, row, '\u2713', color='black', ha='center', va='center', fontsize=10)
                
                
        if part in ['CmeetsN','NmeetsC']:
            for col_pair in range(1,4): # subtle vertical lines for col pairs
                ax.axvline(x=2 * col_pair - 0.5, color='gray', linewidth=0.5, alpha=0.5)
        else:
            for col_pair in range(1,2):
                ax.axvline(x=2 * col_pair - 0.5, color='gray', linewidth=0.5, alpha=0.5)

#####################################

def plot_lead8_column(ax_L8, DF, strategy_info):
    """
    Plots the Lead8 column with strategy names and gray annotations.
    """
    ax_L8.set_xlabel('Strategy', fontsize=11, rotation=0, labelpad=10, va='top')
    #ax_L8.text(0.0, -1, '\u2713\u2713     \u2713\u2713', fontsize=7)
    ax_L8.text(0.0, -1, r'$\checkmark$ as text', fontsize=7)

    # Create the Lead8 dictionary within this function
    lead8 = createLeading8()
    for k, v in lead8.items():
        match_view = DF[
            (DF['Strategy'] == v['strategy']) &
            (DF['CmeetsN'].apply(mapScoresRuleToBinary) == v['CmeetsN'])
        ]
        lead8[k]['indices'] = match_view.index.tolist()

    # Plot strategy names
    for row, strat in enumerate(DF['Strategy'].values):
        ax_L8.text(0.0, row, strategy_info[strat]['nickname'],  # was 'symbol' 
                   color=strategy_info[strat]['color'], 
                   ha='left', va='center', fontsize=8,
                   fontproperties=fixed_width_font)
    
    # Plot Lead8 annotations ('L1' and so on)
    for k, v in lead8.items():
        for i in v['indices']:
            ax_L8.text(0.9, i, v['nick'], 
                       color='black', ha='left', va='center', fontsize=6, 
                       bbox=dict(facecolor=whiteish, 
                             edgecolor='gray', 
                             linewidth=2.0))
    
    ax_L8.set_xticks([])
    ax_L8.spines[['left', 'right', 'bottom']].set_visible(False)

#####################################

def plot_ess_pane(ax_ESS, DF, strategy_info):
    """
    Plots the ESS pane showing fitness lines and cooperation levels.
    """
    line_width = max(0.1, min(2, 20 / np.sqrt(len(DF))))  # Scale using square root for gradual thinning
    # Plot ESS fitness lines
    for rank, (fit, strat) in enumerate(zip(DF['fit'][::-1], DF['Strategy'][::-1])):
        colr = strategy_info[strat]['color']
        #ax_ESS.plot([fit, fit], [rank, rank + 1], color=colr, linewidth=6, solid_capstyle='butt')
        ax_ESS.plot([0, fit], [rank + 0.5, rank + 0.5], color=colr, linewidth=line_width, solid_capstyle='butt')
        if fit == 0.0:
            ax_ESS.plot([0, 0.02], [rank + 0.5, rank + 0.5], color=colr, linewidth=line_width, solid_capstyle='butt')


    # Configure the ESS axis
    ax_ESS.xaxis.set_ticks_position('top')
    ax_ESS.set_xlim(0.0, 1.0)
    ax_ESS.set_xlabel('Cooperation', fontsize=11, labelpad=10, va='top')

    ax_ESS.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_ESS.set_yticks([])
    ax_ESS.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
    ax_ESS.set_ylim(0, len(DF))
    ax_ESS.spines[['left', 'right', 'bottom']].set_visible(False)

    # Adjust xtick label size
    ax_ESS.tick_params(axis='x', labelsize=8)  # Smaller font size for xtick labels

    ax_ESS.text(1.0, len(DF)/2, f'({len(DF)} rows)',  
                color='gray', ha='right', va='center', fontsize=7,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

####################################

from matplotlib.gridspec import GridSpec

def create_axes(fig, fig_width, fig_height, BB_col_names, show_lead8=True, ess_ratio=3, header_height_factor=0.06, cell_height=None):
    """
    Creates axes for the BB columns, optional Lead8 column, ESS pane, and header.
    The `cell_height` ensures consistent absolute height for the header matrix cells.
    """
    bot, top = 0.1, 0.93  # Main plot height bounds
    xcurrent = 0.05
    axs_BB = []
    lead8_width = 0.8

    # Add BB column axes
    for part in BB_col_names:
        if part in ["CmeetsN","NmeetsC"]:
            axs_BB.append(fig.add_axes([xcurrent, bot, 2 / fig_width, top - bot]))
            xcurrent += (2 + 0.22) / fig_width
        else:
            axs_BB.append(fig.add_axes([xcurrent, bot, 1 / fig_width, top - bot]))
            xcurrent += (1 + 0.22) / fig_width
        
    # Add Lead8 column axis if needed
    ax_L8 = None
    if show_lead8:
        ax_L8 = fig.add_axes([xcurrent, bot, lead8_width / fig_width, top - bot], yticklabels=[], sharey=axs_BB[0])
        xcurrent += (lead8_width + 0.22) / fig_width

    # Add ESS pane axis
    ax_ESS = fig.add_axes([xcurrent, bot, ess_ratio / fig_width, top - bot], yticklabels=[])

    return axs_BB, ax_L8, ax_ESS


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
    row_label = ['donor\'s score \u2265 1? \u2192', 'donor gives help? \u2192', 'receiver score \u2265 1? \u2192']
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

import sys, os, matplotlib, argparse, re
#matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.close('all')
plt.interactive(False)
import matplotlib.colors as mcolors
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d import Axes3D
import string, math, os
from plotting_funcs import *
low_memory = False

'help given? (g) \u2192',
# Setup argparse
parser = argparse.ArgumentParser(description="Process and plot results from data files")
parser.add_argument('--directory', '-d', default='./data-default', help='Directory containing data files')
parser.add_argument('--onefile', '-f', default=None, help='single datafile (in that dir but w/o path)')
parser.add_argument('--threshold', '-t', default=0.0, help='ignore fitnesses below this')
parser.add_argument('--keepsymmetries', '-s', default=False, action="store_true", help='keep symmetries')
#parser.add_argument('--negative', '-n', action="store_true", help='include negative scores')
parser.add_argument('--old', '-o', action="store_true", help='old score file')
args = parser.parse_args()

directory_path = args.directory
files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f)) and f != 'Figs']

theNames = [f for f in files]
if args.onefile != None: # if a single file is specified, just do that one.
    theNames = [args.onefile]
   
# Define the path for the 'Figs' subdirectory within the data directory
figs_directory = os.path.join(directory_path, 'Figs')
if not os.path.exists(figs_directory):
    os.makedirs(figs_directory)

for base_tag in theNames: 
    print("\n\tWorking on ",base_tag)       
    infile = os.path.join(directory_path, base_tag)
    if not os.path.isfile(infile):
        print("!!Ooops, no such file as ", infile)
        break

    if 'NmeetsC' in base_tag: 
        NmeetsC = True
    else:
        NmeetsC = False

    # Tedious, but I need to extract BENEFIT and COST values from the file,
    # just in order to scale the "fitness" plot.    
    REPUTATION = None

    with open(infile, 'r') as file:
        # Read the first few lines of the file (adjust the number as needed)
        lines_to_search = [next(file) for _ in range(2)]
        benefit, cost = None, None
        # Use regex to find 'BENEFIT' and the next number within those lines
        #if 'inary' in infile: REPUTATION="Binary"
        #elif 'okens' in infile: REPUTATION="Tokens"
        #elif 'cores' in infile: REPUTATION="Scores"
        for line in lines_to_search:
            if 'inary' in line: REPUTATION="Binary"
            elif 'okens' in line: REPUTATION="Tokens"
            elif 'cores' in line: REPUTATION="Scores"
            
            if 'BENEFIT' in line:
                match = re.search(r'BENEFIT\s+(\d+\.\d+|\d+)', line)
                if match:
                    benefit = float(match.group(1))
            if 'COST' in line:
                match = re.search(r'COST\s+(\d+\.\d+|\d+)', line)
                if match:
                    cost = float(match.group(1))
                    
            # Exit the loop if both values are found
            if benefit is not None and cost is not None and REPUTATION is not None:
                print("found benefit and cost: ",benefit, cost)
                break

    if REPUTATION is not None:
        print("Reputation type is ",REPUTATION)
    else:
        print("Cannot tell which REPUTATION type this is")
    
    # create a new subdirectory for this particular file's figures, if necessary
    #outdirectory = os.path.join(figs_directory, base_tag)
    #if not os.path.exists(outdirectory):
    #    os.makedirs(outdirectory)
    outdirectory = figs_directory
    
    print("Writing into directory ", outdirectory)

    colnames=['CmeetsN', 'NmeetsC', 'NmeetsN','Strategy','fit', 'w0','w-1', 'w1','a','b','c', 'd']
    #colnames=['CmeetsN', 'NmeetsC', 'NmeetsN','CmeetsC','Strategy','fit', 'w0','w-1', 'w1','a','b','c', 'd']
    # Create a dictionary for dtype, assuming all columns are float except for the specified string columns
    dtype_dict = {i: 'float' for i in colnames}
    for col in [0, 1, 2, 3]:
        dtype_dict[colnames[col]] = 'str'

    DF = pd.read_csv(infile, comment='#', header=None, delimiter=r'\s+', names=colnames, dtype=dtype_dict, engine='python')

    if DF.empty:
        print('DataFrame is empty!')
        continue

    DF['fit'] = DF['fit']/(benefit-cost) # normalises 'fitness', since benefit-cost is the max possible fitness.            
    
    DF = DF[DF['fit'] >= float(args.threshold)]  # remove rows where fitness is "low"
    DF.reset_index(drop=True,inplace=True)
        
    if not args.keepsymmetries and REPUTATION=="Binary":
        DF = removeBinarySymmetries(DF,NmeetsC)
    elif not args.keepsymmetries and REPUTATION=="Scores":    
        DF = removeScoresSymmetries(DF)


    # Convert the null_row to a DataFrame and concatenate it into the original as first row.
    # Add a "null" row at the start, consisting of the do-nothing strategy, and do-nothing BB.
    #null_row = {
    #    'CmeetsN': '00000000', 'NmeetsC': '00000000', 'NmeetsN': '0000',
    #    'Strategy': '0,0|0,0','fit': 0.0,'w0': 0.0,'w-1': 0.0,'w1': 0.0,
    #    'a': 0.0,'b': 0.0,'c': 0.0,'d': 0.0,'nickname': 'null'
    #}
    #null_DF = pd.DataFrame([null_row])
    #DF = pd.concat([null_DF, DF], ignore_index=True)

    plotFigure(DF.copy(deep=True), base_tag, outdirectory, doSort=False)
    plotFigure(DF.copy(deep=True), base_tag, outdirectory, doSort=True)
    
    #DF2 = DF.copy(deep=True)
    #plotInOrder(DF, base_tag+'_InOrder', outdirectory)
    #plotByRank(DF2, base_tag, outdirectory)
    #if REPUTATION == "Scores" or REPUTATION == "Tokens":
    #    plotGridW1vals(DF, base_tag, outdirectory)
    #plotGridABCvals(DF, base_tag, outdirectory)



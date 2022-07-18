import numpy as np
import numpy.random as rng
import copy, sys, os, shutil
from graphviz import Digraph
import argparse

from exchange_funcs import *
np.set_printoptions(precision=5)


#==============================================================================

if __name__ == '__main__':

        
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Three groups of system parameters.
    parser.add_argument('--VAL2A', action='store', type=float, default=4., help='VAL2A is val of obj2 to A (cf. default val of obj1 to A is 1).')
    parser.add_argument('--VAL1B', action='store', type=float, default=4., help='VAL1B is val of obj1 to B (cf. default val of obj2 to B is 1).')
    parser.add_argument('--VAL1A', action='store', type=float, default=1., help='VAL1A is val of obj1 to A.')
    parser.add_argument('--VAL2B', action='store', type=float, default=1., help='VAL2B is val of obj2 to B.')
    
    parser.add_argument('-m','--allowMULTIHOLDS', action='store_true', default=False, help='whether or not diff agents hold same thingy')
    parser.add_argument('--allowBREAK', action='store_true', default=False, help='whether or not can break a hold')
    parser.add_argument('--noAGENTHOLDS', action='store_true', default=False, help='whether or not agents can hold each other (ooh err)')
    parser.add_argument('--NUMHANDS', action='store', type=int, default=3, help='number of hands (2 or 3)')
    parser.add_argument('-p','--forcePASSINGB',  action='store_true', default=False, help='when set, agent B will always pass!')
    
    parser.add_argument('-g','--GAMMA', action="store", type=float, default=0.99, help='discounting of future returns')
    parser.add_argument('-a','--ACTIONNOISE', action='store', type=float, default=0.01, help='noise on transitions')
    parser.add_argument('-t','--TEMPERATURE', action='store', type=float, default=-999, help='softmax temperature, puts softmax noise on action selection. If <= 0.0, defaults to vanilla greedy.')
    parser.add_argument('-e','--EXITRATE', action='store', type=float, default=1.0, help='relative speed of exit attempts (< 1)')
    parser.add_argument('-b','--BETA', action="store", type=float, default=0.5, help='relative speed of A vs B (in [0,1] and 0.5 is equal speeds)')
    parser.add_argument('-q','--QNOISE', action="store", type=float, default=0.01, help='start value for qnoise')
    
    parser.add_argument('-B','--PAINtoBE',    action='store', type=float, default=-0.0, help='cost just for being here (opportunity cost)')
    parser.add_argument('-R','--PAINtoBREAK', action='store', type=float, default=-10.0, help='cost for trying to break an EXISTING hold')
    parser.add_argument('-G','--PAINtoGRAB',  action='store', type=float, default=-0.1, help='cost for initiating a NEW hold')
    parser.add_argument('-H','--PAINtoHOLD',  action='store', type=float, default=-0.0, help='cost for maintaining an OLD hold')
    parser.add_argument('-F','--PAINtoFAIL',  action='store', type=float, default=-10.0, help='cost for trying an action that FAILS')
    
    # algorithmic parameters
    parser.add_argument('-i','--VIitns', action="store", type=int, default=1000, help='the number of iterations of Value Iteration to run')
    parser.add_argument('-r','--BIGTEST', action="store_true", help='if set, runs everything tonnes of times and collates outcomes')
    parser.add_argument('-v','--verbose', action="store_true", help='if set, plot V and final Q')
    parser.add_argument('-s','--SYMMETRIZE', action="store_true", help='if set, V_A and V_B forced to be symmetric. ')
    parser.add_argument('-n','--NAME', action="store", default='test', help='name to tag image files with')
    args = parser.parse_args()
    
    assert(args.NUMHANDS in [2,3])
    twohands = (args.NUMHANDS == 2)
    
    # I need a generator of ALL POSSIBLE states. 
    # The strings read as [a0,a1,a2,b0,b1,b2]= [A holds a, A holds B, A holds b, B holds a, B holds A, B holds b]
    # Does not need to be very efficient :)
    counter = 0
    index2state = {} # a map from an integer index to a state like [1,0,0,0,1,0]
    statestr2index = {} # a map back from a state like [1,0,0,0,1,0] to its index (like a hash)
    for a0 in [0,1]:
        for a1 in [0,1]:
            for a2 in [0,1]:
                # now look at possible locks for the B agent
                if twohands and (a0 and a1 and a2): continue
                else:
                    for b0 in [0,1]:
                        if (b0 and a0) and (not args.allowMULTIHOLDS): continue
                        else: 
                            for b1 in [0,1]:
                                for b2 in [0,1]:
                                    if (b2 and a2) and (not args.allowMULTIHOLDS): continue
                                    else:
                                        if twohands and (b0 and b1 and b2): continue
                                        else:
                                            index2state[counter] = [a0,a1,a2,b0,b1,b2]
                                            statestr2index[str([a0,a1,a2,b0,b1,b2])] = counter
                                            counter = counter + 1
    # And there is an "exit" state. exit stays exit under all actions, and positive
    # rewards are zero except when entering the exit state for the first time. 
    EXITSTATE = [-1,-1,-1,-1,-1,-1]
    index2state[counter] = EXITSTATE
    statestr2index[str(EXITSTATE)] = counter
    #for i,s in index2state.items():
    #    print(i, s)
    
    # actions have names, to make more readable. I use a dictionary, but it's
    # ugly in that elsewhere it will be ASSUMED that these keys are actually 
    # the integers starting at 0, with no gaps :( 
    actionNames = {0:'TOGGLE a',1:'TGL other',2:'TOGGLE b',3:'EXIT',4:'PASS'} 
    # 'TGL obj1' means agent (tries) toggle hold on the item 'obj1', etc.
    # 'EXIT' means agent tries to terminate the interaction
    # 'PASS' means agent does nothing this round
    nacts = len(actionNames)
        
    """
    NOW THE "PAIRED" AGENTS' VALUE ITERATION.
    """
    # collect all the parameters of the MDP together for compactness, to pass in to VI.
    world = MDP_World(index2state, statestr2index, actionNames, EXITSTATE, args)
    #world_params.test_VI()
    
    #do_big_graph(index2state, world_params, 'biggie')  # such a pity this doesn't work!!!
    
    #########################################################################
    # Okay, do it once and make a plot.......
    #values, stored_V_A, stored_V_B = alt_run_Value_Iteration(world_params, args.VIitns, QNOISE=0.1) 
    values, stored_V_A, stored_V_B = run_Value_Iteration(world, args.VIitns, QNOISE=args.QNOISE)
    [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts] = values
    
     
    # PLOT WHAT HAPPENED
    #start = [0,0,0,0,0,1]
    start = [1,0,0,0,0,1]
    #start = index2state[30]
    
    # First, we prepare an empty directory to put the results into
    if os.path.isdir(world.NAME):  shutil.rmtree(world.NAME)
    os.makedirs(world.NAME)
    world.NAME = os.path.join(world.NAME,args.NAME)

    if args.verbose:
        print('Verbose mode')
        
        world.plot_rewards(actionNames,world.NAME)
        world.plot_transitions(actionNames,args.NAME)
        plot_VIconvergence(stored_V_A, stored_V_B, index2state, world)
        plot_rollout(start, EXITSTATE, 20, Q_toA_Aacts, Q_toB_Bacts, world)
        #plot_Qs(Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts, world, actionNames)
        plot_QV(Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts, world, actionNames, stored_V_A)
        

 
    if args.BIGTEST:
        #########################################################################
        # Run VI lots of times, collect ALL the unique policies found, 
        # and show each one's gametree, Q's and V's.
        
        """ Here is an alternative that gives the directory a long name incorporating all the param vals!
        longname = 'GA{0:.3f}_BE{1:.3f}_HI2A{2:.1f}_HI1B{3:.1f}_LO1A{4:.1f}_LO2B{5:.1f}_BRK{6:.1f}_GRB{7:.3f}_HLD{8:.3f}_BE{9:.3f}_FL{10:.3f}_NOI{11:.3f}_AB{12:1d}_NH{13:1d}_AMH{14:1d}_AAH{15:1d}_EX{16:.3f}'.format(
                world_params.GAMMA,world_params.BETA,float(world_params.VAL2A),
                float(world_params.VAL1B),float(world_params.VAL1A),
                float(world_params.VAL2B),-world_params.PAINtoBREAK,-world_params.PAINtoGRAB,
                -world_params.PAINtoHOLD,-world_params.PAINtoBE,-world_params.PAINtoFAIL, 
                world_params.ACTIONNOISE, world_params.allowBREAK, world_params.NUMHANDS, 
                world_params.allowMULTIHOLDS,world_params.noAGENTHOLDS, world_params.EXITRATE)
        
        longname = os.path.join(longname,args.NAME)
        # And you'd have to prepare an empty directory of this name etc.
        """
        
        # Okay here goes..........
        unique_trees = []
        counter = {}
        VQsaved = {}
        policies = {}
        print('okay here we go **************************************************')
        unique_trees = set()
        for trial in range(100):
            values, stored_V_A, stored_V_B = run_Value_Iteration(world, args.VIitns, QNOISE=args.QNOISE)
            [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts] = values    
            
            # and look at the consequences
            policyA = Q_toA_Aacts.argmax(1)
            
            # this is B's policy but reordered "as if it was in A's position".
            policyB = Q_toB_Bacts.argmax(1) 
            # store it, with a hash, so we can look for the sets.
            ahash = do_graph(start, EXITSTATE, Q_toA_Aacts, Q_toB_Bacts, V_A, V_B, world, SILENTMODE=True)

            unique_trees.add(ahash)
            ### Don't hash the entire policy: just hash the actual tree!  
            ### (e.g. we don't care about variations in states that are not visited)
            policies[ahash] = [policyA,policyB]
            if (ahash in counter.keys()):
                counter[ahash] = counter[ahash] + 1 
            else:
                counter[ahash] = 1
                VQsaved[ahash] = values
    
        print('trees for all the unique trees!')
        originalName = world.NAME
        for i,h in enumerate(unique_trees):
            print('{0}\n{1}'.format(policies[h][0], policies[h][1]))
            print('this pair happened {0} times \n'.format(counter[h]))
            # change name
            world.NAME = '{0}_happened_{1}_times'.format(world.NAME, counter[h])
            #if os.path.isfile(os.path.join(world_params.NAME,NAME+ '_rollout.pdf')):
            #    NAME = NAME+'a'
            
            #world_params.NAME = NAME 
            #os.path.join(longname,NAME) # What was the intent of this?
            
            # make the figures
            # UNPACK stuff first....
            values = VQsaved[h]
            [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts] = values

            h = do_graph(start, EXITSTATE, Q_toA_Aacts, Q_toB_Bacts, V_A, V_B, world)  
            #plot_VIconvergence(stored_V_A, stored_V_B, index2state, world)
            #plot_Qs(Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts, world, actionNames)
            #plot_rollout(start, EXITSTATE, 20, Q_toA_Aacts, Q_toB_Bacts, world)
            #do_big_graph(EXITSTATE, Q_toA_Aacts, Q_toB_Bacts, V_A, V_B, world)
            world.NAME = originalName # just changing it back again. Cheap & cheesy.           
    else:
        do_graph(start, EXITSTATE, Q_toA_Aacts, Q_toB_Bacts, V_A, V_B, world)
        do_big_graph(EXITSTATE, Q_toA_Aacts, Q_toB_Bacts, V_A, V_B, world)


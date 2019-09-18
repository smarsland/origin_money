import numpy as np
import numpy.random as rng
import pylab as pl
from pytest import approx

np.set_printoptions(precision=3)

"""
A Policy is a (2x2) matrix, each elt being a tuple(dh, ds).
First indices are h and s
h is "can help", binary, set with probability BETA every step new.
s is score: integer from 0 to upper limit nsl (ideally not reached)
Uppercase S is cartoon of score: S = istrue(s>=1)

The tuple denotes the proposal to make: (dh, ds_SELF, ds_OTHER)
Eg:

 Self's
 cartoon 
 (h,S)  : Proposal      example
-------------------
 (0,0)  :  (dh,dsSelf,dsOther)        (0,0,0)
 (0,1)  :  (dh,dsSelf,dsOther)        (-,+,-)
 (1,0)  :  (dh,dsSelf,dsOther)        (+,-,+)
 (1,1)  :  (dh,dsSelf,dsOther)        (+,-,+)

If the example shown was an ESS, and even better if there was a "road" to it among feasible mutations, then that's an explanation of money: it's a social norm that can arise all by itself.
"""


### CLASSES ==================================================================


class Strategy():
    """
    """
    def __init__(self, index, dh_prop, dsSelf_prop, dsOther_prop):
        self.index = index
        self.dh_prop = dh_prop  # a proposal for dh
        self.dsSelf_prop = dsSelf_prop
        self.dsOther_prop = dsOther_prop
        #nb. index order is always going to be (helping, scoring)
        
        # Now give it a readable name of some sort
        #self.name = '{0}{1}'.format(np.ravel(dh_prop),np.ravel(ds_prop)).replace(' ','')
        self.name='[{0:3d}{1:3d}{2:3d}{3:3d}][{4:3d}{5:3d}{6:3d}{7:3d}][{8:3d}{9:3d}{10:3d}{11:3d}]'.format(
                dh_prop[0,0],dh_prop[0,1],dh_prop[1,0],dh_prop[1,1],
                dsSelf_prop[0,0],dsSelf_prop[0,1],dsSelf_prop[1,0],dsSelf_prop[1,1],
                dsOther_prop[0,0],dsOther_prop[0,1],dsOther_prop[1,0],dsOther_prop[1,1],
                )
        self.name='[[{0:3d}{1:3d}{2:3d}][{3:3d}{4:3d}{5:3d}]],[[{6:3d}{7:3d}{8:3d}][{9:3d}{10:3d}{11:3d}]]'.format(
                dsSelf_prop[0,0],dh_prop[0,0],dsOther_prop[0,0],
                dsSelf_prop[1,0],dh_prop[1,0],dsOther_prop[1,0],
                dsSelf_prop[0,1],dh_prop[0,1],dsOther_prop[0,1],
                dsSelf_prop[1,1],dh_prop[1,1],dsOther_prop[1,1],
                )
                                
    def __str__(self):
        return self.name


### METHODS ========================================================


def find_agreed_changes(strat1, strat2, args):
    """
    werdz here 
    """
    top = args.nsl-1 # the highest allowed score level.
    
    # dh1 stores the changes to h1 that will result from
    # agent one being in state (h1,s1) and agent 2 in state (h2,s2),
    # and similarly for ds1 (and for dh2, ds2)
        
    ds1 = np.zeros((2,args.nsl,2,args.nsl),dtype=int)
    dh1 = np.zeros((2,args.nsl,2,args.nsl),dtype=int)
    ds2 = np.zeros((2,args.nsl,2,args.nsl),dtype=int)
    dh2 = np.zeros((2,args.nsl,2,args.nsl),dtype=int)
    for h1 in [0,1]:
        for s1 in range(args.nsl):
            S1 = 1*(s1>0)
            for h2 in [0,1]:
                for s2 in range(args.nsl):
                    S2 = 1*(s2>0)

                    # But they need to accept each other or it'll be zero! 
                    # As well all know, there's more than one way to be unacceptable.

                    # 1. They have to be in perfect agreement, both for dh and ds suggestions.
                    # This isn't equal, it's being opposite / complement to.
                    h_agree = (strat1.dh_prop[h1,S1] + strat2.dh_prop[h2,S2] == 0) # do they agree on helping?
                    
                    #ds1_agree = (strat1.dsSelf_prop[h1,S1] == -strat2.dsSelf_prop[h2,S2])
                    ds1_agree = (strat1.dsSelf_prop[h1,S1] == strat2.dsOther_prop[h2,S2]) # do they agree on ds1?
                    ds2_agree = (strat1.dsOther_prop[h1,S1] == strat2.dsSelf_prop[h2,S2]) # and agree on ds2?
                    ds_agree = ds1_agree and ds2_agree
                    
                    # 2a. if help is asked for, it has to be available (else one party will reject as unmet)
                    dh1_possible, dh2_possible = True, True
                    if (strat1.dh_prop[h1,S1] == 1 and (h2==0)): 
                        dh1_possible = False
                    if (strat2.dh_prop[h2,S2] == 1 and (h1==0)): 
                        dh2_possible = False
                    dh_possible = dh1_possible and dh2_possible
                    
                    # 2b. signal changes can't be illegal (else one party will reject as unmet)
                    ds1_possible, ds2_possible = False, False
                    if 0 <= s1 + strat1.dsSelf_prop[h1,S1]: # <= top: 
                        ds1_possible = True
                    if 0 <= s2 + strat2.dsSelf_prop[h2,S2]: # <= top: 
                        ds2_possible = True
                    ds_possible = ds1_possible and ds2_possible


                    if (h_agree and ds_agree and dh_possible and ds_possible):
                        dh1[h1,s1,h2,s2] = strat1.dh_prop[h1,S1]
                        dh2[h1,s1,h2,s2] = strat2.dh_prop[h2,S2]
                        # One last check, that only applies to scores though:
                        # we don't do s changes that would "top out" (but DO allow the help to flow)
                        if (s1+strat1.dsSelf_prop[h1,S1]<=top) :
                            ds1[h1,s1,h2,s2] = strat1.dsSelf_prop[h1,S1] 
                        if (s2+strat2.dsSelf_prop[h2,S2]<=top) :
                            ds2[h1,s1,h2,s2] = strat2.dsSelf_prop[h2,S2] 

    # Okay! Now we've got the signal changes (and the help provision) for all
    # pairs of states.
    return dh1,ds1,dh2,ds2


def run_strategy(common, w_init, args, VERBOSE=False):                
    """ 
    Werdz here.
    """
    #     We assume strat1 makes up entire population here, as follows:
    dh1,ds1,dh2,ds2 = find_agreed_changes(common, common, args)
    # Nb. I don't think dh2 or ds2 will be used inside this method.
    
    #new_s1 = np.zeros((2,args.nsl,2,args.nsl),dtype=int)
    #for h1 in [0,1]:
    #    for s1 in range(args.nsl):
    #        for h2 in [0,1]:
    #            for s2 in range(args.nsl):
    #                new_s1[h1,s1,h2,s2] = s1 + ds1[h1,s1,h2,s2]
    
    # THIS MUCH MORE COMPACT VERSION IS EQUIVALENT: 
    new_s1 = np.swapaxes(np.ones((2,args.nsl,2,args.nsl),dtype=int)*np.arange(args.nsl), 1,3) + ds1
    
    assert((new_s1 >= args.nsl).any() == False)
    assert((new_s1 < 0).any() == False)
    
    initSignalPerAgent = np.sum(np.ravel(w_init) * np.arange(args.nsl))
    if VERBOSE: 
        print('init  ',w_init)
        print("Initial signal/agent = {0}".format( initSignalPerAgent ))    
    assert(w_init.sum() == approx(1.0))
    w = np.copy(w_init)

    w_seq = [np.copy(w)]
    pairDensity = np.zeros((2,args.nsl,2,args.nsl),dtype=float)
    for step in range(args.itns):
        outer = np.outer(w,w)
        for h1 in [0,1]:
            for h2 in [0,1]:
                factor = (args.BETA**(h1+h2))*((1-args.BETA)**(2-h1-h2))
                pairDensity[h1,:,h2,:] = factor*outer
        assert(np.abs(pairDensity.sum() == approx(1.0)))
        #assert(np.abs(pairDensity.sum() - 1.0) < 0.000001)
        # Okay it's close. But make it exactly 1, to avoid compound errors.
        pairDensity = pairDensity / pairDensity.sum()
    
            
        for k in range(args.nsl):
            # count all the pairDensity slots where new_s1_full == k
            w[k] = pairDensity[(new_s1 == k)].sum()
        w_seq.append(np.copy(w))
    assert(w.sum() == approx(1.0))
    cash =np.sum(np.ravel(w) * np.arange(args.nsl))
    #assert(cash == approx(initSignalPerAgent))  
    # I had to remove the above assertion, due to possible loss when signals "top out".
    # See the comment in find_agreed_changes().
    
    helpingRate  = pairDensity[(dh1 == -1)].sum()
    helpedRate   = pairDensity[(dh1 == 1)].sum()
    # Is this actually wrong...?
    # if someone negotiates to give help to one who already has h=1,
    # that's fine but the receiver with h=1 should not be getting any payoff.
    # ie. the interaction "happens", but the recipient gets no PAYOFF.
    pp = pairDensity[:,:,1,:] # pp is all the densities where player2 has surplus
    dd = dh2[:,:,1,:]  # dd is all the player2 dh values, where player2 has surplus
    helpingRate = pp[dd==-1].sum()  # looks good: all the times player2 actually helped.

    pp = pairDensity[:,:,0,:] # densities of pairs where player 2 was in need.
    dd = dh2[:,:,0,:]  # all the player2 dh vals, when they were in situation of need.
    helpedRate = pp[dd==1].sum() # sum the densities where they were in need, and got helped.
    # so that looks good too, AFAIK.

    return(helpingRate, helpedRate, w, w_seq)


def run_rare_strategy_amongst_common(rare, common, w_common, args, VERBOSE=False):                
    """
    Hmmmm, this seems to assume that w_common has already been arrived at.
    It then goes about seeing what w_rare is going to end up as, by running
    the specified number of iterations of it, without changing w_common now.
    
    That's problematic really. 1, I can't check for rarity = 0.1, say.
    2. What's the model...? Seems like the common gets time to equilibrate, and
    THEN rare mutant arrives and has a shot. Well okay actually that's not so bad.
    """
    dh1,ds1,dh2,ds2 = find_agreed_changes(common, rare, args)
    # yep. All the changes, in all the encounters.

    new_s2 = np.ones((2,args.nsl,2,args.nsl),dtype=int) * np.arange(args.nsl)
    # huh?! Why start at ones? Oh, the arange... Fine. The status quo.
    new_s2 = new_s2 + ds2
    
    initSignalPerAgent = np.sum(np.ravel(w_common) * np.arange(args.nsl))
    if VERBOSE: 
        print('init  ',w_common)
        print("Initial signal/agent = {0}".format( initSignalPerAgent ))    
    assert(w_common.sum() == approx(1.0))
    w = np.copy(w_common)
    w_seq = [np.copy(w)]
    # python has made me paranoid, hence all the sad / maybe redundant copying
    # Looks like I'm saving all the score distributions that happen over a series of 
    # encounters. That's purely for the graphics - we return the whole series in 
    # order to display it, but it's not used for anything else.
    
    pairDensity = np.zeros((2,args.nsl,2,args.nsl),dtype=float)
    # oh I see, I'm making the population model include just these two strategies.
    
    for step in range(args.itns):
        outer = np.outer(w_common, w)
        for h1 in [0,1]:
            for h2 in [0,1]:
                factor = (args.BETA**(h1+h2))*((1-args.BETA)**(2-h1-h2))
                # WTF?? Should have commented this - it's inscrutable.
                # Ah, it's just making some R-R pairs, some R-D, some D-R and some D-D.
                # whereas simpler model just makes them all 1/4.
                # If BETA is 0.5 then pairDensity is just outer then. Fine.
                pairDensity[h1,:,h2,:] = factor*outer
        
        assert(np.abs(pairDensity.sum() == approx(1.0)))
        # Okay it's close. Good to know. But make it exactly 1 just in case.
        pairDensity = pairDensity / pairDensity.sum()
    
        for k in range(args.nsl):
            # count all the pairDensity slots where new_s1_full == k
            w[k]   = pairDensity[(new_s2 == k)].sum()
            # notice w_common does NOT change here - we only look at rare
        w_seq.append(np.copy(w))

    assert(w.sum() == approx(1.0))
    
    pp = pairDensity[:,:,1,:] # everything where h2==1
    dd = dh2[:,:,1,:]
    helpingRate_rare = pp[dd==-1].sum()

    pp = pairDensity[:,:,0,:] # everything where h2==0
    dd = dh2[:,:,0,:]
    helpedRate_rare = pp[dd==1].sum()
    """
    for h1 in [0,1]:
        for h2 in [0,1]:
           #for s1 in range(args.nsl):
           #     for s2 in range(args.nsl):
           print('h1={0}  h2={1}:'.format(h1,h2))
           print(pairDensity[h1,:,h2,:])
           print(pairDensity[h1,args.nsl-1,h2,1]) 
    print('wealth of rare: ',w)
    """    
               
    if VERBOSE:
        print('end:',w)
    return(helpingRate_rare, helpedRate_rare, w, w_seq)



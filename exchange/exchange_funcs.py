#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 09:51:49 2018

@author: frean
"""
import numpy as np
import numpy.random as rng
import matplotlib.pyplot as plt
import copy, sys, os, shutil
import math
import os.path
from os import path
from graphviz import Digraph, Graph

EPSILON = 0.02 # this determines when two Q values are determined to be a "tie".
myCMAP = 'CMRmap_r' #'RdYlGn'
myCMAP = 'gist_earth_r'
StartStateColour = 'cadetblue'  #options from mpl named colours
EndStateColour = 'yellowgreen' #'mediumseagreen' #'cadetblue' #'limegreen'
imgformat = 'pdf'  # set the format for all the saved figures here. One of svg, png, pdf

# This is horrible to have to use, but it works:
HOME_EXCHANGE_DIR = '/home/marslast/Projects/tradingmodel/exchange'


### CLASSES ===================================================================

class MDP_World():
    """ Just overall parameters relevant to the model, namely:
        the transition probabilities between all states, given actions
            nb. need two of these, one for actions by each player
        the rewards (same size as probs)
            nb. need 4 of these, and there are two actors and two recipients
    """
    def __init__(self, index2state, statestr2index, actionNames, EXIT_STATE, argparams, VERBOSE=False): 
        self.index2state = index2state
        self.statestr2index = statestr2index
        # first, the overall parameters of the simulation
        self.GAMMA = argparams.GAMMA  # discounting
        self.BETA = argparams.BETA    # prob that previous actor does next action too
        self.VAL2A = argparams.VAL2A  # the value to A of obj2 ("the other guy's stuff").
        self.VAL1B = argparams.VAL1B  # the value to B of obj1 ("the other guy's stuff").
        self.VAL1A = argparams.VAL1A # And vice versa
        self.VAL2B = argparams.VAL2B # And vice versa
        # (nb. the corresponding value of "your own stuff" is 1.0)
        self.ACTIONNOISE = argparams.ACTIONNOISE
        self.TEMPERATURE = argparams.TEMPERATURE
        self.SYMMETRIZE = argparams.SYMMETRIZE
        self.EXITRATE = argparams.EXITRATE
        self.NUMHANDS = argparams.NUMHANDS
        self.twohands = (argparams.NUMHANDS == 2)
        self.allowMULTIHOLDS = argparams.allowMULTIHOLDS
        self.noAGENTHOLDS = argparams.noAGENTHOLDS
        self.forcePASSINGB = argparams.forcePASSINGB
        self.NAME = argparams.NAME

        # Note: PAINs should be negative rewards, but it's a (sic) pain to pass in 
        # negatives on command line. So here I just take positive pains and 
        # make them negative.
        self.PAINtoBE  = -abs(argparams.PAINtoBE)
        self.PAINtoBREAK = -abs(argparams.PAINtoBREAK)
        self.PAINtoGRAB = -abs(argparams.PAINtoGRAB)
        self.PAINtoHOLD = -abs(argparams.PAINtoHOLD)
        self.PAINtoFAIL = -abs(argparams.PAINtoFAIL)

        assert(self.VAL2A > 0.0 and self.VAL1B > 0.0)
        assert(self.VAL1A > 0.0 and self.VAL2B > 0.0)
        assert(self.PAINtoBE <= 0.0 and self.PAINtoBREAK <= 0.0 and self.PAINtoGRAB <= 0.0 and self.PAINtoHOLD <= 0.0 and self.PAINtoFAIL <= 0.0)
        
        self.allowBREAK = argparams.allowBREAK
        print("Allow break? ",self.allowBREAK)
        print("Exit rate ",self.EXITRATE)
        if self.forcePASSINGB: print("TEST CASE: Agent B will always pass!")
        # a couple of handy things
        self.nstates = len(statestr2index.keys())
        self.nacts = len(actionNames.keys())
        #VAL = 1.0
        r_A = np.array([argparams.VAL1A, argparams.VAL2A])  # order is obj1, obj2
        r_B = np.array([argparams.VAL1B, argparams.VAL2B])
        self.max_payoff_feasible = max(r_A.sum(), r_B.sum())
    
        # Now for the big tensors saying what happens in every situation...        
        # ie. we set up the physics and the rewards, for all state-state-action options.
        # Nb. the LAST index is the successor state (contrary to usual notation s^prime | s.
        # But I want to broadcast in multiplying by V, so want ordering s,a,s^\prime instead.
        # So just remember the order reads as s,a --> s^\prime   EASY!!

        # Looks like I need to keep FOUR matrices of reward values.
        # Rather than do this with 2 more indices (making 5 in all, which is inhuman), I'm just
        # going to give them 4 names and wear the risk of having replicated (but readable) code.
        # Nearly all vals are zero of course, right now, but keeping all makes the model general.
        self.RewardA_Aacts = self.PAINtoBE * np.ones((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardA_Bacts = self.PAINtoBE * np.ones((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardB_Bacts = self.PAINtoBE * np.ones((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardB_Aacts = self.PAINtoBE * np.ones((self.nstates, self.nacts, self.nstates), dtype=float)
        allR = [self.RewardA_Aacts, self.RewardB_Aacts, self.RewardA_Bacts, self.RewardB_Bacts]

        self.Ptrans_Aacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float) 
        self.Ptrans_Bacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        allP = [self.Ptrans_Aacts, self.Ptrans_Bacts]
        # Reminder: in all these tensors, the order goes [initial state,  action,  successor state]

        assert(actionNames == {0:'TOGGLE a',1:'TGL other',2:'TOGGLE b',3:'EXIT',4:'PASS'})
        assert(EXIT_STATE == [-1,-1,-1,-1,-1,-1])
        # (just to check nothing's fubar there)

    
        for i,s in index2state.items(): # s stands for the initial state
        
            # FIRST, deal with case where everyone has ALREADY left the field of play.
            if (s == EXIT_STATE) : 
                # set rewards and outcomes
                for P in allP:
                    P[s,:,0] = 0.0 # once out, you stay out, regardless of acts, "noise" etc.
                    P[s,:,s] = 1.0 
                for R in allR:
                    R[s,:,:] = 0.0 # once out, nothing hurts
                continue  # and we're outta there
            
            # Pay pains for holding
            self.RewardA_Aacts[:,:,i] += self.PAINtoHOLD * np.sum(s[:3])
            self.RewardA_Bacts[:,:,i] += self.PAINtoHOLD * np.sum(s[:3])
            self.RewardB_Bacts[:,:,i] += self.PAINtoHOLD * np.sum(s[3:])
            self.RewardB_Aacts[:,:,i] += self.PAINtoHOLD * np.sum(s[3:])

            assert(s != EXIT_STATE)
            # NEXT, what happens when the actor (A or B) is trying to toggle hold on an object?     
            for a in [0,2]: # action (and hence affected state) concerns obj1 (=index 0) or obj2 (=index 2)
                assert(actionNames[a] in ['TOGGLE a','TOGGLE b'])
                for ag in ['A','B']: # 0 for case of player A acting, 3 for player B acting.
                    if   ag=='A': p=0
                    elif ag=='B': p=3
                    intended = copy.copy(s)
                    intended[a+p] = 1-s[a+p]
                    isclashA = not(self.allowMULTIHOLDS) and ((s[3] and intended[0]) or (s[5] and intended[2])) 
                    isclashB = not(self.allowMULTIHOLDS) and ((s[0] and intended[3]) or (s[2] and intended[5]))
                    if ag=='A': isclash=isclashA
                    elif ag =='B': isclash=isclashB
                    isbreak = isclash and self.allowBREAK
                    if isbreak: intended[(a+p+3)%6] = 0  # effect on the OTHER player's hold
                    fail = ((intended[0+p]+intended[1+p]+intended[2+p])>2 and self.twohands) or (isclash and not(self.allowBREAK))
                    if not(fail): j = statestr2index[str(intended)]
                    else:         j = statestr2index[str(s)]
                    if   ag=='A': self.Ptrans_Aacts[i,a,j] = 1.0 # very likely to happen
                    elif ag=='B': self.Ptrans_Bacts[i,a,j] = 1.0 
                    # Now the rewards
                    if   ag=='A': R = self.RewardA_Aacts 
                    elif ag=='B': R = self.RewardB_Bacts
                    R[i,a,j] += fail*self.PAINtoFAIL
                    if intended[a+p] and not s[a+p]: # Agent (successfully or not) grabbing 
                        R[i,a,j] += self.PAINtoGRAB
                    # TODO: is this if isbreak or if isclash?
                    if isclash: # broke a hold (nb. not invoked if break attempted but failed?)
                        R[i,a,j] += self.PAINtoBREAK

            """
            SYMPTOMS:
            if you are allowed multiHOLDS, it's okay to have a PAINtoGRAB, even up to 2.0!
            But if multiHOLDS aren't allowed, even 0.0000000001 causes immediate EXIT behaviour.
            
            AND SAME FOR PAINtoBE
            
            Why on earth would that be so? Tiny tiny cost to grabbing... or being....
            I don't get it.
            
            cf.
            PAINtoBREAK is well behaved, ie. has a sensible effect, and only in non-trivial amounts.
            PAINtoHOLD is well behaved too.
            
            Additional worry: what happens to unclaimed goods? Eg if A exits from 001000 
            (leaving obj1 behind), should we reward B with that, assuming it then picks it up?
            This is only an issue because I didn't make possible "A exits, B is still there"...
            as a state. ie. we don't have "Present" for each agent, in the state.
            """

            # AND THEN, what happens when the actor (A or B) is trying to toggle hold on other agent?     
   
            a=1
            assert(actionNames[a] == 'TGL other')
            for ag in ['A','B']: # 0 for case of player A acting, 3 for player B acting.
                if   ag=='A': p=0
                elif ag=='B': p=3
                intended = copy.copy(s)
                intended[a+p] = 1-s[a+p]
                # Note: there is a hack in the next line; we assume that the players aren't holding each other to start with
                fail = ((intended[0+p]+intended[1+p]+intended[2+p])>2 and self.twohands) or self.noAGENTHOLDS
                if not(fail): j = statestr2index[str(intended)]
                else:         j = statestr2index[str(s)]
                if   ag=='A': self.Ptrans_Aacts[i,a,j] = 1.0 # very likely to happen
                elif ag=='B': self.Ptrans_Bacts[i,a,j] = 1.0 
                # Now the rewards
                if   ag=='A': R = self.RewardA_Aacts 
                elif ag=='B': R = self.RewardB_Bacts
                R[i,a,j] += fail*self.PAINtoFAIL
                #R[i,a,j] += (ss[0+p]+ss[1+p]+ss[2+p])*self.PAINtoHOLD + fail*self.PAINtoFAIL
                # And the other guy pays the holding pain
                if intended[a+p] and not s[a+p]: # Agent (successfully or not) grabbing 
                    R[i,a,j] += self.PAINtoGRAB

            # AND ALSO, what happens when the actor (A or B) is trying to exit?     
            a=3  # action (and hence affected state) concerns obj1 (=index 0) or obj2 (=index 2)
            assert(actionNames[a] == 'EXIT')
            for ag in ['A','B']: # 0 for case of player A acting, 3 for player B acting.
                if   ag=='A': p=0
                elif ag=='B': p=3
                isAttached = (s[0] and s[3]) or (s[2] and s[5]) or s[1] or s[4]
                isBreak = isAttached and self.allowBREAK
                fail = isAttached and not(self.allowBREAK)
                if fail: j = i
                else:    j = statestr2index[str(EXIT_STATE)]
                #if   ag=='A': self.Ptrans_Aacts[i,a,j] = 1.0 # very likely to happen
                #elif ag=='B': self.Ptrans_Bacts[i,a,j] = 1.0 
                # In the particular case of an exit attempt, we need to slow things down.
                if   ag=='A': 
                    if fail:
                        self.Ptrans_Aacts[i,a,j] = 1.0
                    else:
                        self.Ptrans_Aacts[i,a,j] = self.EXITRATE
                        self.Ptrans_Aacts[i,a,i] = 1.0-self.EXITRATE
                elif ag=='B': 
                    if fail:
                        self.Ptrans_Bacts[i,a,j] = 1.0
                    else:
                        self.Ptrans_Bacts[i,a,j] = self.EXITRATE
                        self.Ptrans_Bacts[i,a,i] = 1.0-self.EXITRATE
                # Now the rewards
                if   ag=='A': R = self.RewardA_Aacts 
                elif ag=='B': R = self.RewardB_Bacts
                if fail:
                    # agent still in play, so has to pay for any holds it maintains.
                    R[i,a,i] += (s[0+p]+s[1+p]+s[2+p])*self.PAINtoHOLD + fail*self.PAINtoFAIL
                else: # EXIT achieved! Get the loot...
                    assert(j == statestr2index[str(EXIT_STATE)])
                    if s != EXIT_STATE:
                        # TODO: What value to use for this?
                        # This is a patronising way of saying "pick it up and piss off"
                        LEFT_BEHIND_CHANCE = 0.0 # Small chance somebody else nails the object. Should have held it earlier!
                        if ag=='A':
                            self.RewardA_Aacts[i,a,j] += s[0]*r_A[0] + s[2]*r_A[1]
                            self.RewardB_Aacts[i,a,j] += s[3]*r_B[0] + s[5]*r_B[1]
                            # is there an obj left behind? If so, B should get it, right?
                            # NB: if so, B should feel the appropriate pain too. (Grab and Hold)
                            if s[0]==0 and s[3]==0: # A just left, leaving behind object a! 
                                self.RewardB_Aacts[i,a,j] += LEFT_BEHIND_CHANCE * r_B[0]    
                                self.RewardB_Aacts[i,a,j] += LEFT_BEHIND_CHANCE * (self.PAINtoGRAB + self.PAINtoHOLD) # BOTH, RIGHT?
                            if s[2]==0 and s[5]==0: # A just left, leaving behind object b!
                                self.RewardB_Aacts[i,a,j] += LEFT_BEHIND_CHANCE * r_B[1]
                                self.RewardB_Aacts[i,a,j] += LEFT_BEHIND_CHANCE * (self.PAINtoGRAB + self.PAINtoHOLD) # BOTH
                        elif ag=='B':
                            self.RewardA_Bacts[i,a,j] += s[0]*r_A[0] + s[2]*r_A[1]
                            self.RewardB_Bacts[i,a,j] += s[3]*r_B[0] + s[5]*r_B[1]
                            if s[3]==0 and s[0]==0: # B just left, leaving behind object a free! 
                                self.RewardA_Bacts[i,a,j] += LEFT_BEHIND_CHANCE * r_A[0]
                                self.RewardA_Bacts[i,a,j] += LEFT_BEHIND_CHANCE * (self.PAINtoGRAB + self.PAINtoHOLD) # BOTH
                            if s[5]==0 and s[2]==0: # B just left, leaving behind object b free!
                                self.RewardA_Bacts[i,a,j] += LEFT_BEHIND_CHANCE * r_A[1]
                                self.RewardA_Bacts[i,a,j] += LEFT_BEHIND_CHANCE * (self.PAINtoGRAB + self.PAINtoHOLD) # BOTH
                                
                # TODO: which of the below options is correct?
                # (nb. not invoked if break attempted but failed?)
                if isBreak: # broke a hold
                #if isAttached: # broke, or tried to break, a hold
                    R[i,a,j] += np.sum([s[0] and s[3], s[2] and s[5],s[1],s[4]]) * self.PAINtoBREAK

            # FINALLY, is there anything to do upon PASS? I don't think so.
            # Oh wait, there are pains to pay....
            a=4
            assert(actionNames[a] == 'PASS')
            # Nothing to do I guess!
            for ag in ['A','B']: # 0 for case of player A acting, 3 for player B acting.
                if   ag=='A': p=0
                elif ag=='B': p=3
                if   ag=='A': self.Ptrans_Aacts[i,a,i] = 1.0 
                elif ag=='B': self.Ptrans_Bacts[i,a,i] = 1.0 
                # agent still in play, so has to pay for any holds it maintains.
                #if   ag=='A': R = self.RewardA_Aacts 
                #elif ag=='B': R = self.RewardB_Bacts
                #R[i,a,i] += (s[0+p]+s[1+p]+s[2+p])*self.PAINtoHOLD
     
        # Re-normalise the transition probabilities.
        for s in range(self.nstates):
            for a in range(self.nacts):
                # normalise Probs for A actions
                Z = self.Ptrans_Aacts[s,a,:].sum()
                self.Ptrans_Aacts[s,a,:] = self.Ptrans_Aacts[s,a,:] / Z
                # normalise Probs for B actions
                Z = self.Ptrans_Bacts[s,a,:].sum()
                self.Ptrans_Bacts[s,a,:] = self.Ptrans_Bacts[s,a,:] / Z


        # Figure out successor state distribution given a RANDOM action, from each state.
        Ptrans_Arand = self.Ptrans_Aacts.sum(1)/self.nacts
        Ptrans_Brand = self.Ptrans_Bacts.sum(1)/self.nacts
        
        # And use that to change the transition probabilities to include effects 
        # of occasional "actions gone wrong".
        # EXCEPT don't do this for the case of the EXIT_STATE, as that has to stay gone forever.
        e = statestr2index[str(EXIT_STATE)]
        for i,s in index2state.items():
            if s != EXIT_STATE:
                for a in range(self.nacts):
                    self.Ptrans_Aacts[i,a,:] = (1-self.ACTIONNOISE)*self.Ptrans_Aacts[i,a,:] + self.ACTIONNOISE*Ptrans_Arand[i,:]
                    self.Ptrans_Bacts[i,a,:] = (1-self.ACTIONNOISE)*self.Ptrans_Bacts[i,a,:] + self.ACTIONNOISE*Ptrans_Brand[i,:]
        # ie. no action, and no noise, would allow you to jump back in once you've exitted. 
        # This shouldn't be needed, but just in case:
        self.Ptrans_Aacts[e,:,:] = 0.0
        self.Ptrans_Bacts[e,:,:] = 0.0
        self.Ptrans_Aacts[e,:,e] = 1.0
        self.Ptrans_Bacts[e,:,e] = 1.0
        
        # Final sanity checks before we ship these probs and rewards
        assert((np.abs(self.Ptrans_Aacts.sum(-1)-1) < 0.0000001).all())
        assert((np.abs(self.Ptrans_Bacts.sum(-1)-1) < 0.0000001).all())
        for R in allR:
            assert((R[e,:,e] == 0.0).all()) # no rewards flow to either player after an exit.
        
        
        # big bad check that R and P are all symmetric.
        for ind_s1,s1 in self.index2state.items():
            sym_s1 = s1[-1::-1]
            ind_sym_s1 = self.statestr2index[str(sym_s1)]                
            
            for ind_s2,s2 in self.index2state.items():
                sym_s2 = s2[-1::-1]
                ind_sym_s2 = self.statestr2index[str(sym_s2)]
                
                for a in actionNames.keys():
                    if a==0: sym_a = 2
                    elif a==2: sym_a = 0
                    else: sym_a = a
                    # Checking the transitions
                    if self.Ptrans_Aacts[ind_s1,a,ind_s2] != self.Ptrans_Bacts[ind_sym_s1,sym_a,ind_sym_s2]:
                        print("compare ",self.Ptrans_Aacts[ind_s1,a,ind_s2], self.Ptrans_Bacts[ind_sym_s1,sym_a,ind_sym_s2])
                    # Checking the rewards
                    if self.RewardA_Aacts[ind_s1,a,ind_s2] != self.RewardB_Bacts[ind_sym_s1,sym_a,ind_sym_s2]:
                        print("mismatch! ",a, s1, s2)
                    if self.RewardA_Bacts[ind_s1,a,ind_s2] != self.RewardB_Aacts[ind_sym_s1,sym_a,ind_sym_s2]:
                        print("mismatch! ",a, s1, s2)
        return

#############################################################################    

    def test_VI(self):
        self.RewardA_Aacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardA_Aacts[:-1,:,-1] = 1
        self.RewardA_Bacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardB_Aacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardB_Bacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        self.RewardB_Bacts[:-1,:,-1] = 1

        self.RewardA_Bacts[:-1,:,-1] = 1
        self.RewardB_Aacts[:-1,:,-1] = 1

        self.Ptrans_Aacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        self.Ptrans_Bacts = np.zeros((self.nstates, self.nacts, self.nstates), dtype=float)
        for i in range(self.nstates-1):
            self.Ptrans_Aacts[i,:,i+1] = 1 
            self.Ptrans_Bacts[i,:,i+1] = 1 
        self.Ptrans_Aacts[-1,:,-1] =1
        self.Ptrans_Bacts[-1,:,-1] =1
        assert((np.abs(self.Ptrans_Aacts.sum(-1)-1) < 0.0000001).all())

        return
        
    #----------------------------------------------------------------------------------------------
    def describe(self):
        print('maybe should print out just the non-zero entries in R tables')
        print('  and most likely successor states in P tables.')

    #----------------------------------------------------------------------------------------------
    def plot_rewards(self, actionNames, filestem):
        
        MAXVAL = self.max_payoff_feasible
        
        fig = plt.figure("Rewards",figsize=(12,10), dpi=200) #, font(20, "Courier"))
        SMALLFONT,BIGFONT = 10,16
        axR_toA_Aacts = []
        axR_toB_Aacts = []
        axR_toA_Bacts = []
        axR_toB_Bacts = []
        all4 = [axR_toA_Aacts,axR_toB_Aacts,axR_toA_Bacts,axR_toB_Bacts]
        for a in range(self.nacts):
            axR_toA_Aacts.append(plt.subplot2grid((4,5), (0,a)))  
            axR_toB_Aacts.append(plt.subplot2grid((4,5), (1,a)))  
            axR_toA_Bacts.append(plt.subplot2grid((4,5), (2,a)))  
            axR_toB_Bacts.append(plt.subplot2grid((4,5), (3,a)))  
    
        for a in range(self.nacts):
            #axR_toA_Aacts[a].imshow(self.RewardA_Aacts[:,a,:],cmap=myCMAP,vmin=-MAXVAL,vmax=MAXVAL,origin='upper')
            axR_toA_Aacts[a].imshow(self.RewardA_Aacts[:,a,:],cmap=myCMAP,vmin=0,vmax=MAXVAL,origin='upper')
            axR_toB_Aacts[a].imshow(self.RewardB_Aacts[:,a,:],cmap=myCMAP,vmin=0,vmax=MAXVAL,origin='upper')
            axR_toA_Bacts[a].imshow(self.RewardA_Bacts[:,a,:],cmap=myCMAP,vmin=0,vmax=MAXVAL,origin='upper')
            axR_toB_Bacts[a].imshow(self.RewardB_Bacts[:,a,:],cmap=myCMAP,vmin=0,vmax=MAXVAL,origin='upper')
        print(np.min(self.RewardA_Aacts), np.max(self.RewardA_Aacts))
        
        for a in range(self.nacts):
            axR_toA_Aacts[a].set_title('{0}'.format(actionNames[a]))
            for axlist in all4:
                axlist[a].set_xticks([])
                axlist[a].set_yticks([])
        axR_toA_Aacts[0].set_ylabel(r'$R^{to\,A}_{A}$',rotation=0,ha='right',fontsize=BIGFONT)
        axR_toB_Aacts[0].set_ylabel(r'$R^{to\,B}_{A}$',rotation=0,ha='right',fontsize=BIGFONT)
        axR_toA_Bacts[0].set_ylabel(r'$R^{to\,A}_{B}$',rotation=0,ha='right',fontsize=BIGFONT)
        axR_toB_Bacts[0].set_ylabel(r'$R^{to\,B}_{B}$',rotation=0,ha='right',fontsize=BIGFONT)
        #plt.tight_layout()
        print(filestem,os.path.isdir(filestem))
        if os.path.isdir(filestem):
            filename = os.path.join(filestem,'Rewards.{0}'.format(imgformat))
        else:
            filename = '{0}_Rewards.{1}'.format(filestem,imgformat)
        plt.savefig(filename)
        plt.close()
        print('Wrote {0}'.format(filename))
        return
    #----------------------------------------------------------------------------------------------
    def plot_transitions(self,  actionNames, filestem):
        
        fig = plt.figure("Transitions",figsize=(12,5), dpi=200) #, font(20, "Courier"))
        SMALLFONT,BIGFONT = 10,16
        axPtrans_Aacts = []
        axPtrans_Bacts = []
        for a in range(self.nacts):
            axPtrans_Aacts.append(plt.subplot2grid((2,5), (0,a)))  
            axPtrans_Bacts.append(plt.subplot2grid((2,5), (1,a)))  
    
        for a in range(self.nacts):
            axPtrans_Aacts[a].imshow(self.Ptrans_Aacts[:,a,:],cmap='Purples',vmin=0,vmax=1,origin='upper')
            axPtrans_Bacts[a].imshow(self.Ptrans_Bacts[:,a,:],cmap='Purples',vmin=0,vmax=1,origin='upper')
        
        for a in range(self.nacts):
            axPtrans_Aacts[a].set_title('{0}'.format(actionNames[a]))
        axPtrans_Aacts[0].set_ylabel(r'$P_{A}$',rotation=0,ha='right',fontsize=BIGFONT)
        axPtrans_Bacts[0].set_ylabel(r'$P_{B}$',rotation=0,ha='right',fontsize=BIGFONT)
        
        for a in range(self.nacts):
            axPtrans_Aacts[a].set_xticks([])
            axPtrans_Aacts[a].set_yticks([])
            axPtrans_Bacts[a].set_xticks([])
            axPtrans_Bacts[a].set_yticks([])
        #plt.tight_layout()
        if os.path.isdir(filestem):
            filename = os.path.join(filestem,'Transitions.{0}'.format(imgformat))
        else:
            filename = '{0}_Transitions.{1}'.format(filestem, imgformat)
        plt.savefig(filename)
        plt.close()
        print('Wrote {0}'.format(filename))
        return

### FUNCTIONS =================================================================

################################################################################
def softmax(qs, temperature):  # q is s by a
    """ softmax of an array of qs """
    vals = qs/temperature
    # since softmax is invariant to baseline, shift everything to avoid the 
    # exp getting too huge or tiny.
    vals = vals - np.atleast_2d(vals.max(1)).T
    tiny = -10.0
    vals[vals<tiny] = tiny
    z = np.exp(vals)
    Z = np.atleast_2d(z.sum(1)).T
    z = z/Z
    return(z)


def run_Value_Iteration(world, VIitns, QNOISE, V_A=None, V_B=None):
    """
    This runs the classic Value Iteration, but with two players.
    VI converges for single player, proved by Bellman, but for two it's less obvious.
    
    We add a tiny amount of noise to the Q-tables every step prior to the max and argmax operations.

    HOW ORDER OF PLAY IS BEING DONE HERE    
    To be agnostic about the actual order of actions requires they be able to pass.
    But that may not be enough, because one player can effectively deny the possibility
    of a multi-step play by the other (by NOT passing, eg. by pushing the state 
    back to an earlier one). But I think the possibility of multiple moves by 
    The Other is something to be guarded against (by avoiding the precursors, say),
    not just by being able to interfere mid-flow like this. 
    Trouble is, I'm not sure how best to incorporate this into the dynamics of VI.
    
    Currently, Nature tosses a coin at every timestep, which determines who is
    given the option to take an action. A drawback of leaving this up to chance is 
    that A_move, B_pass, A_move is 3 steps of discounting, not 2, and this 
    MIGHT give rise to weird / implausible side-effects.
    """

    nstates = world.Ptrans_Aacts.shape[0]
    nacts = world.Ptrans_Aacts.shape[1]
    
    # Noisy initial condition: shouldn't matter, if VI is bound to converge...
    if V_A is None:  # If nothing passed in (normal), we start VI with random values
        V_A = rng.randn(nstates) * QNOISE
    if V_B is None:
        V_B = rng.randn(nstates) * QNOISE 
    stored_V_A = [] # not needed for algorithm, just for display
    stored_V_B = [] # not needed for algorithm, just for display
    
    for iteration in range(VIitns):
        #(i) we recompute all those Q tables
        # Noise added every iteration anew: shouldn't matter, but I suspect it does.
        qnoise = QNOISE * (1-(1.*iteration)/VIitns)
         
        Q_toA_Aacts  = (world.Ptrans_Aacts * (world.RewardA_Aacts + world.GAMMA*V_A)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)      
        Q_toB_Aacts  = (world.Ptrans_Aacts * (world.RewardB_Aacts + world.GAMMA*V_B)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        Q_toB_Bacts  = (world.Ptrans_Bacts * (world.RewardB_Bacts + world.GAMMA*V_B)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        Q_toA_Bacts  = (world.Ptrans_Bacts * (world.RewardA_Bacts + world.GAMMA*V_A)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        
        # DRASTIC INTERVENTION......
        # going to ignore that for B: B's Q vals just reflect its insistence on passing!!
        if world.forcePASSINGB:
            Q_toB_Bacts  = 0.0*Q_toB_Bacts  -1.0 
            for k in range(nstates):  Q_toB_Bacts[k,4] = 0.0
        
        
        if world.TEMPERATURE > 0.0:  # use softmax action selection
            # no infinitely accurate maximization! Don't believe in it! 
            TEMP = world.TEMPERATURE
            V_toA_Aacts = (Q_toA_Aacts * softmax(Q_toA_Aacts,TEMP)).sum(1)
            V_toA_Bacts = (Q_toA_Bacts * softmax(Q_toA_Bacts,TEMP)).sum(1)
            V_toB_Aacts = (Q_toB_Aacts * softmax(Q_toB_Aacts,TEMP)).sum(1)
            V_toB_Bacts = (Q_toB_Bacts * softmax(Q_toB_Bacts,TEMP)).sum(1)
            
            for k in range(nstates):
                V_A[k] = world.BETA*V_toA_Aacts[k] + (1-world.BETA)*V_toA_Bacts[k] 
                V_B[k] = (1-world.BETA)*V_toB_Bacts[k] + world.BETA*V_toB_Aacts[k] 

        else: # use max-Q action selection (as in the old days).
            ind_bestA = Q_toA_Aacts.argmax(1)  # the "greedy" actions
            ind_bestB = Q_toB_Bacts.argmax(1)
            for k in range(nstates):
                V_A[k] = world.BETA*Q_toA_Aacts[k,ind_bestA[k]] + (1-world.BETA)*Q_toA_Bacts[k,ind_bestB[k]]
                V_B[k] = (1-world.BETA)*Q_toB_Bacts[k,ind_bestB[k]] + world.BETA*Q_toB_Aacts[k,ind_bestA[k]]
        #print(V_A[3])
                
        # Symmetrising......
        if world.SYMMETRIZE:
            # eg. For A, the value of s=[001000] is 4.
            # We don't want V_B[s] to be the same, but for B, v_B[000100] = 4.
            for k,s in world.index2state.items():
                symstate = s[-1::-1]
                indexof = world.statestr2index[str(symstate)]
                V_B[indexof] = V_A[k]

        stored_V_A.append(np.copy(V_A))
        stored_V_B.append(np.copy(V_B))
        
        values = [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts]
        
    return (values, stored_V_A, stored_V_B)

################################################################################



def plot_VIconvergence(stored_V_A, stored_V_B, index2state, world):

        
    ## FIRST, if there are lots of stored iterations, just show the first few and the LAST.
    n = 15
    print( len(stored_V_A) )      
    if len(stored_V_A) > n:
        stored_V_A = stored_V_A[:n] + stored_V_A[-1:]
        stored_V_B = stored_V_B[:n] + stored_V_B[-1:]
    print( len(stored_V_A)  )   
    max_payoff_feasible = world.max_payoff_feasible
    filestem = world.NAME
    nstates = len(index2state.keys())
    NUM_ITNS_VI = len(stored_V_A)
    fig = plt.figure("Value Iteration",figsize=(6.,3.5), dpi=300) #, font(20, "Courier"))
    SMALLFONT,BIGFONT = 4,10
    axV_A = plt.subplot2grid((1,2), (0,0))  
    axV_A.set_autoscaley_on(False)
    axV_A.set_xlim([-0.5,len(stored_V_A)])
    axV_A.set_ylim([0,nstates])
    axV_B = plt.subplot2grid((1,2), (0,1),sharey=axV_A)

    axV_A.imshow(np.array(stored_V_A).T,cmap=myCMAP,vmin=-max_payoff_feasible,vmax=max_payoff_feasible)
    axV_A.set_yticks([])
    axV_A.set_xticks(np.arange(len(stored_V_A)))
    axV_A.set_xlabel('Value itns')
    axV_A.set_title(r'$V_A$')
    for k,s in index2state.items():
        ss = str(s).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
        if (ss != 'disengaged'): ss = ss[:3] + ' : ' + ss[3:] 
        if (k in [10,25]): axV_A.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT,color='blue')
        else:       axV_A.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT)
        ## NOTE: low value holdings are the "outside" bits. High val ones are "inside"
        ## ie. lo,_,hi : hi,_,lo
        ## Think of the agents "trying" to get from 100:001 to 001:100
        if stored_V_A[-1][k] > 0.01:
            axV_A.text(NUM_ITNS_VI+2,k, '{0:6.2f}'.format(stored_V_A[-1][k]),ha='right',
                       va='center',fontsize=SMALLFONT,color='gray')
    #plt.subplot(1,5,2)
    h=axV_B.imshow(np.array(stored_V_B).T,cmap=myCMAP, vmin=0,vmax=max_payoff_feasible)
    axV_B.set_yticks([])
    axV_B.set_xticks(np.arange(NUM_ITNS_VI))
    axV_B.set_title(r'$V_B$',fontsize=BIGFONT)
    for k,s in index2state.items():
        if stored_V_B[-1][k] > 0.01:
            axV_B.text(NUM_ITNS_VI+2,k, '{0:6.2f}'.format(stored_V_B[-1][k]),ha='right',
                       va='center',fontsize=SMALLFONT,color='gray')
    print('=============================================')    
    
    axV_A.axis('off')
    axV_B.axis('off')
    plt.tight_layout()
    #if os.path.isdir(filestem):
    #    filename = os.path.join(filestem,'Vs.png')
    #else:
    filename = '{0}-Vs.{1}'.format(filestem,imgformat)
    plt.savefig(filename)
    plt.close()
    print('Wrote {0}'.format(filename))
    return


def show_Q_matrix(ax, Q, title, actionNames, MAXVAL, BIGFONT=10,SMALLFONT=6,showChoices=False):
    """ 
    Show a Q, which has dimensions [states,acts] 
    """
    
    nstates, nacts = Q.shape[0], Q.shape[1]
    ax.imshow(Q,cmap=myCMAP,vmin=0,vmax=MAXVAL)
    ax.set_title(title,fontsize=BIGFONT)
    ax.set_yticks([])
    ax.set_xticks([])
    for a in range(nacts):
        ax.text(a+.5,-.5,actionNames[a],rotation=70,
                ha='right',va='top',fontsize=SMALLFONT)
            
    if showChoices:
        bestAct, bestVal = Q.argmax(1), Q.max(1)  # gets the best act and val for all states.
        for k in range(nstates):
            topQval = bestVal[k]
            for a in range(nacts):
                if math.isclose(Q[k,a], bestVal[k], abs_tol=EPSILON):
                    ax.plot(a,k,'ow',markersize=3)

    for k in range(nstates):
        for a in range(nacts):
            if (Q[k,a]<0):
                ax.plot(a,k,'xk',markersize=6)
    return


def plot_Qs(Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts, world, actionNames):
    max_payoff_feasible = world.max_payoff_feasible
    filestem = world.NAME
    nstates, nacts = Q_toA_Aacts.shape[0], Q_toA_Aacts.shape[1]

    fig = plt.figure("Value Iteration",figsize=(6.5,5.), dpi=300) #, font(20, "Courier"))
    SMALLFONT,BIGFONT = 5,10
    axQ_toA_Aacts = plt.subplot2grid((1,4), (0,0))
    axQ_toA_Aacts.set_autoscaley_on(False)
    axQ_toA_Aacts.set_ylim([0,nstates])
    #axQ_toA_Aacts.set_ylim([nstates,0])
    axQ_toB_Aacts = plt.subplot2grid((1,4), (0,1),sharey=axQ_toA_Aacts)
    axQ_toB_Bacts = plt.subplot2grid((1,4), (0,2),sharey=axQ_toA_Aacts)
    axQ_toA_Bacts = plt.subplot2grid((1,4), (0,3),sharey=axQ_toA_Aacts)

    show_Q_matrix(axQ_toA_Aacts, Q_toA_Aacts, r'$Q_{to\,A}^{A\,act}$', actionNames, 
                  max_payoff_feasible, BIGFONT,SMALLFONT,showChoices=True)    
    
    # do the text entries on the left of the overall plot.
    for k,s in world.index2state.items():
        ss = str(s).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
        if (ss != 'disengaged'): ss = ss[:3] + ' : ' + ss[3:] 
        if (k in [10,25]): axQ_toA_Aacts.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT,color='blue')
        else:       axQ_toA_Aacts.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT)
        ## NOTE: low value holdings are the "outside" bits. High val ones are "inside"
        ## ie. lo,_,hi : hi,_,lo
        ## Think of the agents "trying" to get from 100:001 to 001:100
        if Q_toA_Aacts[k].max() > 0.01:
            axQ_toA_Aacts.text(8,k, '{0:6.2f}'.format(Q_toA_Aacts[k].max()),ha='right',
                       va='center',fontsize=SMALLFONT,color='gray')

    show_Q_matrix(axQ_toB_Aacts, Q_toB_Aacts, r'$Q_{to\,B}^{A\,act}$', actionNames,
                  max_payoff_feasible, BIGFONT,SMALLFONT)
    show_Q_matrix(axQ_toB_Bacts, Q_toB_Bacts, r'$Q_{to\,B}^{B\,act}$', actionNames, 
                  max_payoff_feasible, BIGFONT,SMALLFONT,showChoices=True)
    show_Q_matrix(axQ_toA_Bacts, Q_toA_Bacts, r'$Q_{to\,A}^{B\,act}$', actionNames, 
                  max_payoff_feasible, BIGFONT,SMALLFONT)
    axQ_toA_Aacts.axis('off')
    axQ_toA_Bacts.axis('off')
    axQ_toB_Aacts.axis('off')
    axQ_toB_Bacts.axis('off')
    #plt.tight_layout()
    plt.subplots_adjust(left=0,wspace = 0)
    filename = '{0}-Qs.{1}'.format(filestem,imgformat)
    #plt.subplot_tool()
    #plt.show()
    fig.subplots_adjust(left=0.04,right=0.45,top=0.95,wspace = 0)
    plt.savefig(filename)
    plt.close()
    print('Wrote {0}'.format(filename))
    return

def plot_QV(Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts, world, actionNames,stored_V_A):

    #import matplotlib.gridspec as gridspec
    max_payoff = world.max_payoff_feasible
    max_payoff = 3.0 
    filestem = world.NAME
    nstates, nacts = Q_toA_Aacts.shape[0], Q_toA_Aacts.shape[1]

    fig = plt.figure("Value Iteration",figsize=(12.,6.), dpi=300) #, font(20, "Courier"))
    TINYFONT,SMALLFONT,BIGFONT = 7,9,14  # was 5,10
    axQ_toA_Aacts = plt.subplot2grid((1,7), (0,0))
    axQ_toA_Aacts.set_autoscaley_on(False)
    axQ_toB_Aacts = plt.subplot2grid((1,7), (0,1),sharey=axQ_toA_Aacts)
    axQ_toB_Bacts = plt.subplot2grid((1,7), (0,2),sharey=axQ_toA_Aacts)
    axQ_toA_Bacts = plt.subplot2grid((1,7), (0,3),sharey=axQ_toA_Aacts)
    axV = plt.subplot2grid((1,7), (0,4),colspan=3)
    axQ_toA_Aacts.set_ylim([0,nstates])
    axV.set_ylim([0,nstates])
    
    show_Q_matrix(axQ_toA_Aacts, Q_toA_Aacts, r'$Q_{to\,A}^{A\,act}$', actionNames, 
                  max_payoff, BIGFONT,SMALLFONT,showChoices=True)    
    for k,s in world.index2state.items():
        ss = str(s).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
        if (ss != 'disengaged'): ss = ss[:3] + ' : ' + ss[3:] 
        if (k == 10): 
            axQ_toA_Aacts.text(-1,k,"done:  "+ss,ha='right',va='center', 
                                fontsize=SMALLFONT,color=EndStateColour, weight='bold')
        elif (k == 25): 
            axQ_toA_Aacts.text(-1,k,"start: "+ss,ha='right',va='center',
                                fontsize=SMALLFONT,color=StartStateColour, weight='bold')
        else:       axQ_toA_Aacts.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT)
        ## NOTE: low value holdings are the "outside" bits. High val ones are "inside"
        ## ie. lo,_,hi : hi,_,lo
        ## Think of the agents "trying" to get from 100:001 to 001:100
        if Q_toA_Aacts[k].max() > 0.01:
            axQ_toA_Aacts.text(6,k, '{0:6.2f}'.format(Q_toA_Aacts[k].max()),ha='right',
                       va='center',fontsize=SMALLFONT,color='white')  # HIDING FOR THE PAPER ONLY
    

    show_Q_matrix(axQ_toB_Aacts, Q_toB_Aacts, r'$Q_{to\,B}^{A\,act}$', actionNames,
                  max_payoff, BIGFONT,SMALLFONT)
    show_Q_matrix(axQ_toB_Bacts, Q_toB_Bacts, r'$Q_{to\,B}^{B\,act}$', actionNames, 
                  max_payoff, BIGFONT,SMALLFONT,showChoices=True)
    show_Q_matrix(axQ_toA_Bacts, Q_toA_Bacts, r'$Q_{to\,A}^{B\,act}$', actionNames, 
                  max_payoff, BIGFONT,SMALLFONT)
    print('=============================================')    
    #plt.colorbar(orientation='horizontal')
    
    n = 15
    steps = 2
    if len(stored_V_A) > n:
        stored_V_A = stored_V_A[:(n*steps):steps] + stored_V_A[-1:]
            
    NUM_ITNS_VI = len(stored_V_A)
    stored_V_A = list(np.array(stored_V_A).T)
    
    h=axV.imshow(stored_V_A,cmap=myCMAP,vmin=0,vmax=max_payoff)
    plt.colorbar(mappable=h,orientation='vertical',label='key: colour by value')
    axV.set_title(r'$V_A$',fontsize=BIGFONT)
    axV.set_yticks([])
    axV.set_xticks([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]) 
    axV.set_xticklabels(['1','3','5','7','9','11','13','15','17','19','21','23', '25','27','29','100'])
    #axV.set_xticks(np.arange(len(stored_V_A)))
    axV.set_xlabel('Value Iteration steps')
    for k,s in world.index2state.items():
        #if (k in [10,25]): axV.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT,color='blue')
        #else:       axV.text(-1,k,ss,ha='right',va='center',fontsize=SMALLFONT)
        ## NOTE: low value holdings are the "outside" bits. High val ones are "inside"
        ## ie. lo,_,hi : hi,_,lo
        ## Think of the agents "trying" to get from 100:001 to 001:100
        if stored_V_A[k][-1] > 0.01:
            axV.text(NUM_ITNS_VI+2,k, '{0:6.2f}'.format(stored_V_A[k][-1].max()),ha='right', va='center',fontsize=SMALLFONT,color='white') #WHITE TEXT! Hidden for the paper's figure.
    
    axQ_toA_Aacts.axis('tight')
    axQ_toA_Bacts.axis('tight')
    axQ_toB_Aacts.axis('tight')
    axQ_toB_Bacts.axis('tight')
    axV.axis('tight')

    axQ_toA_Aacts.axis('off')
    axQ_toA_Bacts.axis('off')
    axQ_toB_Aacts.axis('off')
    axQ_toB_Bacts.axis('off')
    #axV.axis('off')

    fig.tight_layout()
    plt.subplots_adjust(wspace=0.4)
    filename = '{0}-QV.{1}'.format(filestem,imgformat)
    plt.savefig(filename)
    plt.close()
    print('Wrote {0}'.format(filename))
    return
#---------------------------------------------------------------------------------------------


def  do_graph(rootState, EXIT_STATE, Q_AA, Q_BB, V_A, V_B, world, SILENTMODE=False):
        
    # Here's a wee helper method. Hopefully it inherits the main method's scope.
    def  add_node(i, thisName, graphHashName):
        # create a description of the node (which is really an array) in a string of 6 bits.
        if i==e:
            ss = 'disengaged'
        else:
            ss = str(world.index2state[i]).replace(', ','').replace('[','').replace(']','')

        graphHashName = graphHashName + str(i)
            
        if (thisName not in seenBefore):    
            seenBefore.add(thisName)
            # print('adding ',i)
            
            # decide on the "look" of this node.
            if (ss in ['100001']): 
                dot.attr('node', shape='doublecircle',fillcolor=StartStateColour,edgecolor=StartStateColour,color=StartStateColour,style='filled')
            elif (ss in ['001100']): 
                dot.attr('node', shape='doublecircle',fillcolor=EndStateColour,edgecolor=EndStateColour,color=EndStateColour,style='filled')
            else:
                dot.attr('node', shape='circle',fillcolor='gray',color='gray',edgecolor='gray',style='filled')


            if (ss == 'disengaged'):
                dot.attr('node', shape='doublecircle',fillcolor='white',edgecolor='black',color='white',style='filled')
                dot.node(thisName,'')
                #dot.node(thisName,'out')
                return graphHashName # because this is a leaf

            val_to_A = V_A[i] #Q_AA[i,:].max()
            val_to_B = V_B[i] #Q_BB[i,:].max()
            
            # create a new node (and recurse from that etc.)

            ## Show a picture in the middle!
            ## nb. I seem to need to include the little images as PNG, not SVG. 
            #imgfile = '../pics/{0}.{1}'.format(ss,'png') #imgformat)
            imgfile = '{0}/pics/{1}.{2}'.format(HOME_EXCHANGE_DIR,ss,'png') 
            
            
            assert(path.exists(imgfile)),'you probably need to run drawDiagrams.py in ../pics'
            
            dot.node(thisName, margin='0.1',image=imgfile, imagescale='True',label='')
            
            #dot.node(thisName, margin='0.1',image=imgfile, imagescale='True',
            #         label='{0:.3f},\n\n\n\n\n\n{1:.3f}'.format(V_A[i], V_B[i]), fontsize='22')
            
            # Now think about children
            oftenEnough = 0.26 # if softmax of the Q values is above this, (ie. prob of choosing), show the link.
            # This child is what happens if A acts
            bestQAA = (Q_AA[i,:]).max() 
            for a in range(world.nacts):
                #if softmax(Q_AA,world.TEMPERATURE)[i,a] > oftenEnough: #WAS: math.isclose(Q_AA[i,a], bestQAA, abs_tol=EPSILON): 
                if math.isclose(Q_AA[i,a], bestQAA, abs_tol=EPSILON):  
                    if a != 4:   # argh! so ugly, but 4 == 'PASS'
                        j = (world.Ptrans_Aacts[i,a,:]).argmax()
                        childName = '{0}'.format(j)
                        if (childName not in seenBefore): 
                            graphHashName = add_node(j, childName, graphHashName)
                        edgeTxt=actionString(a,world.index2state[i],'A')
                        dot.edge(thisName, childName , label=edgeTxt, color='blue', fontcolor='blue',fontsize='48')
                        
                    else: # it's just a PAUSE action: no new node is made. Instead, put an edge back to this
                        dot.edge(thisName, thisName, 'pass', color='blue', fontcolor='blue') # this is an action
                    
            # And this child is what happens if B acts
            bestQBB = (Q_BB[i,:]).max()
            for a in range(world.nacts):
                #if softmax(Q_BB,world.TEMPERATURE)[i,a] > oftenEnough: #WAS: math.isclose(Q_BB[i,a], bestQBB, abs_tol=EPSILON):
                if math.isclose(Q_BB[i,a], bestQBB, abs_tol=EPSILON):
                    if a != 4:   # argh! so ugly, but 4 == 'PASS'
                        j = (world.Ptrans_Bacts[i,a,:]).argmax()
                        childName = '{0}'.format(j)
                        if (childName not in seenBefore): 
                            graphHashName = add_node(j, childName, graphHashName)
                        edgeTxt=actionString(a,world.index2state[i],'B') # args are (act index, start state, 'B')
                        dot.edge(thisName, childName , label=edgeTxt, color='red', fontcolor='red',fontsize='48')
                    else: # it's just a PAUSE action: no new node is made. Instead, put an edge back to this
                        dot.edge(thisName, thisName, 'pass', color='red', fontcolor='red') # this is an action
           
            
        return graphHashName
    
    ####### MAIN GRAPH PLOTTING METHOD STARTS HERE ##############
    rootIndex = world.statestr2index[str(rootState)]
    e = world.statestr2index[str(EXIT_STATE)] # the index of EXIT_STATE
    
    # I'm going to do this all via graphviz, because it's so awesome.
    dot = Digraph(format=imgformat)  # works fine with png. pdf or svg not sure.
    dot.attr('graph',dpi='200',size='12,10',overlap='prism',rankdir='LR') #,concentrate='true')  # size='16,10', 
    dot.attr('edge',fontsize='24',penwidth='3')
    dot.attr('node',fontsize='24',fixedsize='true',width='2.5',height='1.5')
    seenBefore = set()
        
    graphHashName = add_node(rootIndex, str(rootIndex), '')
    
    if SILENTMODE == False:
        if os.path.isdir(world.NAME): # used to check whether world.NAME is a named dir or not.
            filename = os.path.join(world.NAME,'path')
        else:
            filename = world.NAME
        filename = filename + '_path'# + imgformat
        # Actually render the figure as the filename
        # (What format will be used here? Seems it's PDF)
        dot.render(filename, view=False, cleanup=True)   
        print('Wrote {0}'.format(filename))
    
    if len(graphHashName) > 31: # in case they get too long to use as hashes
            graphHashName = str(int(graphHashName) % 10000000019)  # denominator is prime
    #print('graph hashed to {0}'.format(graphHashName))
    return graphHashName


#-----------------------------------------------------------------------------
def  do_big_graph(EXIT_STATE, Q_AA, Q_BB, V_A, V_B, world):
    """
    Plot all the states, and best options between them.
    """
    localEPSILON = 0.05 #EPSILON #0.1
    # first, reduce the state to a short string to use later
    index2short = {} 
    for i in world.index2state.keys():
        index2short[i] = str(world.index2state[i]).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
    
    
    dot = Digraph(format=imgformat,engine='dot')  # engine in {dot, fdp, circo, neato, twopi}
    dot.attr(dpi='100')  # size='16,10',     rankdir='LR',  
    dot.attr('graph',root='36',concentrate='true')
    dot.attr('graph',overlap='scale') #,size='16,16')
    dot.attr('edge',fontsize='24',penwidth='10',arrowsize='1.0')
    dot.attr('node',fontsize='24',fixedsize='true',width='2.5',height='1.5')
    myRed, myBlue = '#ff0000AA', '#0000ffAA'
    
    # First we'll do all the nodes
    for i in range(len(world.index2state.keys())):
        # decide on the "look" of this node.
        if (index2short[i] == 'disengaged'):
            dot.node(str(i), label='disengaged', fontsize='36', shape='doublecircle',fillcolor='snow2',edgecolor='snow2',color='snow2',style='filled')
        else:
            if (index2short[i] in ['100001']): 
                dot.attr('node', shape='doublecircle',fillcolor=StartStateColour,edgecolor=StartStateColour,color=StartStateColour,style='filled')
            elif (index2short[i] in ['001100']): 
                dot.attr('node', shape='doublecircle',fillcolor=EndStateColour,edgecolor=EndStateColour,color=EndStateColour,style='filled')
            #elif (index2short[i] in ['000101']):
            #    dot.attr('node', shape='doublecircle',fillcolor='#ffaaaa',edgecolor='gray',color='gray',style='filled')
            #elif (index2short[i] in ['101000']):
            #    dot.attr('node', shape='doublecircle',fillcolor='#aaaaff',edgecolor='gray',color='gray',style='filled')
            else:
                c = 'gray'
                #if V_A[i] - V_B[i] >  0.1: c = '#aaaaff' # colour it blue if A likes it more than B.
                #if V_A[i] - V_B[i] < -0.1: c = '#ffaaaa' # colour it red  if B likes it more than A.
                dot.attr('node', shape='circle',fillcolor=c,color='gray',edgecolor='gray',style='filled')
            # now actually create the new node
            ss = str(world.index2state[i]).replace(', ','').replace('[','').replace(']','')
            
            #imgfile = '../pics/{0}.{1}'.format(ss,'png') #imgformat)
            imgfile = '{0}/pics/{1}.{2}'.format(HOME_EXCHANGE_DIR,ss,'png') 
            dot.node(str(i), margin='0.1',image=imgfile, imagescale='True',label='')
                     #label='{0:.3f},\n\n\n\n\n\n{1:.3f}'.format(V_A[i], V_B[i]), fontsize='22')
                     
    # Now we do the edges, for when A acts...
    for i in range(len(world.index2state.keys())):
        if (index2short[i] == 'disengaged'): continue
        bestQAA = (Q_AA[i,:]).max()
        for a in range(world.nacts):
            if math.isclose(Q_AA[i,a], bestQAA, abs_tol=localEPSILON): 
                if a != 4:   # argh! so ugly, but 4 == 'PASS'
                    j = (world.Ptrans_Aacts[i,a,:]).argmax()
                    childName = '{0}'.format(j)
                    #if (childName not in seenBefore) and (RECURSE or depth < 2): 
                    #    graphHashName = add_node(j, childName, graphHashName, depth+1, RECURSE)
                    edgeTxt=actionString(a,world.index2state[i],'A')
                    dot.edge(str(i), childName , label=edgeTxt, #style='dashed',
                             color=myBlue, fontcolor=myBlue, fontsize='30')
                    
                else: # it's just a PAUSE action: no new node is made. Instead, put an edge back to this
                    dot.edge(str(i), str(i), 'pass', color=myBlue, fontcolor=myBlue) # this is an action

    # ... and for when B acts...
    for i in range(len(world.index2state.keys())):
        if (index2short[i] == 'disengaged'): continue
        bestQBB = (Q_BB[i,:]).max() 
        for a in range(world.nacts):
            if math.isclose(Q_BB[i,a], bestQBB, abs_tol=localEPSILON): 
                if a != 4:   # argh! so ugly, but 4 == 'PASS'
                    j = (world.Ptrans_Bacts[i,a,:]).argmax()
                    childName = '{0}'.format(j)
                    #if (childName not in seenBefore) and (RECURSE or depth < 2): 
                    #    graphHashName = add_node(j, childName, graphHashName, depth+1, RECURSE)
                    edgeTxt=actionString(a,world.index2state[i],'B')
                    dot.edge(str(i), childName , label=edgeTxt, #style='dashed',
                             color=myRed, fontcolor=myRed, fontsize='30')
                    
                else: # it's just a PAUSE action: no new node is made. Instead, put an edge back to this
                    dot.edge(str(i), str(i), 'pass', color=myRed, fontcolor=myRed) # this is an action
    
    filename = '{0}_entirity'.format(world.NAME)
    dot.render(filename, view=False, cleanup=True)
    print('Wrote {0}'.format(filename))        
    return


#-----------------------------------------------------------------------------
    

def actionString(actionIndex, oldState, player='A'):
    words = ['grab','drop']
    if actionIndex==3: return 'exit'
    elif actionIndex==4: return 'pass'
    if player=='A':
        if actionIndex==0: return( '{0} a'.format(words[oldState[0]]) )
        elif actionIndex==1: return( '{0} B'.format(words[oldState[1]]) )
        elif actionIndex==2: return( '{0} b'.format(words[oldState[2]]) )
    elif player=='B':
        if actionIndex==0: return( '{0} a'.format(words[oldState[3]]) )
        elif actionIndex==1: return( '{0} A'.format(words[oldState[4]]) )
        elif actionIndex==2: return( '{0} b'.format(words[oldState[5]]) )    
    else: return( 'oh dear')
    


################################################################################

def plot_rollout(start, EXITSTATE, numsteps, Q_toA_Aacts, Q_toB_Bacts, params):
    """
    """
    if params.TEMPERATURE > 0.0: TEMPER = params.TEMPERATURE
    else: TEMPER = 0.01
    exitIndex = params.statestr2index[str(EXITSTATE)]
    recentChange = 100.
    pStates = np.zeros(params.nstates, dtype=float)
    pStates[params.statestr2index[str(start)]] = 1.0
    pStates_recorder = []
    pExitFrom = np.zeros(params.nstates, dtype=float)
    pExitFrom_recorder = []
    t=0
    while recentChange > 0.05:  # the sum of abs change in prob vector over states.
        pStates_recorder.append(pStates)
        pExitFrom_recorder.append(pExitFrom[:-1])
        t += 1
        psucc = np.zeros(params.nstates, dtype=float)
        pExitFrom = np.zeros(params.nstates, dtype=float)
        BoltzA = softmax(Q_toA_Aacts,TEMPER)
        BoltzB = softmax(Q_toB_Bacts,TEMPER)
        for k in range(params.nstates):
            # figure out the new density over states
            # With prob BETA, A is the one who acts.
            # When A acts, they choose an intended action by looking at... what?
            # Boltzmann on Q's??? 
            # But to be consistent we should perhaps look at close ties instead.
            
            psucckA = np.dot(BoltzA[k,:], params.Ptrans_Aacts[k,:,:])  # will it broadcast right??!
            # psucckA should be probs of successor states, when state was k and A was the actor
            
            psucckB = np.dot(BoltzB[k,:], params.Ptrans_Bacts[k,:,:])  # will it broadcast right??!
            
            psuccChange = pStates[k] * (params.BETA*psucckA + (1-params.BETA)*psucckB)
            # TESTER: psucc += Pstates[k] * (psucckA)
            pExitFrom[k] = psuccChange[exitIndex]
            psucc += psuccChange
        pStates = psucc
        
        recentChange = np.sum(np.abs(pStates-pStates_recorder[-1]))
        
    fig = plt.figure("PState",figsize=(12,5), dpi=200)
    
    ax1 = plt.subplot2grid((1,2), (0,0))
    #ax1.set_autoscaley_on(False)
    #ax1.set_ylim([0,nstates])
    ax2 = plt.subplot2grid((1,2), (0,1),sharey=ax1)
    
    #plt.subplot(121)
    ax1.imshow(np.array(pStates_recorder),cmap=myCMAP,origin='upper')
    ax1.set_yticks(range(0,len(pStates_recorder),5))
    ax1.set_xticks([])
    ax1.set_ylabel(r'$\longleftarrow$ #actions taken $\longleftarrow$')
    ax1.set_title('prob of states')
    print(len(pStates_recorder),' steps of rollout')
    SMALLFONT, XOFFSET, YOFFSET, ANGLE, ALPHA = 8, -.1, len(pStates_recorder)-1, -90, .8
    for k,s in params.index2state.items():
        ss = str(s).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
        if (ss != 'disengaged'): ss = ss[:3] + ' : ' + ss[3:] 
        if (k in [10,25]): 
            ax1.text(k+XOFFSET,YOFFSET,ss,ha='center',va='bottom',fontsize=SMALLFONT,fontweight='bold',
                    rotation=ANGLE,color='blue',alpha=ALPHA)
        elif (ss == 'disengaged'): 
            ax1.text(k+XOFFSET,0.0,ss,ha='center',va='top',fontsize=SMALLFONT,
                    rotation=ANGLE,alpha=ALPHA)
        else: 
            ax1.text(k+XOFFSET,YOFFSET,ss,ha='center',va='bottom',fontsize=SMALLFONT,
                    rotation=ANGLE,alpha=ALPHA)
    
    YOFFSET = 0.    
    #plt.subplot(122)
    ax2.imshow(np.array(pExitFrom_recorder).cumsum(0),cmap=myCMAP,origin='upper')
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_ylabel(r'$\longleftarrow$ #actions taken $\longleftarrow$')
    ax2.set_title('where exits come from (cumulative)')
    for k,s in params.index2state.items():
        ss = str(s).replace(', ','').replace('[','').replace(']','').replace('-1-1-1-1-1-1','disengaged')
        if (ss == 'disengaged'): continue 
        else: ss = ss[:3] + ' : ' + ss[3:] 
        if (k in [10,25]): 
            ax2.text(k+XOFFSET,YOFFSET,ss,ha='center',va='top',fontsize=SMALLFONT,fontweight='bold',
                    rotation=ANGLE,color='blue',alpha=ALPHA)
        else:       
            ax2.text(k+XOFFSET,YOFFSET,ss,ha='center',va='top',fontsize=SMALLFONT,
                    rotation=ANGLE,alpha=ALPHA)
    plt.tight_layout(pad=0)
    filename = '{0}_rollout.{1}'.format(params.NAME, imgformat)
    plt.savefig(filename)
    print('Wrote {0}'.format(filename))
    return 
    
    
    
#######################################################################################
#######################################################################################
#######################################################################################
#######################################################################################
## OLD STUFF - hopefully we can stick with softmax VI instead from now on.
## But anyway, this is the vanilla deterministic VI
##

"""
def run_Value_Iteration(param, VIitns,QNOISE,V_A=None,V_B=None):
    This runs the classic Value Iteration, but with two players.
    VI converges for single player, proved by Bellman I guess, but for 2?
    
    An issue that worries me is that there are dead-ties in the Q-values, and 
    the code will just pick one to be the argmax, arbitrarily. Isn't that a
    bit of a worry? To give myself some confidence, I add a tiny amount of noise
    to the Q-tables every step prior to the max and argmax operations.

    What we get: for some parameter settings, MULTIPLE SOLUTIONS. 
    Are these "valid"?? Should we eliminate them somehow, or take all seriously?
    Are they a result of different i.c. V tables, or of noise in the Q's added
    during the run? 

    HOW ORDER OF PLAY IS BEING DONE HERE    
    To be agnostic about the actual order of actions requires they be able to pass.
    But that may not be enough, because one player can effectively deny the possibility
    of a multi-step play by the other (by NOT passing, eg. by pushing the state 
    back to an earlier one). But I think the possibility of multiple moves by 
    The Other is something to be guarded against (by avoiding the precursors, say),
    not just by being able to interfere mid-flow like this. 
    Trouble is, I'm not sure how best to incorporate this into the dynamics of VI.
    
    Currently, Nature tosses a coin at every timestep, which determines who is
    given the option to take an action. A drawback of leaving this up to chance is 
    that A_move, B_pass, A_move is 3 steps of discounting, not 2, and this 
    MIGHT give rise to weird / implausible side-effects?

    nstates = world.Ptrans_Aacts.shape[0]
    nacts = world.Ptrans_Aacts.shape[1]
    
    # Noisy initial condition: shouldn't matter, if VI is bound to converge...
    if V_A is None:  # If nothing passed in (normal), we start VI with random values
        V_A = rng.random(nstates) * QNOISE
    if V_B is None:
        V_B = rng.random(nstates) * QNOISE 
    stored_V_A = [] # not needed for algorithm, just for display
    stored_V_B = [] # not needed for algorithm, just for display
    
    for iteration in range(VIitns):
        #(i) we recompute all those Q tables
        # Noise added every iteration anew: shouldn't matter, but I suspect it does.
        if iteration > 2/3.*VIitns: QNOISE = 0.0  # no noise anyway, for the last third, say.
        qnoise = QNOISE * (1.*iteration/VIitns)
         
        Q_toA_Aacts  = (world.Ptrans_Aacts * (world.RewardA_Aacts + world.GAMMA*V_A)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)      
        Q_toB_Aacts  = (world.Ptrans_Aacts * (world.RewardB_Aacts + world.GAMMA*V_B)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        Q_toB_Bacts  = (world.Ptrans_Bacts * (world.RewardB_Bacts + world.GAMMA*V_B)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        Q_toA_Bacts  = (world.Ptrans_Bacts * (world.RewardA_Bacts + world.GAMMA*V_A)).sum(2) + qnoise*(2*rng.random((nstates,nacts))-1)
        

        # Can deal with ties in the optimal choice
        ind_bestA = Q_toA_Aacts.argmax(1)  
        ind_bestB = Q_toB_Bacts.argmax(1)  
        for k in range(nstates):
            V_A[k] = world.BETA*Q_toA_Aacts[k,ind_bestA[k]] + (1-world.BETA)*Q_toA_Bacts[k,ind_bestB[k]]
            V_B[k] = (1-world.BETA)*Q_toB_Bacts[k,ind_bestB[k]] + world.BETA*Q_toB_Aacts[k,ind_bestA[k]]
            
        # Symmetrising......
        if world.SYMMETRIZE:
            print('yeah its symmetrizing')
            # eg. For A, the value of s=[001000] is 4.
            # We don't want V_B[s] to be 5.  For B, v_B[000100] = 4.
            for k,s in world.index2state.items():
                symstate = s[-1::-1]
                indexof = world.statestr2index[str(symstate)]
                V_B[indexof] = V_A[k]
         
            
        stored_V_A.append(V_A)
        stored_V_B.append(V_B)
        values = [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts]
    return (values, stored_V_A, stored_V_B)

################################################################################
def alt_run_Value_Iteration(param, VIitns, QNOISE, V_A=0., V_B=0.):
    SAME AS ABOVE BUT I HOLD B, RUN VI FOR A FOR A BIT, THEN REVERSE, ETC.
    
    SEEMS TO GIVE SAME BEHAVIOUR, BUT WORTH CHECKING MORE THOROUGHLY IN ABSENCE 
    OF A CONVERGENCE PROOF
    
    This runs the classic Value Iteration, but with two players.
    VI converges for single player, proved by Bellman I guess, but for 2?
    
    An issue that worries me is that there are dead-ties in the Q-values, and 
    the code will just pick one to be the argmax, arbitrarily. Isn't that a
    bit of a worry? To give myself some confidence, I add a tiny amount of noise
    to the Q-tables every step prior to the max and argmax operations.

    What we get: for some parameter settings, MULTIPLE SOLUTIONS. 
    Are these "valid"?? Should we eliminate them somehow, or take all seriously?
    Are they a result of different i.c. V tables, or of noise in the Q's added
    during the run? 

    HOW ORDER OF PLAY IS BEING DONE HERE    
    To be agnostic about the actual order of actions requires they be able to pass.
    But that may not be enough, because one player can effectively deny the possibility
    of a multi-step play by the other (by NOT passing, eg. by pushing the state 
    back to an earlier one). But I think the possibility of multiple moves by 
    The Other is something to be guarded against (by avoiding the precursors, say),
    not just by being able to interfere mid-flow like this. 
    I'm not sure how best to incorporate this into the dynamics of VI.
    
    Currently, Nature tosses a coin at every timestep, which determines who is
    given the option to take an action. A drawback of leaving this up to chance is 
    that A_move, B_pass, A_move is 3 steps of discounting, not 2, and this 
    MIGHT give rise to weird / implausible side-effects?
    
    nstates = world.Ptrans_Aacts.shape[0]
    nacts = world.Ptrans_Aacts.shape[1]
    
    # Noisy initial condition: shouldn't matter, if VI is bound to converge...
    V_A = rng.random(nstates) * QNOISE
    V_B = rng.random(nstates) * QNOISE 
    stored_V_A = [] # not needed for algorithm, just for display
    stored_V_B = [] # not needed for algorithm, just for display
    Q_toA_Aacts  = (world.Ptrans_Aacts * (world.RewardA_Aacts + world.GAMMA*V_A)).sum(2)      
    Q_toB_Bacts  = (world.Ptrans_Bacts * (world.RewardB_Bacts + world.GAMMA*V_B)).sum(2)
            
    NUM_INNER = 5  
    for iteration in range(VIitns):
        V_A[-1] = 0.0
        V_B[-1] = 0.0
        #(i) we recompute all those Q tables
        # Noise added every iteration anew: shouldn't matter, but I suspect it does.
        if iteration > 2/3*VIitns: 
            QNOISE = 0.0  # no noise anyway, for the last third, say.

        # do A for a bit
        for inner in range(NUM_INNER):
            Q_toA_Aacts  = (world.Ptrans_Aacts * (world.RewardA_Aacts + world.GAMMA*V_A)).sum(2) + QNOISE*(2*rng.random((nstates,nacts))-1)   
            Q_toA_Bacts  = (world.Ptrans_Bacts * (world.RewardA_Bacts + world.GAMMA*V_A)).sum(2) + QNOISE*(2*rng.random((nstates,nacts))-1)
            bestB = Q_toB_Bacts.argmax(1)  
            tmp_V_AA = Q_toA_Aacts.max(1) # value of state for A player, if they get to play next
            #(ii) what action looks best for the OTHER player?
            tmp_V_AB = np.zeros(nstates,dtype=float)
            for k in range(nstates):
                tmp_V_AB[k] = Q_toA_Bacts[k,bestB[k]]
            V_A = world.BETA*tmp_V_AA + (1-world.BETA)*tmp_V_AB
        stored_V_A.append(V_A)


        for inner in range(NUM_INNER):
            Q_toB_Aacts  = (world.Ptrans_Aacts * (world.RewardB_Aacts + world.GAMMA*V_B)).sum(2) + QNOISE*(2*rng.random((nstates,nacts))-1)
            Q_toB_Bacts  = (world.Ptrans_Bacts * (world.RewardB_Bacts + world.GAMMA*V_B)).sum(2) + QNOISE*(2*rng.random((nstates,nacts))-1)
            bestA = Q_toA_Aacts.argmax(1)  
            tmp_V_BB = Q_toB_Bacts.max(1) # sim for B.       
            tmp_V_BA = np.zeros(nstates,dtype=float)
            for k in range(nstates):
                tmp_V_BA[k] = Q_toB_Aacts[k,bestA[k]]
            V_B = (1-world.BETA)*tmp_V_BB + world.BETA*tmp_V_BA
        stored_V_B.append(V_B)
        
        values = [V_A, V_B, Q_toA_Aacts, Q_toB_Aacts, Q_toA_Bacts, Q_toB_Bacts]
    return (values, stored_V_A, stored_V_B)
"""


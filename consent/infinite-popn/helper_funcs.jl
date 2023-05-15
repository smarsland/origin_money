using Printf
using OrderedCollections


BENEFIT = 2
COST = 1

# Read the following as WHAT WILL HAPPEN TO THE FIRST PLAYER IN THE KEY.
# Note two arguable spots:
#    AllowedDS['n','n']=0 and sim for ['p','p'], ie. if doing nothing score-wise is ok with both, that's what happens.
#    AllowedDH['n','p']=0, similarly: if doing nothing help-wise is ok with both, that's what happens.
# ie. if you want a change in state, you have to ask for it!
AllowedDS = Dict(['-','-']=>-1,['0','0']=>0,['+','+']=>1)
AllowedDH = Dict(['g','r']=>'g',['r','g']=>'r',['0','0']=>'0')

strScore  = Dict(0=>"S0",   1=>"S1")
strCan    = Dict(0=>"need", 1=>"surp")

function isZeroSum(stratname) 
    """ Is this strategy a zero-sum one with respect to scores?
    ie. in EACH of the 4 situations (S=0/1 and state=need/can) is score conserved, 
        should the transaction take place?
    """
    strat = name2strategy(stratname)["strategy"]
    isZeroSum = true
    for neediness in ["need","surp"]
        for solvency in ["S0","S1"]
            if ((strat[neediness][solvency][1] * strat[neediness][solvency][3]) in ["-+","00","+-"]) == false
                isZeroSum = false
            end
        end
    end
    return isZeroSum
end

function makeAllSpecies(FULL_STRATEGY_SPACE=true)
    # make ALL species!!
    # Returns them as a SortedDict, with the name as key.
    #allspecies = OrderedDict{String,Any}()
    allspecies = Dict{String,Any}()
    ScoreChgOptions  = "-0+" 
    HelpOfferOptions = "g0r"
        
    for selfChg_NeedS0 in ScoreChgOptions
        for help_NeedS0 in HelpOfferOptions
            for otherChg_NeedS0 in ScoreChgOptions
                for selfChg_SurpS0 in ScoreChgOptions
                    for help_SurpS0 in HelpOfferOptions
                        for otherChg_SurpS0 in ScoreChgOptions
                            for selfChg_NeedS1 in ScoreChgOptions# [selfChg_NeedS0]#ScoreChgOptions
                                for help_NeedS1 in HelpOfferOptions#[help_NeedS0]#HelpOfferOptions
                                    for otherChg_NeedS1 in ScoreChgOptions# [otherChg_NeedS0]#ScoreChgOptions
                                        for selfChg_SurpS1 in ScoreChgOptions# [selfChg_SurpS0]#ScoreChgOptions
                                            for help_SurpS1 in HelpOfferOptions#[help_SurpS0]#HelpOfferOptions
                                                for otherChg_SurpS1 in ScoreChgOptions# [otherChg_SurpS0]#ScoreChgOptions

                                                    # We don't need to include strategies that would be == "no offer"
                                                    # in effect, due to being unrealisable in practice.
                                                    # (nb: no problem to include them, but makes interpretation harder due to 
                                                    # effective redundancy among the possible strategies.)
                                                    # NOTICE this excludes "money" -r+,+g-  from the full strategy space.
                                                    
                                                    """
                                                    if  (FULL_STRATEGY_SPACE) && # nb. this needed, else will 
                                                                                 # exclude (eg) money from the restricted space too! 
                                                        ((selfChg_NeedS0 == '-') || (selfChg_SurpS0 == '-')) #
                                                        continue # because, even if agreed to, this would reduce x score below zero
                                                    elseif (help_NeedS0 == 'g') || (help_NeedS1 == 'g')
                                                        continue # because x can't give if it is in need.
                                                    end
                                                    """
                                                    if (help_NeedS0 == 'g') || (help_NeedS1 == 'g')
                                                        continue # because x can't give if it is in need.
                                                    end
                                                    if ((selfChg_NeedS0 == '-') || (selfChg_SurpS0 == '-'))
                                                        continue # because the score can't go negative.
                                                    end
                                                    
                                                    species = Dict{String,Any}()
                                                    species["strategy"]= Dict{String,Any}()
                                                    # prep the STRINGS that go into the offer dictionaries.
                                                    dumS0 = selfChg_NeedS0 * help_NeedS0 * otherChg_NeedS0 
                                                    dumS1 = selfChg_NeedS1 * help_NeedS1 * otherChg_NeedS1
                                                    species["strategy"]["need"] = Dict([("S0",dumS0),("S1",dumS1)])
                                                    dumS0 = selfChg_SurpS0 * help_SurpS0 * otherChg_SurpS0
                                                    dumS1 = selfChg_SurpS1 * help_SurpS1 * otherChg_SurpS1
                                                    species["strategy"]["surp"] = Dict([("S0",dumS0),("S1",dumS1)])
                                                    species["name"] = strategy2name(species) # knows its own name

                                                    if FULL_STRATEGY_SPACE || isZeroSum(species["name"])
                                                        allspecies[species["name"]] = species # name is its key in allspecies
                                                    end
                                                end
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    #println(length(allspecies)," species altogether")
    #for (name,spec) in collect(allspecies)[1:6]
    #    println(name)
    #end
    return(allspecies)
end

#------------------------------------------------------------------------------------------------------------
"""
Take a species (essentially, a dictionary of offers) and generate a single string that represents it.
"""
function strategy2name(species)
    S0name = species["strategy"]["need"]["S0"] * ',' * species["strategy"]["surp"]["S0"]
    S1name = species["strategy"]["need"]["S1"] * ',' * species["strategy"]["surp"]["S1"]

    #if S1name == S0name
    #    return( S0name )
    #else
    #    return( S0name * "|" * S1name )
    #end
    return( S0name * "|" * S1name )
end


"""
Take a string representation of a strategy, and generate the full strategy (ie. a dictionary of offers).
"""
function name2strategy(name::String)
    @assert(length(name) == 15) #in [7,15])
    #if (length(name)==7)  name = name*'|'*name  end
    species = Dict{String,Any}()
    species["strategy"]= Dict{String,Any}()
    species["strategy"]["need"] = Dict([("S0",name[1:3]),("S1",name[9:11])])
    species["strategy"]["surp"] = Dict([("S0",name[5:7]),("S1",name[13:15])])
    # tell it its name!
    species["name"] = strategy2name(species)
    return species
end

# check those two functions work as intended
testname = "+0+,+g-|-r+,000"
@assert(strategy2name(name2strategy(testname)) == testname)

testname = "+0+,+g-|+0+,+g-"
@assert(strategy2name(name2strategy(testname)) == testname)

#------------------------------------------------------------------------------------------------------------

function build_interaction_cases(X, Y) # X,Y being 2 species / strategies
    """
    Precomputation that is useful for the score and payoff calculations to come.
    Consider the interaction between an X individual with a Y individual:
    We step through all the 16 options for the 'case'=(Sx,Sy,Cx,Cy), where 
      Sx is 1 if the X player is `solvent', ie. has score above zero.
      Cx is 1 if player is in `CAN` (== in surplus), and 0 if it is in Need;
      And similarly for the Y player.
    The strategies dictate what happens in each such case. 

    If Sx=0 AND (for the X player) ds= +1: include the case (Sx,Sy,Cx,Cy) in a set `alphaCases`
    If Sx=1 AND ds= +1: include in `betaCases`
    If Sx=1 AND ds= -1: include in `gammaCases`
    If dh=1 (ie. X player helps): include in 'costCases'
    If dh=-1 (player is helped): include in 'benefitCases'
    
    Return these 5 sets as a single Dict from the name (e.g. 'alphaCases') to the Set.
    """
    xcases = Dict{String,Set{Any}}("alpha"=>Set(), "beta"=>Set(), "gamma"=>Set(), "cost"=>Set(), "benefit"=>Set())
    
    for Sx in 0:1
        for Sy in 0:1
            for Cx in 0:1
                for Cy in 0:1
                    # is there a match between the offers of X and Y, in this situation?
                    
                    xOffer = X["strategy"][strCan[Cx]][strScore[Sx]] # which is 3-pronged; a string of 3 chars.
                    yOffer = Y["strategy"][strCan[Cy]][strScore[Sy]]
                    # if ANY of these is a fail, we simply jump to next, without any further checks
                    if !([xOffer[1],yOffer[3]] in keys(AllowedDS)) # x's ds not agreed
                        continue
                    elseif !([xOffer[3],yOffer[1]] in keys(AllowedDS)) # y's ds not agreed
                        continue
                    elseif !([xOffer[2],yOffer[2]] in keys(AllowedDH)) # help not agreed
                        continue
                    end
                    # If get to here, the offers were a perfect match. But can they be carried out?
                    # Nb. It is possible to skip this out IF YOU'RE CERTAIN that such strategies have been
                    # EXCLUDED already. But also "dangerous" to skip this if you're not certain :)
                    # Tested, and including it seems to have no performance cost, so leaving it in.
                    if     (Sx == 0 && AllowedDS[[xOffer[1],yOffer[3]]] < 0)
                        continue # because this would reduce x score below zero
                    elseif (Sy == 0 && AllowedDS[[yOffer[1],xOffer[3]]] < 0)
                        continue # because this would reduce y score below zero
                    #elseif (Cx == 0 && AllowedDH[[xOffer[2],yOffer[2]]] == 'g')
                    #    continue # because x can't give if it is in need.
                    #elseif (Cy == 0 && AllowedDH[[yOffer[2],xOffer[2]]] == 'g')
                    #    continue # because y can't give if it is in need.
                    end
                    
                    # There is actionable agreement between the parties, for this case.
                    ds   = AllowedDS[[xOffer[1],yOffer[3]]] # in {-1, 0, 1}
                    help = AllowedDH[[xOffer[2],yOffer[2]]] # in {'r','0','g'}
                    if (ds == 1 && Sx == 0) push!( xcases["alpha"],  [Sx, Sy, Cx, Cy]) end
                    if (ds == 1 && Sx == 1) push!( xcases["beta"],  [Sx, Sy, Cx, Cy]) end
                    if (ds == -1 && Sx == 1) push!( xcases["gamma"],   [Sx, Sy, Cx, Cy]) end
                    # WAS JUST THIS EARLIER BUT THE ABOVE LINE IS SAFER...
                    #if (ds == -1) push!( xcases["gamma"],   [Sx, Sy, Cx, Cy]) end
                    
                    # NOTE: while in theory an agent that is in surplus *can* still 
                    # be receptive to being given help, and this *should* cost the giver,
                    # the receiver shouldn't "feel" it, in its payoff.
                    # That's a better way to handle this situation than simply banning it.
                    # Hence the extra condition in the first line, below.
                    if (help == 'r' && Cx == 0) push!( xcases["benefit"],[Sx, Sy, Cx, Cy]) end
                    #if (help == 'r') push!( xcases["benefit"],[Sx, Sy, Cx, Cy]) end
                    if (help == 'g')            push!( xcases["cost"],   [Sx, Sy, Cx, Cy]) end
                end
            end
        end
    end
    
    #for (k,v) in xcases
    #    println(k,":")
    #    for case in v println("\t",case) end

    return xcases
end


"""
    Find stable score distribution of an infinite population 
    consisting of a single species.
"""
function calc_stable_w_1species(A; w_init=[0.5,0.5], tolerance=1e-5, maxn=1000, VERBOSE=false)

    cases = build_interaction_cases(A, A)
    w = copy(w_init)
    
    trans = Dict("alpha"=>0.0, "beta"=>0.0, "gamma"=>0.0) # store the 3 transition probs as a Dict    
    chg = 1.0
    global n = length(w)
    global counter = 0
    while chg > tolerance && counter < maxn
        counter += 1
        n = length(w)
        w0 = w[1]
        push!(w,0.0) # adds one more (empty) bin, because the top-possible score goes up each iteration.
        # find alpha, etc... which are CONDITIONED on Sx, so we don't include that prob, just the Sy one.
        for key in keys(trans) 
            total = 0.0
            for case in cases[key]  # Note: case[2] is Sy
                if case[2]==0 total += w0 else total += (1-w0) end
            end
            trans[key] = total/4.0 # the 1/4 is the p(Cx) * p(Cy) of this case.
        end
        
        dw = zeros(length(w))
        
        dw[1] += -w[1]*trans["alpha"] + w[2]*trans["gamma"]  # the change to w0
        dw[2] += -w[2]*trans["gamma"] -w[2]*trans["beta"]   + w[1]*trans["alpha"] + w[3]*trans["gamma"] # the change to w0
        for i in 3:n
            dw[i] += -w[i]*trans["gamma"] -w[i]*trans["beta"]   + w[i-1]*trans["beta"] + w[i+1]*trans["gamma"]
        end
        dw[end] += w[end-1]*trans["beta"]
        #@assert(sum(dw) == 0.0)
   
        w = w .+ dw
        w = w ./ sum(w)
        chg = maximum(abs.(dw)) # this is perhaps over the top, but works.
        if w[1] == w[2] == 0.0  
            # Special case: both the bottom bins are empty: 
            # is transient, and no need to continue.
            chg = 0.0
        end
    end

    w0 = w[1]
    prob = Dict("cost"=>0.0, "benefit"=>0.0)
    for key in keys(prob)
        # no conditioning here, so we get the joint prob: a product of appropriate Sx and Sy probs.
        total = 0.0
        for case in cases[key]  # Note: case[2] is Sy
            pr = 1.0
            if case[1]==0 pr *= w0 else pr *= (1-w0) end
            if case[2]==0 pr *= w0 else pr *= (1-w0) end  # ie. quadratic terms are possible
            total += pr
        end
        prob[key] = total/4.0 
    end    
    fit = BENEFIT*prob["benefit"] - COST*prob["cost"]

    if VERBOSE
        @printf("STRATEGY: %s \nw stable: ", A["name"])
        for i in 1:min(5,length(w))  @printf("%.3f  ",w[i])   end
        @printf("...(n=%d)\n", n)
        @printf("mean score:  \t %.4f\n",sum(w .* collect(0:n)))
        @printf("mean fitness:\t %.4f\n",fit)
    end

    return w, n, fit
    
end




"""
    Find stable score distribution of an infinite population 
    consisting of a mixture of two species.
    A and B are two strategies that form the whole of an infinite population.
    rhoA is the relative density of A in that population.
    wA_init is an initial density of scores for A, e.g. [.6, .3, .1] would 
    mean a population with 60% having score=0, 30% have 1, and 10% have 2.
    We run a Markov Chain with two possible end conditions:
    exit if the max change to score densities is less than "tolerance", and
    exit if the number of bins exceeds "maxn".
"""
function calc_stable_w_2species(A, B; rhoA=0.5, wA_init=[0.5,0.5], wB_init=[0.5,0.5], tolerance=1e-5, maxn=1000, VERBOSE = false, FORCE_UNTIL_MAXN=false)
    """
    similar to 1species, but with 2 species.
    Handling the interactions right is extremely finicky.
    # Note: by setting maxn=0, one can evaluate fitness of A immediately.
    """
    chainA, chainB = Dict(), Dict()
    chainA["name"] = A["name"]
    chainB["name"] = B["name"]
    chainA["rho"], chainB["rho"] = rhoA,  1-rhoA
    chainA["self"], chainA["other"] = A, B
    chainB["self"], chainB["other"] = B, A
    chainA["w"] = copy(wA_init)
    chainB["w"] = copy(wB_init)
    for ch in [chainA, chainB]
        ch["cases_withSelf"]  = build_interaction_cases(ch["self"], ch["self"])
        ch["cases_withOther"] = build_interaction_cases(ch["self"], ch["other"])
        ch["trans"] = Dict("alpha"=>0.0, "beta"=>0.0, "gamma"=>0.0)    
        ch["n"] = length(ch["w"])
    end
        
    
    global max_chg = 1.0
    global counter = 0
    # until things stabilise, or someone's scores get crazy big...
    while counter < maxn  && (max_chg > tolerance || FORCE_UNTIL_MAXN)  
        # this WAS: while max(chainA["n"], chainB["n"]) < maxn && etc.
        # but that makes it return too soon should it be started with a long chain already.
        # Really, we'd like it to go around lots of times HERE, regardless of the history of w from before.
        counter += 1
        
        for ch in [chainA, chainB]
            ch["n"]  = length(ch["w"])
            push!(ch["w"],0.0)
        end
        
        # find the new transition rates, for both chains
        for ch in [chainA, chainB]
            if ch==chainA chOther=chainB else chOther=chainA end 
            w0, w0Other = ch["w"][1], chOther["w"][1] 
            for key in keys(ch["trans"])
                grandTotal = 0.0
                total = 0.0
                for case in ch["cases_withSelf"][key]
                    if case[2]==0 total += w0 else total += (1-w0) end    # Note: case[2] is Sy
                end
                grandTotal += ch["rho"] * total
                total = 0.0
                for case in ch["cases_withOther"][key] 
                    if case[2]==0 total += w0Other else total += (1-w0Other) end    # Note: case[2] is Sy
                end
                grandTotal += chOther["rho"] * total
                ch["trans"][key] = grandTotal/4.0 # the 1/4 is the p(Cx) * p(Cy) of this case.
            end
        end    
        
        # And now do one step with those transition rates, throughout each chain (these are entirely separable).
        global max_chg=0.0
        for ch in [chainA, chainB]
            w = ch["w"]
            t = ch["trans"] # the three transitions: alpha, gamma, beta
            ch["dw"] = zeros(length(w))
            dw = ch["dw"]
            dw[1] += -w[1]*t["alpha"] + w[2]*t["gamma"]  # change to w0
            dw[2] += -w[2]*t["gamma"]  -w[2]*t["beta"]   + w[1]*t["alpha"] + ch["w"][3]*t["gamma"] # change to w0
            for i in 3:ch["n"]
                dw[i] += -w[i]*t["gamma"] -w[i]*t["beta"]   + w[i-1]*t["beta"] + w[i+1]*t["gamma"]
            end
            dw[end] += w[end-1] * t["beta"]
            w = w .+ dw
            w = w ./ sum(w)
            max_chg = max(max_chg,  maximum( abs.(dw) ))
            ch["w"] = w # NECESSARY, as we haven't changed the actual chain yet.
        end
                
        if chainA["w"][1:2] == chainB["w"][1:2]  == [0.0, 0.0]  
            max_chg = 0.0 # Special case: the bottom bins are empty, for both species. Both chains transient, no need to continue.
        end
    end


    ################# calculate the (final) fitnesses.
    for ch in [chainA, chainB]
        if ch==chainA chOther=chainB else chOther=chainA end
        w0, w0Other = ch["w"][1], chOther["w"][1] 
        prob = Dict("cost"=>0.0, "benefit"=>0.0)
        for key in ["cost", "benefit"]
            # no conditioning here, so calc joint prob: a product of the prob(Sx) and prob(Sy).
            grandTotal = 0.0
            # first, encounters with Self
            total = 0.0
            for case in ch["cases_withSelf"][key]
                pr = 1.0
                if case[1]==0 pr *= w0 else pr *= (1-w0) end  # Note: case[1] is Sx, ie. Self
                if case[2]==0 pr *= w0 else pr *= (1-w0) end  # Note: case[2] is Sy, ie. also Self
                total += pr
            end
            grandTotal += total * ch["rho"]
            # now, encounters with Other
            total = 0.0
            for case in ch["cases_withOther"][key]
                pr = 1.0 
                if case[1]==0 pr *= w0 else pr *= (1-w0) end           # Note: case[1] is Sx, ie. Self
                if case[2]==0 pr *= w0Other else pr *= (1-w0Other) end # Note: case[2] is Sy, ie. Other
                total += pr
            end
            grandTotal += total * chOther["rho"]
            prob[key] = grandTotal/4.0 # the 1/4 is the p(Cx) * p(Cy) of this case.
        end
        #@printf("A: prob[benefit] %.3f \t prob[cost] %.3f \n", prob["benefit"], prob["cost"])
        ch["fit"] = BENEFIT*prob["benefit"] - COST*prob["cost"]
    end
    
    
    if VERBOSE
        for ch in [chainA, chainB]
            @printf("STRATEGY: %s (rho=%.3f)\nw stable: ", ch["name"], ch["rho"])
            for i in 1:min(5,length(ch["w"]))  @printf("%.3f  ",ch["w"][i])   end
            @printf("... (n=%d)\n", ch["n"])
            @printf("mean score:  \t %.4f\n",sum(ch["w"] .* collect(0:length(ch["w"])-1))) #offset: julia ix from 1.
            @printf("mean fitness:\t %.4f\n\n",ch["fit"])
        end    
    end
    return chainA, chainB # these 2 dicts already contain the three things (w,n,fit) we want, so can return them directly.
end


#= 
NOTE this function is really BinvadesA_even_if_only_by_neutral_drift !!
=#
function BinvadesA(nameA, nameB; w_init=[.5,.5], limitn=1000, rhoA=1-1e-6, VERBOSE=false, ALLOW_NEUTRAL_INVASION=true)
    """
    Maynard-Smith and Price criteria for ESS is as follows. 
    They say a strategy `A` is ESS (ie. *un*-invadeable) if, for *every* B != A,
    EITHER 
      E(A,A) >  E(B,A)  ie. a rare B would be actively die out in a popn of A. 
    OR
      E(A,A) == E(B,A)  AND   E(A,B) > E(B,B), 
    i.e. B matches A in a popn of A, but A would invade pure B from rare.
    
    Our definition of `B can invade A' should be consistent.
    It should be the exact negation of itemwise part of the ESS definition, which is:
      Not (E(A,A) >  E(B,A))  AND  Not (E(A,A) == E(B,A) && E(A,B) > E(B,B))
    so that if this BinvadesA returns true, it would also have caused a failure of 
    A to be ESS in MaynardSmith-Price-ESS-finder.jl
    
    NOTE: sometimes we might want to exclude invasions that would only
    occur by neutral drift (at both extremes). 
    So we include a flag, ALLOW_NEUTRAL_INVASION, which defaults to true.
    
    Algorithm:
    First, run a rare B in a popn of A.
    If B is strictly worse, return false: B cannot invade.
    If B is strictly better, return true: clearly B can invade. 
    Only if they're equal do we consider the case of B becoming common.
    Run a rare A in a popn of B. IF A does strictly better, return false (B cannot actually invade). 
    Otherwise we return true: B could invade neutrally and even if it gets common, A can't beat it.
    """
    stratA = name2strategy(nameA)
    stratB = name2strategy(nameB)
    
    resultA, resultB = calc_stable_w_2species(stratA, stratB; 
        wA_init=copy(w_init), wB_init=copy(w_init), rhoA=rhoA, maxn=limitn)
    # Note: by setting maxn=0, one can evaluate fitness of A immediately.
    if resultA["fit"] > resultB["fit"] 
        return false  #B actively excluded 
    elseif resultA["fit"] < resultB["fit"]
        return true   #B actively invades
    else
        # B could invade from rare NEUTRALLY. So we check what happens when B gets common.
        reversedA, reversedB = calc_stable_w_2species( stratA, stratB; 
            wA_init=copy(w_init), wB_init=copy(w_init), rhoA=1-rhoA, maxn=limitn)
        if ALLOW_NEUTRAL_INVASION 
            return (reversedB["fit"] >= reversedA["fit"])
            #B neutrally invades, and A can't actively beat it as it grows.
        else
            return (reversedB["fit"] >  reversedA["fit"])
            #B neutrally invades, and then actively excludes A.
        end
    end
        
    return true
end



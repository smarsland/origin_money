"""
Find all the ESS strategies.

A strategy is ESS if 

Try to do this in an efficient way:
within a loop over all strategies (playing the role of "common"), 
a naive option would be to go through all possible strategies as "rare".
But as soon as one is found that can invade, we know that the "common" one is NOT an ESS.
Accordingly, we will try the most promising invaders first in this inner loop, starting with 
score_user and score_maker, followed by all the partial mimics of the common strategy, and finally going through everything as a last resort.
"""

using Printf
using Dates
include("helper_funcs.jl")

function name_mimics(species_name, allspecies)
    mimic_substr_options = [
        "-r-","-r0","-r+","0r-","0r0","0r+","+r-","+r0","+r+",
        "-0-","-00","-0+","00-","000","00+","+0-","+00","+0+",
        "-g-","-g0","-g+","0g-","0g0","0g+","+g-","+g0","+g+"]
    mimics = []
    for i in [1,5,9,13]
        for option in mimic_substr_options
            tmp = collect(species_name)
            tmp[i:i+2] = collect(option)
            mimic = join(tmp)
            if mimic in keys(allspecies)  push!(mimics, mimic)   end
        end
    end
    return mimics
end
#----------------------------------------------------------------------------------------------

FULL_STRATEGY_SPACE = true #nb: set "false" if you ONLY want the score-conserving strategies.

allspecies = makeAllSpecies(FULL_STRATEGY_SPACE)  

# some to choose from...
if FULL_STRATEGY_SPACE
    prime_suspects = ["0r0,0g0|0r0,0g0", "000,+g-|-r+,+g-", "+0+,+g-|-r+,+g-"]
else
    prime_suspects = ["0r0,0g0|0r0,0g0", "000,+g-|-r+,+g-"]
end

#delete!(allspecies,"+0+,+g-|-r+,+g-")
#prime_suspects = ["0r0,0g0|0r0,0g0", "000,+g-|-r+,+g-"]


println("Number of species in total: ",length(allspecies),"\n\n")


# "testers" is everyone we would like to investigate as potential ESS's.
testers = keys(allspecies)  #["0r0,0g0|0r0,0g0", "000,000|000,000", "000,+g-|-r+,+g-", "+0+,+g-|-r+,+g-"]


startTime = time()
global c=0
all_the_ESS = []
for nameA in testers

    stratA = allspecies[nameA]
    global isESS = true
    global isInESSset = true
    global c += 1
    @printf("\r \t %8d \t %s   ",c,nameA)


    equalToA = [] # those strategies that are *potentially* in an ESS set with A.
    # If (as happens most often) A is eventually found not to be an ESS, this is ditched...
    
    # The order we go through B (invader) strategies in can be random, or sensible (!).
    # The sensible one differs for each A strategy:
    #   first, we check the main invaders we know about, then the mimics, then everyone
    #   take an early exit as soon as you find an invader.
    # Maynard-Smith and Price criteria for ESS is that, for *every* B != A,
    # EITHER 
    # E(A,A) >  E(B,A)  ie. a rare B would be actively die out in a popn of A. 
    # OR
    # E(A,A) == E(B,A)  AND   E(A,B) > E(B,B), i.e. B matches A in a popn of A, but 
    #                                          A would invade pure B from rare.
    #
    bigList = cat(prime_suspects, name_mimics(nameA,allspecies), collect(keys(allspecies)), dims=1)
    for nameB in bigList
        if nameB != nameA
            stratB = allspecies[nameB]
            resultA, resultB = calc_stable_w_2species(stratA, stratB; rhoA=0.99, maxn=100)
            if (resultA["fit"] > resultB["fit"])
                continue  # A is safe from rare B, so move on to next B contender
            elseif (resultA["fit"] == resultB["fit"]) # they're equal when A common, so we need more evidence...
                newresultA, newresultB = calc_stable_w_2species(stratA, stratB; rhoA=0.01, maxn=100)
                if (newresultA["fit"] > newresultB["fit"])
                    continue # Although common A tolerates some B, common B would 
                             # lose to rare A, so A's still safe: move on to next B contender.
                elseif (newresultA["fit"] == newresultB["fit"]) # ie. they're equal, regardless of who is common.
                    global isESS = false
                    if (newresultA["fit"] > 0) # we can add this to those equal to A.
                                 # nb. A is not strictly an ESS, but might be part of ESS set.
                        push!(equalToA, nameB)
                        #@printf("\t mutual with some (eg) %s \t(fit=%.3f)\n",nameB,fitA2) end
                        continue # since we do want to collect the set for a look...
                    else 
                        break # just ditch this A and move on.
                    end
                else  # ie. A sucks! It tolerates some B, yet loses to B if B get going.
                    global isESS = false
                    global isInESSset = false
                    break
                end
            else # this is the case that rare B actively beats up common A, so A isn't ESS.
                #@printf("\t actively invaded by (eg) %s\n",nameB)
                global isESS = false
                global isInESSset = false
                break
            end
        end        
    end
    
    # we've checked everything -- report back if it really is an ESS
    if isESS 
        @printf("\n\n%s is ESS.",nameA)
        w, nn, fit = calc_stable_w_1species(stratA)
        if fit < 1e-5
            @printf("\t But a boring one: fitness is %f\n",fit)
        else
            @printf("\nDETAILS:\n")
            calc_stable_w_1species(name2strategy(nameA); VERBOSE=true)
            
            
            global countThisInvades=0
            for B in keys(allspecies)
                local resultA, resultB = calc_stable_w_2species(stratA, allspecies[B]; rhoA=1e-6, maxn=100)
                if resultA["fit"] > resultB["fit"]
                    global countThisInvades += 1
                end
            end
            @printf("%s can ACTIVELY invade %d other strats from rare\n\n",nameA,countThisInvades)
            push!(all_the_ESS, nameA)
        end

    else
        if isInESSset #length(equalToA) > 0
            w, nn, fit = calc_stable_w_1species(stratA)
            if fit > 0.0
                @printf("\n\t\tNOT strict ESS, but has fitness %f, is == to these:\n", fit)
                for z in unique(equalToA)  @printf("\t\t%s\n",z) end
            end
        end
    end
end
@printf("\n\n")
@printf("That took %.0f seconds\n",time() - startTime)

println("All the ESS that have fitness above 0:")
for name in all_the_ESS
    @printf("%s\n",name)
end


"""
Explore who is able to invade (say) Money
"""

using Printf
using Dates
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------
# Lots of things to choose here:

allspecies = makeAllSpecies(true)  #nb: call with "false" if you want the score-conserving strategies only.
ALLOW_NEUTRAL_INVASION = false
# Note that entirely neutral "invasions" are legitimate (they count as invasions)
# when assessing whether something is an ESS. 
# It's a decision about what you're interested in knowing about.
MUTANT_SCORES = "late" # "early" or "late"
# "early" means early in the scoring season, i.e. right from the beginning,
# both species are altering their score distributions, which both start the same
# "late" means late in the season, i.e. the common strategy runs until stability,
# then a mutation occurs, so the rare species then starts with the commoners'
# score distribution. Both run from there to stability.
MAXN = 100
RARITY = 1e-6
VERBOSE = false
nameA = "000,+g-|-r+,+g-"

#----------------------------------------------------------------------------------------------



println("Number of species in total: ",length(allspecies))
@printf("MUTANT_SCORES is %s \n",MUTANT_SCORES)
@printf("ALLOW_NEUTRAL_INVASION is %s \n\n",ALLOW_NEUTRAL_INVASION)
stratA = name2strategy(nameA)
@printf("WHO CAN INVADE %s?\n",stratA["name"])

if MUTANT_SCORES == "early"
    w_init = [0.5,0.5]
else
    wA_alone, nA_alone, fitA_alone = calc_stable_w_1species(stratA; maxn=MAXN)
    w_init = wA_alone
end

possibleInvaders = setdiff( keys(allspecies), [nameA]) # try all except for A itself.
count = 1
for nameB in possibleInvaders
    stratB = name2strategy(nameB)
    @printf("\r%8d  %s\t",count,nameB)
    global count += 1
    if BinvadesA(nameA, nameB; w_init=copy(w_init),
                rhoA=1-RARITY, limitn=MAXN,
                ALLOW_NEUTRAL_INVASION=ALLOW_NEUTRAL_INVASION)
                
        @printf("\rinvaded by     %s \n",nameB)
        if VERBOSE
            resA_comm, resB_rare = calc_stable_w_2species(stratA, stratB; rhoA=1-RARITY, maxn=MAXN)
            resA_rare, resB_comm = calc_stable_w_2species(stratA, stratB; rhoA=RARITY, maxn=MAXN)      
            
            @printf("\t FITNESSES (early): A common: A=%.3f, B=%.3f \t\t B common: A=%.3f, B=%.3f\n",
                     resA_comm["fit"],resB_rare["fit"],
                     resA_rare["fit"],resB_comm["fit"])
            
            resA_comm, resB_rare = calc_stable_w_2species(stratA, stratB; 
                wA_init=copy(w_init), wB_init=copy(w_init), rhoA=1-RARITY, maxn=MAXN)
            @printf("\t FITNESSES (late) : A common: A=%.3f, B=%.3f\n",
                     resA_comm["fit"],resB_rare["fit"])
            @printf("\t wA (late) %s \n",resA_comm["w"][1:4])
            @printf("\t wB (late) %s \n",resB_rare["w"][1:4])
            @printf("\t nA (late) %s \n",resA_comm["n"])
            @printf("\t nB (late) %s \n",resB_rare["n"])
        end        
    end
end
@printf("\r                                               \n")

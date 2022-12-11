using Printf
using Dates
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------


# just some to choose from...
money      = "-r+,+g-" 
spender    = "-r+,000" 
scoremaker = "+0+,+0+" 
naive      = "0r0,0g0" 
moneymaker = "+0+,+g-|-r+,+g-"



nameB = "+0+,+g-|-r+,+g-"
allspecies = makeAllSpecies(true)  #nb: call with "false" if you want the restricted strategies only.
stratB = name2strategy(nameB)
@printf("------------ how many can %s  *actively* invade from rare? --------\n",nameB)
@printf("A definition: there are two ways that rare B to invade common A.\n")
@printf("EITHER fitnessB > fitnessA when B is rare, \n")
@printf("OR they're equal then (a strictly neutral start for B) but fitnessB > fitnessA when B common (ie. strong finish)\n\n")


counter=0
countTheInvaded=0
println("Number of species in total: ",length(allspecies),"\n\n")
startTime = time()
for nameA in setdiff(keys(allspecies), nameB)
    global counter += 1
    @printf("\r%d \t %d",counter, countTheInvaded)
    
    if BinvadesA(nameA, nameB; rhoA=0.99)
        global countTheInvaded += 1
    end
end

@printf("\n%s invades %d\n",nameB,countTheInvaded)
@printf("\n%s invades %d\n",nameB,ALTcountTheInvaded)
@printf("That took %.0f seconds\n",time() - startTime)




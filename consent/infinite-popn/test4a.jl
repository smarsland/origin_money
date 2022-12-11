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


println("------------ how many can strategy A (e.g. money) *actively* invade from rare? --------")

#A = "-r+,+g-"
#A = "+0+,+g-|-r+,+g-"
A = "000,+g-|-r+,+g-"
B = "+0+,+g-|-r+,0r0"
#allspecies = makeAllSpecies(false)  #nb: call with "false" if you want the restricted strategies only.
Astrat = name2strategy(A)
Bstrat = name2strategy(B)

wA, nA, fitA, wB, nB, fitB = calc_stable_w_2species(Astrat, Bstrat; rhoA=0.01, tolerance=0.001, maxn=1000,VERBOSE=true)



using PlotlyJS
using Printf
using Dates
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------


allspecies = makeAllSpecies()  #nb: call with "false" if you want the restricted strategies only.

stratA = name2strategy("000,+g-|-r+,+g-")
stratB = name2strategy("+0+,+g-|-r+,+g-")


for t in 1:20
    resA, resB = calc_stable_w_2species(stratA, stratB; rhoA=0.99, tolerance=0.01, maxn=t)
    global p = plot(scatter(x=float(t),y=resA["fit"))
#    p = plot(t,fitB)
end
p


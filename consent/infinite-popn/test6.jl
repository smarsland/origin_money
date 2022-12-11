"""
Take 2 strategies.
Vary their relative density.
Get their payoffs as the density is varied.
Maybe make a plot or something.
"""

using Printf
using PlotlyJS
using DataFrames
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------

A = "+0+,+g-|-r+,+g-"  # the blue one
B = "+0+,+g-|-r+,+0+"  # the other one

rhos = collect(0.05:0.05:0.95) # options for rho

fitAs, fitBs = [], []
for rhoA in rhos
    resultA, resultB = calc_stable_w_2species(
        name2strategy(A),name2strategy(B); rhoA=rhoA, maxn=1000)
    push!(fitAs, resultA["fit"]) 
    push!(fitBs, resultB["fit"]) 
end

df = DataFrame(rhos=rhos, fitAs=fitAs, fitBs=fitBs)
#p=plot(df, kind="scatter", mode="lines", x=:rho)
p=plot(
    [scatter(df, x=:rhos, y=:fitAs, name=A,line_color="blue",marker_color="blue"), 
     scatter(df,x=:rhos,y=:fitBs,name=B,line_color="orange",marker_color="orange")],
     Layout(title="fitness vs density (of blue)") 
)
savefig(p,"test6-output.png")

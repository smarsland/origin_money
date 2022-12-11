"""
Take final 11 strategies.
Vary their relative density.
Get their payoffs as the density is varied.
Maybe make a plot or something.
"""

using Printf
using PlotlyJS
using DataFrames
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------

oceans11 = [
    "00-,+g-|-r+,+g-",
    "000,+g-|-r+,+g-",
    "00+,+g-|-r+,+g-",
    "+0-,+g-|-r+,+g-",
    "+00,+g-|-r+,+g-",
    "+0+,+g-|-r+,+g-",
    "0r-,+g-|-r+,+g-",
    "0r0,+g-|-r+,+g-",
    "0r+,+g-|-r+,+g-",
    "+r-,+g-|-r+,+g-",
    "+r0,+g-|-r+,+g-",
    "+r+,+g-|-r+,+g-",
    ]

oceans12 = vcat(oceans11, "+00,00+|-r+,+00")
#push!(oceans12, "000,000|000,000")

println(length(oceans11))
println(length(oceans12))


commFitness = zeros(length(oceans11), length(oceans12))
rareFitness = zeros(length(oceans11), length(oceans12))

ci = 1
for A in oceans11
    cvals = []
    rvals = []
    for B in oceans12
        wA,nA,fitA,wB,nB,fitB = 
            calc_stable_w_2species(name2strategy(A),name2strategy(B); rhoA=0.99)
        push!(cvals, fitA)
        push!(rvals, fitB)
    end
    commFitness[ci,:] = cvals
    rareFitness[ci,:] = rvals
    global ci += 1
end

#=
trace = heatmap(x=oceans12, y=oceans11, z=commFitness, 
                colorscale="hot", zmin=-0.1, zmax=0.1)
layout= Layout(title="Fitness of common",# xaxis_side="top", 
        xaxis_title="rare", yaxis_title="common")
p1=plot(trace, layout)
savefig(p1,"last11-heatmap1.png")


trace = heatmap(x=oceans12, y=oceans11, z=rareFitness,
                colorscale="hot", zmin=-0.1, zmax=0.1)
layout= Layout(title="Fitness of rare",# xaxis_side="top", 
        xaxis_title="rare", yaxis_title="common")
p2=plot(trace, layout)
savefig(p2,"last11-heatmap2.png")
=#

diff  = rareFitness-commFitness

trace = heatmap(x=oceans12, y=oceans11, z=diff, 
                colorscale="hot", zmin=-0.02, zmax=0.02)
layout= Layout(title="Fitness advantage, for rare",# xaxis_side="top", 
        xaxis_title="rare", yaxis_title="common")
p3=plot(trace, layout)

filename = "monies-heatmap.png"
savefig(p3, filename)
println("Wrote ",filename)

#p = [p1,p2]
#relayout!(p, title_text="Side by side layout (1 x 2)")

#savefig(p,"last11-heatmap.png")

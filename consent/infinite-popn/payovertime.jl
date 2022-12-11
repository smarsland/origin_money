"""
plot of payoff versus time
"""

using Printf, LaTeXStrings

#using DataFrames
include("helper_funcs.jl")

using Plots
#plotlyjs() # Tells Plots to use the PlotlyJS back-end.
gr() # or use the GR backend
p=plot(xaxis=:log); 
#----------------------------------------------------------------------

allspecies = makeAllSpecies(true)  #nb: call with "false" if you want the restricted strategies only.

RHOS        = [0.01,  0.1,   0.5]
lineStyles  = [:dot,  :dash, :solid]
lineColours = [:red,  :gray, :blue]
MAXN = 10100

Cs= ["000,+g-|-r+,+g-"]
Rs= ["+0+,+g-|-r+,+g-"]

#push!(Cs, "00+,+g-|-r+,+g-")
#push!(Rs, "+00,+g-|-r+,+g-")

#push!(Cs, "+00,+g-|-r+,+g-")
#push!(Rs, "00+,+g-|-r+,+g-")

#for i in 1:10
#    push!(Cs, rand(keys(allspecies)))
#    push!(Rs, rand(keys(allspecies)))
#end

for i in 1:length(Cs)
    C = Cs[i]
    R = Rs[i]
    for (RARE_RHO, lineStyle, lineColour) in zip(RHOS, lineStyles, lineColours)

        cvals = []
        rvals = []
        # this loop is dumb, as it does not reuse earlier timeseries. Gets too slow for >1000 steps.
        # Doing so is sensible, and works (see the MAXN>100 section below), HOWEVER
        # there seems to be an off-by-one error in setting maxn that increments (by 1) previous w_init.
        # That should be fixed, but meanwhile, I'm just running the first 100 brute force,
        # and from then on incrementally, since the off-by-one error isn't a feature anymore.
        # Nb. I have confirmed the figure is the same as if you'd just done brute-force the whole way.
        for t in 1:min(100,MAXN)
            println(t)
            wR,nR,fitR,wC,nC,fitC = 
                calc_stable_w_2species(name2strategy(R),name2strategy(C); 
                    rhoA=RARE_RHO, maxn=t, FORCE_UNTIL_MAXN=true)
            push!(rvals, fitR)
            push!(cvals, fitC)
        end
        if MAXN>100
            wR,nR,fitR,wC,nC,fitC = 
                    calc_stable_w_2species(name2strategy(R),name2strategy(C); 
                        rhoA=RARE_RHO, maxn=100, FORCE_UNTIL_MAXN=true)
                
            for t in 101:MAXN
                println(t)
                wR,nR,fitR,wC,nC,fitC = 
                    calc_stable_w_2species(name2strategy(R),name2strategy(C); 
                        rhoA=RARE_RHO, wA_init=wR, wB_init=wC, maxn=t, FORCE_UNTIL_MAXN=true)
                push!(rvals, fitR)
                push!(cvals, fitC)
            end        
        end                
        plot!(p, rvals[2:end], 
                fillrange=cvals[2:end], fillalpha=0.2, 
                color=lineColour,  line=(:solid,1),  label=L"$\rho=$"*string(RARE_RHO)) 
        plot!(p, rvals[2:end], color=lineColour, line=(:solid,1),  label="") 
        plot!(p, cvals[2:end], color=lineColour, line=(:solid,4), label="") 
        #    label=C*" "*string(RARE_RHO)) 
        
    end
    plot!(p, title="payoffs vs time, for different densities", 
            xlabel="number of interactions per agent",
            ylabel="mean payoff \n (thick line: money, thin: money-maker)",
            ylims=(0.07,0.25), yticks=0.1:0.05:0.25,  xticks=[1,10,100,1000,10000],
            legend=(.1, 0.9),
            ) #legendtitle=L"my $x^2$ legend")
    savefig(p,"payovertime" * string(i) * ".png")
end


include("helper_funcs.jl")
strats = makeAllstrategies()
#println("cases are indexed like this: [Sx, Sy, Cx, Cy], where S:Score>0, C:Can")

bbname = "CmeetsN:000000++ NmeetsC:000000-- NmeetsN:0000" 
#bbname = "CmeetsN:+---0--- NmeetsC:00000000 NmeetsN:0000" #W1 10001000 


BigB = name2bigbrother(bbname)
#println(convertToHilbeNotation(bbname[7:14]) * " " * convertToHilbeNotation(bbname[22:29]))

SCORES_ARE_BINARY = false
WSTART = [.5,.0,.5]
noiseval = 0.01

#X = strats["0,g|0,g"]
X = strats["0,0|g,g"]
#= Suppose X is common. What's it's outcome alone under this BigB? =#
w, fit, trans = calc_stable_w_1strategies(
                            X, BigB;
                            w_init=WSTART,
                            SCORES_ARE_BINARY=SCORES_ARE_BINARY, 
                            FORCE_UNTIL_MAXN=false,ALLOW_NEGATIVE_SCORES=false,
                            NOISE_VAL=noiseval)
@printf("\t comm \t%s \t %.3f :\t %.3f \t %.3f \t %.3f\n",X["name"],fit,w[1],w[2],w[3])
println("----------------------")

for Y in values(strats)
    #=
    Suppose Y is very RARE, so it only interacts with these X's.
    What mean payoff does Y get?
    =#    
    resX, resY = calc_stable_w_2strategies(X, Y, BigB; 
                rhoA=1.0, 
                wA_init=WSTART, wB_init=WSTART,
                SCORES_ARE_BINARY=SCORES_ARE_BINARY,
                FORCE_UNTIL_MAXN=false,ALLOW_NEGATIVE_SCORES=false,
                NOISE_VAL=noiseval)
    #println(keys(resY))
    if resY["fit"] <  fit print("     ") end
    if resY["fit"] == fit print("==== ") end
    if resY["fit"] >  fit print("<<<< ") end
    @printf("rare \t%s \t %.3f :\t %.3f \t %.3f\n", Y["name"], resY["fit"], resY["w"][1], resY["w"][2])
end




#=
println("******************** c.f. EACH AS COMMON *********************")
for X in values(strats)
    #= Suppose X is common. What's it's outcome alone under this BigB? =#
    w2, fit2, trans2 = calc_stable_w_1strategies(
                                X, BigB;
                                w_init=WSTART,
                                BINARY_SCORES=BINARY_SCORES, 
                                FORCE_UNTIL_MAXN=false,
                                NOISE_VAL=noiseval)
    if fit2 <= fit print("     ")  else print(" !!  ") end
    @printf("comm \t%s \t %.3f :\t %.3f \t %.3f\n",X["name"],fit2,w2[1],w2[2])
end
println("----------------------")
=#

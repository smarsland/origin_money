include("helper_funcs.jl")
#println("cases are indexed like this: [Sx, Sy, Cx, Cy], where S:Score>0, C:Can")

REPUTATION=:tokens 
#REPUTATION=:binary #,:tokens,:scores] # binary, tokens, scores
#WSTART_OPTIONS = [[.5,0,.5],[.5,0,0,0,.5],[.5,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5],[.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.5]]
WSTART_OPTIONS = [[0,0,0,0,0,0,1]]#[0.00001,0,0,0,0,0,.99999],[.01,0,0,0,0,0,.99]]
#WSTART_OPTIONS = [[.01,0,.99],[.01,0,0,0,.99],[.01,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.99],[.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,.99]]
#WSTART = [.5,.0,0,0,0,0,0,0,.5]
#WSTART_OPTIONS = [[0,0,1],[0,0,0,0,1],[0,0,0,0,0,0,1],[0,0,0,0,0,0,0,0,1]]
noiseval = 0.01

BENEFIT = 2
COST = 1
MINFITNESS = 0.01
RHOA = 0.99
MAXN = 500
# Need to specify an odd number of slots (at least -1, 0, 1)
# Don't always specify the -1 slot, so this puts it in
strategyOptionsDict =  makeAllstrategies()
strategyOptionsList = collect(values(strategyOptionsDict))
    
@printf("#Reputation type: %s,\t noise: %.3f, ", REPUTATION, noiseval)
@printf("# BENEFIT %s, COST %s ", string(BENEFIT), string(COST))

                                                                
#name = "CmeetsN:00000000 NmeetsC:00000000 NmeetsN:0000"        
#name = "CmeetsN:++++0-++ NmeetsC:+0++0000 NmeetsN:0000"        
#name = "CmeetsN:++++0-0+ NmeetsC:00000000 NmeetsN:0000"        
name = "CmeetsN:000000++ NmeetsC:000000--" # money 
#name = "CmeetsN:0000000+ NmeetsC:0000000- NmeetsN:0000" 
#name = "CmeetsN:00000-++ NmeetsC:00000000 NmeetsN:0000"
#name = "CmeetsN:++++++++ NmeetsC:++++++++ CmeetsC:0000 NmeetsN:++++"
#name = "CmeetsN:-------- NmeetsC:-------- CmeetsC:0000 NmeetsN:----"
#name = "CmeetsN:00-00000 NmeetsC:00-00000 CmeetsC:0000 NmeetsN:0-00"
#name = "CmeetsN:00+00-++ NmeetsC:000++-00 CmeetsC:0000 NmeetsN:0000"
BigB = name2bigbrother(name)
for WSTART in WSTART_OPTIONS
if iseven(length(WSTART))
    for i in 1:length(WSTART)-1
        insert!(WSTART,2*i,0.) 
    end                     
end                         
                            
@printf("*******************************************************\n Winit %s\n", string(WSTART))
tier = 0                
                        
name_best_ESS, best_fitness, best_score = small_test(strategyOptionsList,BigB;
                                            threshold_fitness=MINFITNESS,
                                            REPUTATION=REPUTATION,
                                            WSTART=WSTART, maxn=MAXN, rhoA=RHOA, noiseval=noiseval,
                                            BENEFIT=BENEFIT,COST=COST,VERBOSE=true)

@printf("#ESS %s\t %s %sFITNESS %.5f \t %f\n", name_best_ESS, name[1:33], "__ "^tier, best_fitness,best_score)
end

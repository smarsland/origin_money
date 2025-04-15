using ArgParse
using CSV
using DataFrames
include("helper_funcs.jl")

#---- PARAMETERS ----#
REPUTATION=:tokens # :scores :binary
ALLOWABLE_BB_PARTS = ["CmeetsN"]
WSTART = [0.5,0,0.5] 
#WSTART = [0,0,1] 
#WSTART = [.5,.0,.0,.0,.0,.0,.0,.0,.0,.0,.5] 
#NOISE_opts = [0,0,0.01,0.02, 0.05,0.1,0.2,0.3, 0.5]
NOISE_opts = [0.01,0.05,0.1,0.2] #,0.02,0.05,0.1,0.2,0.3,0.4,0.5]
BENEFIT = 2
COST = 1
MINFITNESS = 0.01
RHOA = 0.99
MAXN = 100

printing_rate = 0

#---- CODE ----#

function check_hamming_variants(theBB, tier, threshold_fitness)
    tops = []
    top_option_fitness = threshold_fitness
    options = ['-','0','+']
	for chunk in ALLOWABLE_BB_PARTS
		for i in 1:2
		for j in 1:2
		if chunk in ["CmeetsN", "NmeetsC"] K=2; else K=1; end
		for k in 1:K
			tmpBB = deepcopy(theBB)  # i.e. reset it back to the 'base' BB.
		    for option in options
				if chunk in ["CmeetsN", "NmeetsC"]
					tmpBB[chunk][i][j][k] = option
				else
					tmpBB[chunk][i][j] = option
				end
				tmpBB["name"] = bigbrother2name(tmpBB)
				
				name_best_ESS, best_fitness = small_test(tmpBB;
					    threshold_fitness=threshold_fitness,
					    REPUTATION=REPUTATION,printing_rate=printing_rate,
					    WSTART=WSTART, maxn=MAXN, rhoA=RHOA, noiseval=NOISE,
			    		    BENEFIT=BENEFIT,COST=COST)
				# if fitter is present, there was an ESS success (or several)
				# with this BB, so we're to recurse, looking for more that are better.
				if (name_best_ESS != nothing)
				    top_option = Dict()
				    top_option["BB"] = tmpBB
				    top_option["ESSname"] = name_best_ESS
				    top_option["fitness"] = best_fitness
				    if (best_fitness > top_option_fitness + 1e-5)
					    tops = [deepcopy(top_option)] # a list of dicts
					    top_option_fitness = best_fitness
                                    elseif (best_fitness >= top_option_fitness - 1e-4) # ie. runs a close 'second'
					    push!(tops, deepcopy(top_option))
				    end
				end
			end
		end # k loop
		end # j loop
		end # i loop
	end
	# AFTER all the options in all the slots have been tried... 
	# we pursue the best to the next tier.
	for t in tops
        # CHECK... println("CHECK: ", t["BB"]["name"], t["ESSname"], t["fitness"], top_option_fitness)
        #print("\n", t, "\n")
		name = bigbrother2name(t["BB"])
		name = replace(name, r"[0]" =>" ")

        # first form
	@printf("#ESS %s\t %s %sFITNESS %.5f\n", t["ESSname"], name, "__ "^tier, t["fitness"])

        # second form
        subs = split(bigbrother2name(t["BB"]), [' ',':'])
        @printf("%s %s %s ",subs[2],subs[4],subs[6])   
        @printf("%s ", t["ESSname"])
        @printf("%.3f ",t["fitness"])
        @printf("0.0 0.0 0.0 0.0 0.0 0.0 0.0\n")


        #################################### RECURSION ########
        #@printf("%f, %f \n",t["fitness"], BENEFIT-COST-1e-2)
        if t["fitness"] < BENEFIT-COST-1e-2
    		check_hamming_variants(t["BB"], tier+1, t["fitness"])
    	end
        #################################### RECURSION ########
	end
end

# Need to specify an odd number of slots (at least -1, 0, 1)
# Don't always specify the -1 slot, so this puts it in
if iseven(length(WSTART))
    for i in 1:length(WSTART)-1
        insert!(WSTART,2*i,0.) 
    end
end

for N in NOISE_opts
    global NOISE = N
    
    @printf("#Reputation type: %s,\t noise: %.3f, ", REPUTATION, NOISE)
    @printf("# BENEFIT %s, COST %s ", string(BENEFIT), string(COST))
    @printf("Winit %s\n", string(WSTART))

    name = "CmeetsN:00000000 NmeetsC:00000000 NmeetsN:0000"
    #name = "CmeetsN:000000++ NmeetsC:000000-- NmeetsN:0000" # might be money!
    #name = "CmeetsN:00+00000 NmeetsC:00+00000 CmeetsC:0000 NmeetsN:0+00"
    #name = "CmeetsN:++++++++ NmeetsC:++++++++ CmeetsC:0000 NmeetsN:++++"
    #name = "CmeetsN:-------- NmeetsC:-------- CmeetsC:0000 NmeetsN:----"
    #name = "CmeetsN:00-00000 NmeetsC:00-00000 CmeetsC:0000 NmeetsN:0-00"
    BigB = name2bigbrother(name)
    tier = 0
    name_best_ESS, best_fitness = small_test(BigB;
                                            threshold_fitness=0.0,
                                            REPUTATION=REPUTATION,printing_rate=printing_rate,
                                            WSTART=WSTART, maxn=MAXN, rhoA=RHOA, noiseval=NOISE,
                                            BENEFIT=BENEFIT,COST=COST)


    # first form
    @printf("#ESS %s\t %s %sFITNESS %.5f\n", name_best_ESS, name[1:42], "__ "^tier, best_fitness)
    #@printf("#ESS %s\t %s %sFITNESS %.5f\n", "0,0|0,0", name[1:42], "__ "^tier, 0.0)
    # 2nd form
    #@printf("00000000 00000000 0000 0,0|0,0 ")
    #@printf("0.000 ")
    #@printf("0.0 0.0 0.0 0.0 0.0 0.0 0.0\n")

    check_hamming_variants(BigB, 0, 0.01)
end

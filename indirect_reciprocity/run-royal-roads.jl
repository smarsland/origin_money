using ArgParse
using CSV
using DataFrames
include("helper_funcs.jl")

#---- PARAMETERS ----#
REPUTATION = :tokens  # :binary, :tokens, or :scores 
ALLOWABLE_BB_PARTS = ["CmeetsN","NmeetsC"]
CONSERVATIVE = false
WSTART = [0.5,0,0.5]
#WSTART = [0,0,0,0,0,0,0,0,0,0,1] 
NOISE  = 0.1
BENEFIT = 2
COST = 1
MINFITNESS = 0.01
RHOA = 0.99
MAXN = 200

#---- CODE ----#

function check_hamming_variants(strategyOptionsList, theBB, tier, threshold_fitness)
    tops = []
    top_option_fitness = threshold_fitness
    
	for chunk in ALLOWABLE_BB_PARTS
		for i in 1:2
		for j in 1:2
		if chunk in ["CmeetsN", "NmeetsC"] K=2; else K=1; end
		for k in 1:K
			tmpBB = deepcopy(theBB)  # i.e. reset it back to the 'base' BB.
			
			# Get current value to determine allowed transitions
			current_val = if chunk in ["CmeetsN", "NmeetsC"]
				theBB[chunk][i][j][k]
			else
				theBB[chunk][i][j]
			end
			
			# Only allow single-step transitions: - ↔ 0 ↔ +
			allowed_options = if current_val == '-'
				['0']  # from '-' can only go to '0'
			elseif current_val == '0'
				['-', '+']  # from '0' can go to '-' or '+'
			elseif current_val == '+'
				['0']  # from '+' can only go to '0'
			else
				[]  # no transitions allowed for other values
			end
			
		    for option in allowed_options
                if CONSERVATIVE
                    # Make NmeetsC from CmeetsN
					tmpBB["CmeetsN"][i][j][k] = option
                    negative_option = if option == '-'
                        '+'
                    elseif option == '+'
                        '-'
                    else
                        '0'
                    end
					tmpBB["NmeetsC"][i][j][k] = negative_option
                else
				    if chunk in ["CmeetsN", "NmeetsC"]
					    tmpBB[chunk][i][j][k] = option
				    else
					    tmpBB[chunk][i][j] = option
				    end
                end

				tmpBB["name"] = bigbrother2name(tmpBB)
				
                if tmpBB["name"] in collect(keys(BigBBs))
				     name_best_ESS, best_fitness = small_test(strategyOptionsList,tmpBB;
				      threshold_fitness=threshold_fitness,
				      REPUTATION=REPUTATION,
				          WSTART=WSTART, maxn=MAXN, rhoA=RHOA, noiseval=NOISE,
			           BENEFIT=BENEFIT,COST=COST,VERBOSE=false)
                    #@printf("%s, %s, %.2f  \n",tmpBB["name"],tmpBB["name"] in collect(keys(BigBBs)),best_fitness)
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
                 #else
                 #    @printf("Nah %s \n",tmpBB["name"] )
                 end
			end # end for option in allowed_options
		    end # k loop
		    end # j loop
		    end # i loop
	    end
	# AFTER all the options in all the slots have been tried... 
	# we pursue the best to the next tier.
	for t in tops
        # CHECK... 
        #println("CHECK: ", t["BB"]["name"], t["ESSname"], t["fitness"], top_option_fitness)
        #print("\n", t, "\n")
		name = bigbrother2name(t["BB"])
		name = replace(name, r"[0]" =>" ")

        # first form
	@printf("#ESS %s\t %s %sFITNESS %.5f\n", t["ESSname"], name, "__ "^tier, t["fitness"])

        # second form
        subs = split(bigbrother2name(t["BB"]), [' ',':'])
        @printf("%s %s ",subs[2],subs[4])   
        @printf("%s ", t["ESSname"])
        @printf("%.3f ",t["fitness"])
        @printf("0.0 0.0 0.0 0.0 0.0 0.0 0.0\n")


        #################################### RECURSION ########
        #@printf("%f, %f \n",t["fitness"], BENEFIT-COST-1e-2)
        if t["fitness"] < BENEFIT-COST-1e-2
    		check_hamming_variants(strategyOptionsList,t["BB"], tier+1, t["fitness"])
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

strategyOptionsDict =  makeAllstrategies()
strategyOptionsList = collect(values(strategyOptionsDict))
    
BigBBs = makeAllBB(;USE_CmeetsN="CmeetsN" in ALLOWABLE_BB_PARTS,  
                        USE_NmeetsC=("NmeetsC" in ALLOWABLE_BB_PARTS || CONSERVATIVE), 
                        REPUTATION=REPUTATION)

@printf("#Reputation type: %s,\t noise: %.3f, \t conservation: %s \n", REPUTATION, NOISE, string(CONSERVATIVE))
@printf("# BENEFIT %s, COST %s ", string(BENEFIT), string(COST))
@printf("Winit %s, maxn %s \n", string(WSTART), string(MAXN))

name = "CmeetsN:00000000 NmeetsC:00000000"
#name = "CmeetsN:000000++ NmeetsC:000000--" # money
BigB = name2bigbrother(name)

    all_the_ESS =  find_ESS(strategyOptionsList, strategyOptionsList, BigB; 
                            w_init=WSTART, rhoA=RHOA, 
                            threshold_fitness=MINFITNESS, 
                            maxn=MAXN,  VERBOSE=false, 
                            REPUTATION=REPUTATION,
                            NOISE_VAL=NOISE, BENEFIT=BENEFIT,COST=COST)
    		        
    if length(all_the_ESS) > 0  # if so, print the details...
        @printf("#%s has an ESS\n",name) 
    else
        @printf("#%s has no cooperative ESS\n",name) 
    end

tier = 0

if name in collect(keys(BigBBs))
    name_best_ESS, best_fitness, best_score = small_test(strategyOptionsList,BigB;
					    threshold_fitness=MINFITNESS,
					    REPUTATION=REPUTATION,
					    WSTART=WSTART, maxn=MAXN, rhoA=RHOA, noiseval=NOISE,
			    		    BENEFIT=BENEFIT,COST=COST,VERBOSE=false)

    # first form
    @printf("#ESS %s\t %s %sFITNESS %.5f\n", name_best_ESS, name[1:33], "__ "^tier, best_fitness)
    # 2nd form
            subs = split(name, [' ',':'])
            @printf("%s %s ",subs[2],subs[4])   
            @printf("%s ", name_best_ESS)
            @printf("%.3f ",best_fitness)
            @printf("0.0 0.0 0.0 0.0 0.0 0.0 0.0\n")

    check_hamming_variants(strategyOptionsList, BigB, tier, MINFITNESS)
end




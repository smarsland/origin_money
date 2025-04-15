#=
This script runs 'big_test' (in helper_funcs.jl) over sets of options, 
and writes to the output (for each option) to a file in data-default
=#
using ArgParse
using CSV
using DataFrames
include("helper_funcs.jl")

# ---- PARAMETERS ---- #
# Set up the options you want to iterate over here
USE_CmeetsN_options=[true]
USE_NmeetsC_options=[true]
USE_NmeetsN_options=[false]
REPUTATIONS_options=[:scores] #,:tokens,:scores] # binary, tokens, scores
WSTART_options = [[0.5,0,0.5]]#, [.5,0,0,0,0,0,0,0,0,0,.5]]
#WSTART_options = [[0.25,0,0.75]]#, [.5,0,0,0,0,0,0,0,0,0,.5]]
#WSTART_options = [[0.1,0,0.9]]#, [.5,0,0,0,0,0,0,0,0,0,.5]]
#WSTART_options = [[0,0,0,0,1.0]]#, [.5,0,0,0,0,0,0,0,0,0,.5]]
#WSTART_options = [[1.0,0,0],[0,0,1.0]]
#WSTART_options = [[0,0,0,0,0,0,0,0,1.0],[0.2,0,0.2,0,0.2,0,0.2,0,0.2]]
#WSTART_options = [[.5,0,0,0,0,0,0,0,0,0,.5]]
NOISE_options = [0.01] #[0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
BENEFIT_options = [2] #, 1.7, 1.8, 1.9]
COST = 1
#tax_prob = 0
#tax_start = 0
#printing_rate_options = [0,0.001,0.01]
#printing_rate_options = 0 #[0.001,0.01,0.1,0.5]
printing_rate_options = [0]
#printing_rate_options = [0.001, 0.01, 0.1,0.5] 
losing_rate = 0
threshold_fitness = 0.01
rhoA = 0.99
maxn = 100
    
function setup_argparse()
    s = ArgParseSettings()
    @add_arg_table s begin
        "--output-dir", "-o"
        help = "directory to store output files"
        default = "./data-default"
        "--ESSindex", "-e"
        help = "index for a single ESS to run to enable parallel tests"
        default = nothing
        required = false
         "--tax", "-t"
         help = "probability of being taxed"
         default = 0
         required = false
         "--tax-start", "-s"
         help = "lowest tax bin (use -ve values for wealth tax)"
         default = 1
         required = false
        "--prefilter-file", "-p"
        help = "CSV file for prefiltering"
	default = nothing
        required = false
    end
    return s
end

function main()
    s = setup_argparse()
    args = parse_args(s)
    # Check and create the output directory
    output_dir = get(args, "output-dir", "./data-default")
    if !isdir(output_dir)
        mkpath(output_dir)
    end

    if args["ESSindex"] != nothing
        allDict = makeAllstrategies()
        thekeys = collect(keys(allDict))
        thekey = thekeys[parse(Int,args["ESSindex"])]
        strategiesOptionsDict = Dict([(thekey, allDict[thekey])])
    else
        strategiesOptionsDict = nothing
    end
      
    # Handling prefilter file
    prefilter = nothing
  
    #if haskey(args, "prefilter-file")
    if args["prefilter-file"] != nothing
        df = DataFrame(CSV.File(args["prefilter-file"], delim=","))
        prefilter = string.(df[:,1], ", ",  df[:,2])
    end
    #print(prefilter)
    
     # Ignore taxation unless using tokens
     # ****
     if args["tax"] != 0
         tax_prob = parse(Float16,args["tax"])
         if args["tax-start"] != 1
             tax_start = parse(Int,args["tax-start"])
         else
             tax_start = 1
         end
     else
         tax_prob = 0
         tax_start = 0
     end
    
    # Need to specify an odd number of slots (at least -1, 0, 1)
    # Don't always specify the -1 slot, so this puts it in
    for WSTART in WSTART_options
	if iseven(length(WSTART))
    	    for i in 1:length(WSTART)-1
        	insert!(WSTART,2*i,0.) 
    	    end
	end
    end

    for USE_CmeetsN in USE_CmeetsN_options
    for USE_NmeetsC in USE_NmeetsC_options
    for USE_NmeetsN in USE_NmeetsN_options
    for REPUTATION in REPUTATIONS_options
    for noiseval in NOISE_options
    for WSTART in WSTART_options
    for BENE in BENEFIT_options
    for printing_rate in printing_rate_options
        global BENEFIT = BENE
        # construct a descriptive filename
        output_filename = output_dir * "/" * string(REPUTATION)
        if USE_CmeetsN  output_filename *= "_CmeetsN" end
        if USE_NmeetsC  output_filename *= "_NmeetsC" end
        if USE_NmeetsN  output_filename *= "_NmeetsN" end
        output_filename *= @sprintf("_Noise%.2g", noiseval)
        output_filename *= @sprintf("_B%g", BENEFIT)
        #if (WSTART != [0.5,0.,0.5]) output_filename *= "_altIC" end
        if (WSTART != [0.5,0.,0.5]) output_filename *= @sprintf("_altIC%s",WSTART) end
	if tax_prob != 0 output_filename *= @sprintf("_t%s",tax_prob) end
	if tax_start != 0 output_filename *= @sprintf("_s%s",tax_start) end
	if printing_rate != 0 output_filename *= @sprintf("_p%s",printing_rate) end
	if losing_rate != 0 output_filename *= @sprintf("_l%s",losing_rate) end
        if prefilter != nothing output_filename *= @sprintf("_%s", split(args["prefilter-file"],'.')[1]) end
        if @isdefined(thekey) output_filename *=  "_" * thekey  end
        @printf("Starting %s ...",output_filename)
        
        startTime = time()

        open(output_filename, "w") do io
            redirect_stdout(io) do
                big_test(;REPUTATION,
                USE_CmeetsN=USE_CmeetsN,  
                USE_NmeetsC=USE_NmeetsC, 
                USE_NmeetsN=USE_NmeetsN,
                WSTART=WSTART,
                maxn=maxn,rhoA=rhoA,noiseval=noiseval,
                threshold_fitness=threshold_fitness,prefilter=prefilter,
                strategiesOptionsDict=strategiesOptionsDict,
	        BENEFIT=BENEFIT,COST=COST,tax_prob=tax_prob,tax_start=tax_start,printing_rate=printing_rate,losing_rate=losing_rate)
            end
        end
        @printf("Done (in %.0f seconds)\n", time()-startTime)
    end
    end
    end
    end
    end
    end
    end
    end
end


main()


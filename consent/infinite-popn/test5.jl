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

println("------ investigate the invasiveness of a strategy --------")
GuineaPig = "+0+,+g-|-r+,+g-"
println("Testing ",GuineaPig," as an invader from rare")


allspecies = makeAllSpecies(true)  #nb: call with "false" if you want the restricted strategies only.
println("Number of species in total: ",length(allspecies))

rhoA = 0.99
MAXN = 100
println("rhoA=",rhoA)
println("maxn=",MAXN)

invaded_at_Gen   = Dict{Int,Any}()
uninvaded_at_Gen = Dict{Int,Any}()

uninvaded_at_Gen[1] = keys(allspecies)
global counter

for gen in 1:4
    @printf("\n\nRunning Gen %d\n",gen)
    invaded_at_Gen[gen] = Set{String}()
    uninvaded_at_Gen[gen] = Set{String}()
    startTime = time()
    global counter=0
    global count2 = 0
    if gen==1
        invadedPreviousGen = Set([GuineaPig])  # <-- the initialisation, ie. species we're interested in
        uninvadedPreviousGen = keys(allspecies)
    else
        invadedPreviousGen = invaded_at_Gen[gen-1]
        uninvadedPreviousGen = uninvaded_at_Gen[gen-1]
    end
    for A in uninvadedPreviousGen
        global counter += 1
        @printf("\r%d\t%s",counter,A)
        invaded = false
        i=0
        for B in invadedPreviousGen                      
            # Can B (e.g. money) invade A?
            local resA, resB = calc_stable_w_2species(
                allspecies[A], allspecies[B]; rhoA=rhoA, maxn=MAXN)
            if resB["fit"] >= resA["fit"] # NOTE THE RE-ORDERING 
                push!(invaded_at_Gen[gen],A)
                invaded = true
                break # jump right out of the inner loop
            end
            i = i+1
        end
        if (!invaded) push!(uninvaded_at_Gen[gen],A)  end  # GOT TO HERE --> cannot find anyone to invade this A, so add it to notInvaded
    end
    @printf("\rGeneration %d took %.0f seconds to complete\n", gen, time() - startTime)
    @printf("\ncount2 triggered %d times\n", count2)

    println("\n CHECK: num species accounted for this gen: ",length(invaded_at_Gen[gen]) + length(uninvaded_at_Gen[gen]))
    @printf(" %d in Gen %d get invaded\n", length(invaded_at_Gen[gen]), gen)
    @printf(" %d in Gen %d NOT invaded\n", length(uninvaded_at_Gen[gen]), gen)
    # too many (~14,000) of these, for the first generation
    if gen>1 
        @printf("All the strategies NOT invaded after Gen %d: \n", gen)
        for spec in uninvaded_at_Gen[gen]   println(spec)  end 
    end
end


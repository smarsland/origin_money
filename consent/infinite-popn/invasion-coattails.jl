using Printf
using Dates
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------

println("------ investigate the invasiveness of a strategy (e.g. money) --------")



allspecies = makeAllSpecies(true)  #use "false" if want score-conserving strategies only.
println("Number of species in total: ",length(allspecies))

GuineaPigs = ["000,+g-|-r+,+g-","+0-,+g-|-r+,+g-","0r0,+g-|-r+,+g-","+r-,+g-|-r+,+g-"]
#GuineaPigs = ["+0+,+g-|-r+,+g-"]
println("Testing ",GuineaPigs,", invading from rare")

MAXN = 100
println("MAXN is ",MAXN)
rare_density = 1e-6
println("rare_density is ",rare_density)

MUTANT_SCORES = "late" # "early" or "late"
# "early" means early in the scoring season, i.e. right from the beginning,
# both species are altering their score distributions, which both start the same
#
# "late" means late in the season, i.e. the common strategy runs until stability,
# then a mutation occurs, so the rare species then starts with the commoners'
# score distribution. Both run from there to stability.
println("MUTANT_SCORES is ",MUTANT_SCORES)


invaded_at_Gen   = Dict{Int,Any}()
uninvaded_at_Gen = Dict{Int,Any}()
global counter
for gen in 1:5
    startTime = time()
    invaded_at_Gen[gen] = Set{String}()
    uninvaded_at_Gen[gen] = Set{String}()
    if gen==1
        possibleInvaders = Set(GuineaPigs)  # <-- the initialisation, ie. species we're interested in
        possiblyInvaded = setdiff( keys(allspecies), possibleInvaders) # ie. the rest
    else
        possibleInvaders = invaded_at_Gen[gen-1]
        possiblyInvaded = uninvaded_at_Gen[gen-1]
    end
    global c=0
    @printf("\n\nRunning Gen %d, %d potential invaders and %d potentially invaded\n",
        gen,length(possibleInvaders),length(possiblyInvaded))

    for A in possiblyInvaded
        # can this be invaded by _anyone_ who was invaded in the previous gen?
        global c += 1
        @printf("\r%8d\t%s",c,A)
        invaded = false
        
        if MUTANT_SCORES == "early"
            w_init = [0.5,0.5]
        else
            wA_alone, nA_alone, fitA_alone = calc_stable_w_1species(allspecies[A]; maxn=MAXN)
            w_init = wA_alone
        end
        for B in possibleInvaders
            if BinvadesA(A, B; w_init=w_init,
                        rhoA=1-rare_density, limitn=MAXN, VERBOSE=false)
                push!(invaded_at_Gen[gen],A)
                invaded = true
                break # jump right out of the inner loop
            end
        end
        if (!invaded) push!(uninvaded_at_Gen[gen],A)  end  # GOT TO HERE --> cannot find anyone to invade this A, so add it to notInvaded
    end
    @printf("\rGeneration %d took %.0f seconds to complete\n", gen, time() - startTime)

    println("\n CHECK: num species accounted for this gen: ",length(invaded_at_Gen[gen]) + length(uninvaded_at_Gen[gen]))
    @printf(" %d in Gen %d get invaded\n", length(invaded_at_Gen[gen]), gen)
    @printf(" %d in Gen %d NOT invaded\n", length(uninvaded_at_Gen[gen]), gen)
    if gen>1 # too many (~14,000) of these, for the first generation
        @printf("All the strategies NOT invaded after Gen %d: \n", gen)
        for spec in uninvaded_at_Gen[gen]   println(spec)  end 
    end
end


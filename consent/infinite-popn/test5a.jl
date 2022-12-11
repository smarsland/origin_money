using Printf
using Dates
include("helper_funcs.jl")

#----------------------------------------------------------------------------------------------

println("------ investigate the invasiveness of a strategy (e.g. money) --------")



allspecies = makeAllSpecies(true)  #nb: call with "false" if you want the restricted strategies only.
println("Number of species in total: ",length(allspecies))


A = "+0+,+g-|-r+,+g-"
B = "000,+g-|-r+,+g-"

# run B on its own to get a stable score distribution and fitness
wB, nB, fitB = calc_stable_w_1species(allspecies[B])
@printf("B alone: %d \t %f \n",nB, fitB)
println(AinvadesB(A,B;w_init=wB))


invaded_at_Gen   = Dict{Int,Any}()
uninvaded_at_Gen = Dict{Int,Any}()

global counter

GuineaPig = "+0+,+g-|-r+,+g-"
println("Testing ",GuineaPig," as an invader from rare")

MAXN = 1000
println("MAXN is ",MAXN)
rare_density = 0.01
println("rare_density is ",rare_density)


for gen in 1:4
    startTime = time()
    invaded_at_Gen[gen] = Set{String}()
    uninvaded_at_Gen[gen] = Set{String}()
    if gen==1
        possibleInvaders = Set([GuineaPig])  # <-- the initialisation, ie. species we're interested in
        possiblyInvaded = keys(allspecies)
    else
        possibleInvaders = invaded_at_Gen[gen-1]
        possiblyInvaded = uninvaded_at_Gen[gen-1]
    end
    global counter=0
    @printf("\n\nRunning Gen %d, %d potential invaders and %d potentially invaded\n",
        gen,length(possibleInvaders),length(possiblyInvaded))
    for B in possiblyInvaded
        # can this be invaded by _anyone_ who was invaded in the previous gen?
        global counter += 1
        @printf("\r%d\t%s",counter,B)
        invaded = false
        wB_alone, n, fitB = calc_stable_w_1species(allspecies[B]; maxn=MAXN)

        for A in possibleInvaders
            if AinvadesB(A, B; w_init=wB_alone, rare_density=rare_density, limitn=MAXN/100, VERBOSE=false)
                push!(invaded_at_Gen[gen],B)
                invaded = true
                break # jump right out of the inner loop
            end
        end
        if (!invaded) push!(uninvaded_at_Gen[gen],B)  end  # GOT TO HERE --> cannot find anyone to invade this A, so add it to notInvaded
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


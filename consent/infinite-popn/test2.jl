include("helper_funcs.jl")

println("SHOULD MATCH:")

testStrat = name2strategy("000,+g-|-r+,+g-")
println("calc with 1 species code:\n---------------------------")
calc_stable_w_1species(testStrat; VERBOSE=true);

println("calc with 2 species code:\n---------------------------")
calc_stable_w_2species(testStrat, testStrat; rhoA=0.5, VERBOSE=true);




println("TEST OF A MIXTURE:")
println("====================")
calc_stable_w_2species(name2strategy("000,+g-|-r+,+g-"), name2strategy("-r+,+g-|-r+,+g-"); rhoA=0.99, VERBOSE=true);


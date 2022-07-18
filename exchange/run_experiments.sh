# This is the script that provides the overview of the experiments reported in the paper
# The tests are for the multihold and implicit hold solutions. There is no difference with the other two.

#g: gamma, a: action noise 0.01, e: exit rate, b: beta, q: qnoise
#B: be, R: break, G: grab, H: hold, F: fail
#m: multihold, noAGENTHOLDS

# Role of discounting
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 -m -n mg99 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.98 -m -n mg98 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.95 -m -n mg95 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.9 -m -n mg90 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.85 -m -n mg85 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.75 -m -n mg75 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.65 -m -n mg65 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99    -n ig99 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.98    -n ig98 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.95    -n ig95 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.9    -n ig90 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.85    -n ig85 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.75    -n ig75 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.65    -n ig65 -e 0.1 -v -r

# Role of costs
python MDPswapper.py -G 0.05        -F 10 -a 0.01 -g 0.99 -m -n mcg5 -v -r
python MDPswapper.py -G 0.03        -F 10 -a 0.01 -g 0.99 -m -n mcg3 -v -r
python MDPswapper.py -G 0.01        -F 10 -a 0.01 -g 0.99 -m -n mcg1 -v -r
python MDPswapper.py -G 0      -H 0.1 -F 10 -a 0.01 -g 0.99 -m -n mcg0h1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99 -m -n mc1h1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 0.1 -a 0.01 -g 0.99 -m -n mcg1h1f01 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 1 -a 0.01 -g 0.99 -m -n mcg1h1f1 -v -r

python MDPswapper.py -G 0.05 -H 0.1 -F 10 -a 0.01 -g 0.99    -n icg5h1 -e 0.1 -v -r
python MDPswapper.py -G 0.03 -H 0.1 -F 10 -a 0.01 -g 0.99    -n icg3h1 -e 0.1 -v -r
python MDPswapper.py -G 0.01 -H 0.1 -F 10 -a 0.01 -g 0.99    -n icg1h1 -e 0.1 -v -r
python MDPswapper.py -G 0    -H 0.1 -F 10 -a 0.01 -g 0.99    -n icg0h1 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.05 -F 10 -a 0.01 -g 0.99    -n icg1h5 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.03 -F 10 -a 0.01 -g 0.99    -n icg1h3 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.01 -F 10 -a 0.01 -g 0.99    -n icg1h01 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 1 -a 0.01 -g 0.99    -n icg1h1f1 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 0.1 -a 0.01 -g 0.99    -n icg1h1f01 -e 0.1 -v -r

# Perceived value
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 3 --VAL2A 3 -m -n mv3 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 2 --VAL2A 2 -m -n mv2 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 1.2 --VAL2A 1.2 -m -n mv12 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 1 --VAL2A 1 -m -n mv1 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 3 --VAL2A 3 -n iv3 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 2 --VAL2A 2 -n iv2 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 1.2 --VAL2A 1.2 -n iv12 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 1 --VAL2A 1 -n iv1 -e 0.1 -v -r

# Perceived value asymmetry
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 4 --VAL2A 3 -m -n mv43 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 4 --VAL2A 2 -m -n mv42 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.01 -g 0.99 --VAL1B 4 --VAL2A 1 -m -n mv41 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 4 --VAL2A 3 -n iv43 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 4 --VAL2A 2 -n iv42 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99   --VAL1B 4 --VAL2A 1 -n iv41 -e 0.1 -v -r

# Noise
python MDPswapper.py -G 0.1        -F 10 -a 0.0 -g 0.99 -m -n mn0 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.1 -g 0.99 -m -n mn1 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.2 -g 0.99 -m -n mn2 -v -r
python MDPswapper.py -G 0.1        -F 10 -a 0.3 -g 0.99 -m -n mn3 -v -r

python MDPswapper.py -G 0.1        -F 10 -q 0.0 -g 0.99 -m -n mnq0 -v -r
python MDPswapper.py -G 0.1        -F 10 -q 0.1 -g 0.99 -m -n mnq1 -v -r
python MDPswapper.py -G 0.1        -F 10 -q 0.2 -g 0.99 -m -n mnq2 -v -r
python MDPswapper.py -G 0.1        -F 10 -q 0.3 -g 0.99 -m -n mnq3 -v -r

python MDPswapper.py -G 0.1        -F 10  -a 0.0 -q 0.0 -g 0.99 -m -n mnaq0 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.0 -g 0.99    -n in0 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.1 -g 0.99    -n in1 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.2 -g 0.99    -n in2 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.3 -g 0.99    -n in3 -e 0.1 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -q 0.0 -g 0.99    -n inq0 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -q 0.1 -g 0.99    -n inq1 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -q 0.2 -g 0.99    -n inq2 -e 0.1 -v -r
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -q 0.3 -g 0.99    -n inq3 -e 0.1 -v -r

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.0 -q 0.0 -g 0.99    -n inaq0 -e 0.1 -v -r

# Slow exits
python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01 -g 0.99    -n is05 -e 0.05 -v -r

# More costs
python MDPswapper.py -G 0.0 -H 0.1 -F 10 -a 0.01 -g 0.99    -n ac001 -e 0.1 -v -r

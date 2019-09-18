
#g: gamma, a: action noise 0.01, e: exit rate, b: beta, q: qnoise
#B: be, R: break, G: grab, H: hold, F: fail
#m: multihold, noAGENTHOLDS

#python MDPswapper.py -v -n a -r
#python MDPswapper.py -G 0.1 -F 10 -v -n b -r
#python MDPswapper.py -G 0.2 -F 10 -v -n c -r

#python MDPswapper.py -B 0.1 -F 10 -v -n d -r
#python MDPswapper.py -B 0.2 -F 10 -v -n e -r

#python MDPswapper.py -H 0.1 -F 10 -v -n f -r
#python MDPswapper.py -H 0.2 -F 10 -v -n g -r
#python MDPswapper.py -G 0.2 -H 0.2 -F 10 -v -n h -r

#====
#python MDPswapper.py -v -n ma -r -m
#python MDPswapper.py -G 0.1 -F 10 -v -n mb -r -m
#python MDPswapper.py -G 0.2 -F 10 -v -n mc -r -m

#python MDPswapper.py -B 0.1 -F 10 -v -n md -r -m
#python MDPswapper.py -B 0.2 -F 10 -v -n me -r -m

#python MDPswapper.py -H 0.1 -F 10 -v -n mf -r -m
#python MDPswapper.py -H 0.2 -F 10 -v -n mg -r -m
#python MDPswapper.py -G 0.2 -H 0.2 -F 10 -v -n mh -r -m

#====
#python MDPswapper.py -g 0.98 -G 0.1 -F 10 -v -n ga -r 
#python MDPswapper.py -g 0.95 -G 0.1 -F 10 -v -n gb -r 
#python MDPswapper.py -g 0.9 -G 0.1 -F 10 -v -n gc -r 
#python MDPswapper.py -g 0.85 -G 0.1 -F 10 -v -n gd -r 

#python MDPswapper.py -g 0.98 -G 0.1 -F 10 -v -n gma -r -m
#python MDPswapper.py -g 0.95 -G 0.1 -F 10 -v -n gmb -r -m
#python MDPswapper.py -g 0.9 -G 0.1 -F 10 -v -n gmc -r -m
#python MDPswapper.py -g 0.85 -G 0.1 -F 10 -v -n gmd -r -m
#python MDPswapper.py -g 0.75 -G 0.1 -F 10 -v -n gme -r -m
#python MDPswapper.py -g 0.65 -G 0.1 -F 10 -v -n gmf -r -m

#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -e 0.1 -v -n f -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -e 0.25 -v -n fm -r -m

#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -e 0.1 -v -n fa -r -m
#python MDPswapper.py -g 0.98 -G 0.1 -F 10 -e 0.1 -v -n fb -r -m
#python MDPswapper.py -g 0.95 -G 0.1 -F 10 -e 0.1 -v -n fc -r -m
#python MDPswapper.py -g 0.9 -G 0.1 -F 10 -e 0.1 -v -n fd -r -m
#python MDPswapper.py -g 0.85 -G 0.1 -F 10 -e 0.1 -v -n fe -r -m

#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.75 -v -n ba -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.9 -v -n bb -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.75 -v -n bc -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.9 -v -n bd -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.75 -e 0.1 -v -n be -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -b 0.9 -e 0.1 -v -n bf -r -m

#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0. -v -n aa -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.05 -v -n ab -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.1 -v -n ac -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.25 -v -n ad -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0. -v -n ama -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.05 -v -n amb -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.1 -v -n amc -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -a 0.25 -v -n amd -r -m

#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0. -v -n qa -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.05 -v -n qb -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.1 -v -n qc -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.25 -v -n qd -r 
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0. -v -n qma -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.05 -v -n qmb -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.1 -v -n qmc -r -m
#python MDPswapper.py -g 0.99 -G 0.1 -F 10 -q 0.25 -v -n qmd -r -m

#python MDPswapper.py -G 0.1 -H 0.1 -F 10 -e 0.1 -v -n ia -r
#python MDPswapper.py -G 0.1 -H 0.1 -F 10 -e 0.1 -v -n ib -r -m
#python MDPswapper.py -G 0.1 -H 0.1 -F 10 -e 0.25 -v -n ic -r
#python MDPswapper.py -G 0.1 -H 0.1 -F 10 -e 0.25 -v -n id -r -m

python MDPswapper.py -G 0.1 -H 0.05 -F 10 -e 0.1 -v -n ie -r
python MDPswapper.py -G 0.1 -H 0.05 -F 10 -e 0.1 -v -n if -r -m
python MDPswapper.py -G 0.1 -H 0.05 -F 10 -e 0.25 -v -n ig -r
python MDPswapper.py -G 0.1 -H 0.05 -F 10 -e 0.25 -v -n ih -r -m

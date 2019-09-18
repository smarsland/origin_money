
# This runs parameters for the four examples in the main figure

python MDPswapper.py -G 0.1        -F 10 -a 0.01  -m -n multihold -v

python MDPswapper.py -G 0.1        -F 10 -a 0.01     -n agenthold -v

python MDPswapper.py -G 0.1        -F 10 -a 0.01     -n noagenthold --noAGENTHOLDS -v

python MDPswapper.py -G 0.1 -H 0.1 -F 10 -a 0.01     -n implicithold -e 0.1 -v



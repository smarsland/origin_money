import java.util.*;
import java.io.PrintWriter;
import java.io.IOException;

public class Simulation {

    // fields
    public int NumAgents, NumGenerations, NumRounds, rngseed;
    public double SelectionIntensity, MutationProbability;
    public boolean CONSERVED, IGNORES;
    // If CONSERVED is set (in main), rules will only be allowed if they conserve the signal.
    // If IGNORES is set (in main), the s=0/s>0 distinction doesn't allow agent to behave differently.
    public List<Agent> popn;
    Random rng;
        
    // constructor
    public Simulation(String[] args, List<Agent> popn) {   
        try {             
            this.NumAgents =  Integer.parseInt(args[0]);
            this.NumGenerations =  Integer.parseInt(args[1]);
            this.NumRounds =  Integer.parseInt(args[2]);
            this.SelectionIntensity = Double.parseDouble(args[3]);
            this.MutationProbability = Double.parseDouble(args[4]);

            if (args.length==6) this.rngseed = Integer.parseInt(args[5]);
            else {
                Random r = new Random();
                this.rngseed = r.nextInt(100);
            }
            this.rng = new Random(this.rngseed); // use seed for repeatable example runs.
        } 
        catch (IndexOutOfBoundsException e) {
            System.err.println("Example usage: java Simulation 500 50000 25 2.0 0.01");
            System.err.println("Args are: #Agents, #Generations, #Rounds, SelectionIntensity,  MutationProbability  [int seed for RNG]");
            System.exit(0);
            //System.err.println("IndexOutOfBoundsException: " + e.getMessage());
        }
        this.popn = popn;

    }


    /************************************************************************/
    // Methods

    //-------------------------------------------------------------------------
    private void evolve (PrintWriter writer) {
    /*
    Here is one way to do this:
    Everyone interacts with some random others, accruing a total payoff.
    We turn that into a positive payoff, and define fitness to be exp(payoff).
    Then we sample from popn with probability proportional to fitness.
    Samples get copied into new generation, with occasional point-mutations possible.
    Keep sampling thus until new generation has the original population size.
    Rinse and repeat.
    */
        boolean VERBOSE = false;
        int nextReport = 1;
        for (int t=0; t<=NumGenerations; t++) {
            initialiseAllScoresPayoffs();    
                        
            doHelping(); // runs several rounds of "helping"        
            double avPay = 0.0;
            for (Agent A : this.popn) avPay = avPay + A.getPayoff();
            avPay = avPay / this.NumAgents;
            
            calcFitnesses();
            
            // sometimes show progress
            if ((t == nextReport)  || (t==NumGenerations)) {
                
                nextReport = Math.max(nextReport+1, t+100);
                if (avPay > -0.1) describePopn(t, writer, VERBOSE);
            }

            if (t==NumGenerations) showScoreDistribution(writer);    

            resample();  // gives you a brand new population
        }
        
        return;
    }

    private void showScoreDistribution(PrintWriter writer) {
        int MAXSCORE=5;
        for (Agent A : this.popn) if (A.getScore() > MAXSCORE) MAXSCORE=A.getScore();
        int total=0;
        for (int k=0; k<=MAXSCORE; k++) {
            int n=0;
            for (Agent A : this.popn) if (A.getScore()== k) ++n;
            writer.printf("SCORE\t %5d\t %d\n",k,n);
            System.out.printf("SCORE\t %5d\t %d\n",k,n);
            total += n; 
        }
        System.out.printf("total: %d\n",total);
    }
    //-------------------------------------------------------------------------

    private void calcFitnesses() {
        /* Convert the payoffs into probabilities for reproduction ("fitnesses")
         "fitnesses" are exp(payoff), normalised over whole population
         BUT ALSO multiplied back up by the population size.
         The latter is purely to help them be interpretable: 
         a "fitness" of 1.0 means neutral evolution.
        */
        
        double sum=0.0;
        for (Agent A : this.popn) {
            A.setFitness( Math.exp(A.getPayoff() * this.SelectionIntensity));
            sum += A.getFitness();
        }
        for (Agent A : this.popn) 
            A.setFitness(A.getFitness() / sum * this.NumAgents);
        return;
    }        

    private void resample() {
        /*
        This assumes that Payoffs --> Fitnesses have been calculated for all Agents.
        */
        
        /* Simple enough version.
        DistributedRandomNumberGenerator drng = new DistributedRandomNumberGenerator();
        for (int i=0; i<popn.size(); i++) drng.addNumber(i, fitness[i]);  */
        
        /* ButT this one is much faster if you need to do this at scale.  */     
        List<Double> myprobs = new ArrayList<Double>();
        for (Agent A : this.popn) myprobs.add(A.getFitness() / this.NumAgents); 
        // notice the normalisation is reinstated for fitnesses here, where it matters.
        AliasMethod ali = new AliasMethod(myprobs, this.rng);
        
        List <Agent> newPopn = new ArrayList <Agent>(); // a brand new array
        int k;
        for (int i=0; i<popn.size(); i++) {
            
            //k = drng.getDistributedRandomNumber(); // Generate a random number
            k = ali.next(); // this is the index chosen as a replicator.
            Agent A = popn.get(k);  // the agent chosen as a replicator.
            int[][] dh = new int[2][2];
            int[][] dsSlf = new int[2][2];
            int[][] dsOth = new int[2][2];
            for (int r = 0; r < 2; r++) { 
                System.arraycopy(A.dh[r], 0, dh[r], 0, A.dh[r].length);
                System.arraycopy(A.dsSelf[r], 0, dsSlf[r], 0, A.dsSelf[r].length);
                System.arraycopy(A.dsOther[r], 0, dsOth[r], 0, A.dsOther[r].length);
            }
            newPopn.add(new Agent(i, dh, dsSlf, dsOth, rng, this.MutationProbability));
        }
        // Finally, replace the simulation's "working" population with this new one.
        this.popn = newPopn;
        if (this.CONSERVED) insistScoreConserved();
        if (this.IGNORES) makeHandshakesIgnoreS();
            
        return;
    }
    //-------------------------------------------------------------------------  

    private void initialiseAllScoresPayoffs() {
        for (Agent A : this.popn) {            
            A.setScore(rng.nextInt(2));
            A.zeroPayoff();
        }
        return;
    }

  
    //-------------------------------------------------------------------------
    private void insistScoreConserved() {
    /* throw away whatever is in dsOther, and replace it with the opposite of dsSelf.
    In other words, FORCE the changes in score to be zero sum. */
        for (Agent A  : popn){
            for (int h=0;h<=1;h++)  
                for (int S=0;S<=1;S++)
                    A.dsOther[h][S] = -1 * A.dsSelf[h][S];
        }
        return;
    }
    
    //-------------------------------------------------------------------------
    private void makeHandshakesIgnoreS() {
    /* ............. */
        for (Agent A  : popn) 
            for (int h=0;h<=1;h++) {
                A.dh[h][1] = A.dh[h][0];
                A.dsSelf[h][1]  = A.dsSelf[h][0];
                A.dsOther[h][1] = A.dsOther[h][0];
            }
        return;
    }
    
    //-------------------------------------------------------------------------
    private void describePopn(int gen, PrintWriter writer, boolean VERBOSE) {
    
        // Prepare a list of the unique strategies present in the current population.
        List <Agent> strategies = new ArrayList<Agent>();
        boolean contains = false;
        for (Agent A : this.popn) {
            contains = false;
            for (Agent B : strategies)
                if (B.hashCode() == A.hashCode()) contains = true;
            if (contains == false) { 
                // we want to record this strategy, so make a brand new Agent 
                int[][] dh = new int[2][2];
                int[][] dsSlf = new int[2][2];
                int[][] dsOth = new int[2][2];
                for (int r = 0; r < 2; r++) { 
                    System.arraycopy(A.dh[r], 0, dh[r], 0, A.dh[r].length);
                    System.arraycopy(A.dsSelf[r], 0, dsSlf[r], 0, A.dsSelf[r].length);
                    System.arraycopy(A.dsOther[r], 0, dsOth[r], 0, A.dsOther[r].length);
                }
                strategies.add(new Agent(-1, dh, dsSlf, dsOth, rng, 0.0)); // with no mutations, of course!
            }
        }
        // each strategy in "strategies" defines a subpopulation in popn.
        // We want to evaluate the mean values for each such subpopulation. 
        // We will use the pay and fitness attributes of B to store the means.
        Map <Agent, List<Agent>> mySubpopnsMap = new HashMap <Agent, List<Agent>> ();
        for (Agent B : strategies) {
            B.resetMaxMinScore();
            // go through popn, looking for instances of B.
            B.setPayoff(0.0); 
            B.setFitness(0.0);
            List<Agent> subpopn = new ArrayList <Agent> ();
            
            for (Agent A : this.popn)  
                if (A.hashCode() == B.hashCode()) {
                    subpopn.add(A);
                    B.setPayoff( B.getPayoff() + A.getPayoff() );
                    B.setFitness( B.getFitness() + A.getFitness() );                    
                    B.setAvScore( B.getAvScore() + A.getScore() );
                    B.setMaxMinScore( A.getScore() );
                }
            B.setPayoff( B.getPayoff() / subpopn.size());
            B.setFitness( B.getFitness() / subpopn.size());
            B.setAvScore( B.getAvScore() / subpopn.size());
            Collections.sort(subpopn);
            mySubpopnsMap.put(B, subpopn);
        } 
        // B has stored the subpopn means of payoff and fitness in it's fields. 
        // We also have a Map from B to all its actual members. Yay.
        // So we can sort the types by their (average) fitnesses - nice for the report.
        Collections.sort(strategies);
        
        
        if (VERBOSE == true) {
            writer.printf("--------------------\nGeneration %d\n",gen);
            writer.printf("%d strategies present:\n\n",strategies.size(),gen);
            int numExamples = 0;
            for (Agent B : strategies) {
                //B.describe(true,writer);
                writer.printf("%s\t",B.hashString());
                writer.printf("\t(n=%d)\tAv: Score %.2f   ~Fit %.3f   \tPay %.3f\n",
                    mySubpopnsMap.get(B).size(),B.getAvScore(),B.getFitness(),B.getPayoff());
                // the ~ is because this is mean of the (normalised) fitness TIMES THE 
                // WHOLE POPN SIZE, just for ease of interpretation, as a value of
                // 1.0 corresponds to neutral evolution.
                if (numExamples > 0) {
                    writer.printf("\tBest %d individuals of this type:\n",numExamples);            
                    for (int i=0; i<Math.min(numExamples,mySubpopnsMap.get(B).size()); i++) {
                        writer.printf("");
                        mySubpopnsMap.get(B).get(i).describe(false,writer);
                        writer.printf("\n");
                    }
                    writer.printf("\tWorst:\n");
                    int L = mySubpopnsMap.get(B).size(); //index of last in sorted list.         
                    for (int i=Math.max(0,L-numExamples); i<L; i++) {
                        writer.printf("");
                        mySubpopnsMap.get(B).get(i).describe(false,writer);
                        writer.printf("\n");
                    }
                }
            }
        }
        int biggest_popn = 0;
        Agent biggest=null;
        for (Agent B : strategies) 
            if (mySubpopnsMap.get(B).size() > biggest_popn) {
                biggest_popn = mySubpopnsMap.get(B).size();
                biggest = B;
            }
        System.out.printf("%10d\t %.2f \t %.3f\t\t %s\n",gen,
            biggest.getAvScore(),biggest.getPayoff(),
            biggest.hashString());


        // Question: why are we reporting for "biggest" instead of the popn average?
        // Oh, well the description of the biggest component's behaviour makes sense.
        // But it would probably be better to calc the true popn av pay, rather than
        // the av pay of the major component in that population.  :/
        if (VERBOSE == false) {
            /* Here we make a description to go into the file. */
            //writer.printf("%10d \t%s",gen, biggest.hashString());
            //writer.printf("\t(n=%d)\tAv: Score %.2f   ~Fit %.3f   \tPay %.3f\n",
            //        mySubpopnsMap.get(B).size(),B.getAvScore(),B.getFitness(),B.getPayoff());
            writer.printf("%10d\t %.2f \t %.3f\t %s \t%.2f to %.2f\n",gen,biggest.getAvScore(),biggest.getPayoff(),biggest.hashString(),biggest.minScore,biggest.maxScore);
        }
        return;
    }
    
    //-------------------------------------------------------------------------  
    private void doHelping() {
        /* Everyone interacts with some random others, accruing a total payoff. Easy, right?
        We will do this in rounds. 
        Each round:
            We put all agents into pairs, totally at random.
            Those pairs compare offers and interact if those are complements
                (this both accrues payoff and changes scores, for both agents)
        */    
        boolean VERBOSE = false;
        
        
        // CHECK: are scores random and payoffs zero? Should they be?
        // Should that happen HERE?
        initialiseAllScoresPayoffs();    
        int numLeft;
        Agent A,B;
        
        for (int round=0; round<this.NumRounds; round++)
        {
            // First, we make a list of everyone.
            List<Integer> unpaired = new ArrayList <Integer> ();
            for (int i=0; i<popn.size(); i++) unpaired.add(i);
            
            numLeft = unpaired.size();
            
            // While unpaired has elements, select random pairs from it
            while (numLeft >= 2)
            {
                // CHOOSE agent A
                int indA = rng.nextInt(numLeft);  //an index into unpaired
                A = popn.get(unpaired.get(indA)); // that elt of unpaired is index of our agent A
                // "remove" ind from unpaired, by overwriting with the last elt and decrementing numleft
                unpaired.set(indA,unpaired.get(numLeft-1));
                numLeft -= 1;
                // SAME AGAIN to get agent B
                int indB;
                do {
                    indB = rng.nextInt(numLeft); 
                    B = popn.get(unpaired.get(indB)); 
                } while (A.index == B.index);
                unpaired.set(indB,unpaired.get(numLeft-1));
                numLeft -= 1;
                
                // Do the interaction, and add the resulting payoff, for A.
                // Suggest we just ignore the payoff of B, as that would introduce 
                // extra stochasticity via variable number of payoff-inducing interactions.

                // Stochastic aspect: are they able to help or not?
                int hA = rng.nextInt(2); 
                int hB = rng.nextInt(2); 
                // Deterministic scores - just binarizing those for use as indices here.
                int SA = (A.score >= 1) ? 1 : 0;            
                int SB = (B.score >= 1) ? 1 : 0;

                //System.out.printf("agent %d (%d,%d) meets %d (%d,%d)",A.index,hA,SA,B.index,hB,SB);
                
                // There is a slight cost to making any non-zero offer.
                if (A.dh[hA][SA]!=0)  A.feelInteractCost();
                if (B.dh[hB][SB]!=0)  B.feelInteractCost();
                
                
                // The big question: do they have a deal? Break it down...
                // 1a. Do their offers regarding help match? (nb. both 0 counts as a "match").
                boolean dh_agree = (A.dh[hA][SA] + B.dh[hB][SB] == 0);
                // 1b. Are they in agreement on ds for A, and for B?
                boolean dsA_agree = (A.dsSelf[hA][SA] == B.dsOther[hB][SB]);
                boolean dsB_agree = (A.dsOther[hA][SA] == B.dsSelf[hB][SB]);
                boolean ds_agree = (dsA_agree && dsB_agree);
                // 2a. If help is either offered or required, it has to also be available
                boolean dhA_possible = true, dhB_possible = true;
                if ((A.dh[hA][SA] ==  1) && (hB==0)) dhA_possible = false;
                if ((A.dh[hA][SA] == -1) && (hA==0)) dhA_possible = false;
                if ((B.dh[hB][SB] ==  1) && (hA==0)) dhB_possible = false;
                if ((B.dh[hB][SB] == -1) && (hB==0)) dhB_possible = false;
                boolean dh_possible = dhA_possible && dhB_possible;
                // 2b. signal changes can't be illegal
                boolean dsA_possible = true, dsB_possible = true;
                if (A.score + A.dsSelf[hA][SA] < 0) dsA_possible = false;
                if (B.score + B.dsSelf[hB][SB] < 0) dsB_possible = false;
                boolean ds_possible = dsA_possible && dsB_possible;
                // NOTE: SO FAR, HAVING MAX SCORE AND ASKING FOR MORE IS NOT DEAL-BREAKER.

                boolean deal = (dh_agree && ds_agree && dh_possible && ds_possible);
                // If we have a deal...
                if (deal) 
                {
                    //System.out.printf("\t deal\n");
                    if (VERBOSE) {
                        System.out.printf("Agent %d (%d,%d) and Agent %d (%d,%d) agree!\t",A.index,hA,SA,B.index,hB,SB);
                        if (A.dh[hA][SA]==1) System.out.printf("%d helps %d\t",B.index,A.index);
                        else if (A.dh[hA][SA]==-1) System.out.printf("%d helps %d\t",A.index,B.index);
                        
                        if (A.dsSelf[hA][SA]==1) System.out.printf("Agent %d gains score\t",A.index);
                        else if (A.dsSelf[hA][SA]==-1) System.out.printf("Agent %d loses score\t",A.index);
                        
                        if (B.dsSelf[hB][SB]==1) System.out.printf("Agent %d gains score\t",B.index);
                        else if (B.dsSelf[hB][SB]==-1) System.out.printf("Agent %d loses score\t",B.index);
                        System.out.printf("\n");
                    }                    
                    // Agents gains payoff if they get helped, and lose payoff if they help.
                    if (A.dh[hA][SA] == 1) 
                        if (hA == 0) A.feelBenefit(); // no benefit if h=1 already!!
                    if (B.dh[hB][SB] == 1) 
                        if (hB == 0) B.feelBenefit();
                    if (A.dh[hA][SA] == -1) A.feelCost();
                    if (B.dh[hB][SB] == -1) B.feelCost();
                    // and scores are changed as per the mutual agreement.
                    if (A.dsSelf[hA][SA] == 1) A.incrementScore();
                    if (A.dsSelf[hA][SA] == -1) A.decrementScore(); 
                    if (B.dsSelf[hB][SB] == 1) B.incrementScore();
                    if (B.dsSelf[hB][SB] == -1) B.decrementScore(); 
                    
                    //System.out.printf("AFTER: A score=%d,fit=%.1f)\t",A.score,A.payoff);
                    //System.out.printf("AFTER: B score=%d,fit=%.1f)\t",B.score,B.payoff);

                } // end of the "if (deal)" condition   
                else {                  
                    // There is a slight cost to making any non-zero offer and having it rejected.
                    // This doesn't really affect anything (and shouldn't!), but just reduces the distraction of 
                    // seeing so many weird things that are always rejected anyway, thus amount to "000" IN EFFECT.
                    if ((A.dsSelf[hA][SA]!=0) ||  (A.dh[hA][SA]!=0) || (A.dsOther[hA][SA]!=0)) A.feelInteractCost();
                    if ((B.dsSelf[hB][SB]!=0) ||  (B.dh[hB][SB]!=0) || (B.dsOther[hB][SB]!=0)) B.feelInteractCost();
                    //System.out.printf("\t no deal\n");
                }
            } // end of the while loop over random pairs: everyone has 1 interaction = 1 round.
        } // end of the "rounds" loop.
        for (Agent jim : popn)
            jim.setPayoff( jim.getPayoff()/NumRounds); // payoff is the average over rounds.
        return;            
    }

    /************************************************************************************/

    public static void main(String[] args) {
    
        
        // generate a population of random individuals             
        List <Agent> popn = new ArrayList <Agent> ();
        //for (int i=0;i<popn.length;i++) popn[i] = new Agent(i);      
        
        Simulation sim = new Simulation (args, popn);
        sim.CONSERVED = false;  // set true if you want to force score changes to be zero sum.
        sim.IGNORES   = false;   // set true if you want to make offers "blind" to (self's) S.
        
        //TEST POPN IS JUST ONE TYPE.
        for (int i=0; i<sim.NumAgents; i++) {
            Agent A = new Agent(i, sim.rng); // just a random init popn.
            
            //Agent A = new Agent(i, new int[][]{{0,1},{-1,-1}},new int[][]{{0,-1},{1,1}},new int[][]{{0,1},{-1,-1}}, sim.rng, 0.0); 
            // This is the "trader" strategy. Whoop, whoop.
            

            sim.popn.add(A);
        }
        /* remake the first few to be some alternative
        for (int i=0; i<10; i++) {
            Agent A = new Agent(i, new int[][]{{0,1},{-1,1}},new int[][]{{0,-1},{1,1}},new int[][]{{0,1},{-1,-1}}, sim.rng, 0.0);
            sim.popn.set(i,A);
        }
        */
        
        String suffix = "";
        if (sim.CONSERVED) suffix = suffix + "-CONSERVED";
        if (sim.IGNORES) suffix = suffix + "-IGNORES";
        String filename = "".format("example-%d%s.txt",sim.rngseed,suffix);
        try {
            PrintWriter writer = new PrintWriter(filename, "UTF-8");
            
            writer.print("java Simulation ");
            for (String s : args) writer.printf("%s\t",s);
            writer.print("\n");
            if (sim.CONSERVED) 
                writer.print("**** NOTE! Scores being constrained to be conserved. ***\n");
            else writer.print("\n");
            if (sim.IGNORES) 
                writer.print("**** NOTE! Offers same for either S=0 or 1. ***\n");
            else
                writer.print("\n");
            
            
            
            sim.evolve(writer); // evolve it for a bit
            
        
            writer.close();
        } catch (IOException e) { e.printStackTrace(); }
        
        
        

        System.out.printf("\nWrote %s\n",filename);
        
        return;
    } // end of main
} // end of class

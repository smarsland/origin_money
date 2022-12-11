//import java.util.concurrent.ThreadLocalRandom;
import java.util.*;
import java.util.Arrays;
import java.io.PrintWriter;

public class Agent implements Comparable {
    private static final double BENEFIT=5.0, COST=1.0, INTERACTIONCOST=0.001;
    private static final int NumScoreLevels = 100; // Should be >> number of rounds.
   
    // fields 
    public int[][] dh, dsSelf, dsOther;
    public double payoff=0.0, fitness=0.0, avScore=0.0, maxScore, minScore;
    public int score=0, index;
    public Random rng;
    
    // first constructor just initialises everything randomly.
    public Agent(int index, Random rng)
    {
        this.rng = rng;
        this.index = index;
        // assign default value
        this.dh = new int[2][2];
        this.dsSelf = new int[2][2];
        this.dsOther = new int[2][2];
        for (int r=0; r<2; r++) {
            for (int c=0; c<2; c++)
            {
                this.dh[r][c] = rng.nextInt(3)-1; // -1, 0, +1
                this.dsSelf[r][c] = rng.nextInt(3)-1;
                this.dsOther[r][c] = rng.nextInt(3)-1;
            }
        }
    }   
    
    // second constructor, for initialising specific agent, and perhaps mutating.
    public Agent(int index, int[][] dh, int[][] dsSelf, int[][] dsOther, Random rng, double mutationProb)
    {
        this.index = index;
        // we take the old agent's parameters, but reset the (init) score randomly.
        this.dh = dh;
        this.dsSelf = dsSelf;
        this.dsOther = dsOther;
        
        // POSSIBLY make a random mutation happen.
        if (mutationProb > 0.0) {
            if (rng.nextDouble() < mutationProb) 
            {
                int i = rng.nextInt(3); // dh, dsSelf, or dsOther
                int r = rng.nextInt(2); // the row
                int c = rng.nextInt(2); // the col
                if (i==0) this.dh[r][c] = rng.nextInt(3)-1; // -1, 0, or +1
                else if (i==1) this.dsSelf[r][c] = rng.nextInt(3)-1; 
                else this.dsOther[r][c] = rng.nextInt(3)-1; 
            }
        }
    }
    
    
    
    //@Override
    /* This is done purely to be consistnet with hashCode() */
    public boolean equals(Agent otherguy)
    {
        boolean match=true;
        for (int h=0;h<=1;h++)
            for (int S=0;S<=1;S++)
                if ((this.dh[h][S] != otherguy.dh[h][S]) ||
                    (this.dsSelf[h][S] != otherguy.dsSelf[h][S]) ||
                    (this.dsOther[h][S] != otherguy.dsOther[h][S]))
                    match=false;
        return(match);
    }
    public String hashString()
    {
        String str="", h;
        int i;
        for (int c=0; c<2; c++)  {
            for (int r=0; r<2; r++)  {
                i = this.dsSelf[r][c];
                h = "0";
                if (i == -1) h = "-";   
                if (i ==  1) h = "+";   
                str = str + h;        

                i = this.dh[r][c];
                h = "0";
                if (i == -1) h = "g";   
                if (i ==  1) h = "r";   
                str = str + h;        
                
                i = this.dsOther[r][c];
                h = "0";
                if (i == -1) h = "-";   
                if (i ==  1) h = "+";   
                str = str + h;          
                                
                if (r==0) str = str + ",";        
            }
            if (c==0) str = str + "|";
        }
        
        return(str);    
    }
    
    @Override
    public int hashCode()
    {   
        //int hash;
        //hash = Arrays.deepHashCode(this.dh);
        //hash = hash * Arrays.deepHashCode(this.dsSelf);
        //hash = hash * Arrays.deepHashCode(this.dsOther);
        //Object[] arrs = {this.dh,this.dsSelf,this.dsOther};
        String h = this.hashString();
        return(h.hashCode()); //Arrays.deepHashCode(arrs));
    }

    @Override
    public int compareTo(Object him) {
        Agent otherguy = (Agent)him;
        /* For Ascending order...... */
        if (this.fitness > otherguy.fitness) return -1;
        else if (this.fitness == otherguy.fitness) return 0;
        else return 1;
    }
    
    
    public void describe(boolean briefly, PrintWriter writer)
    {
        if (briefly) {
            writer.print("dh");
            for (int r=0; r<2; r++) for (int c=0; c<2; c++)
                    writer.printf("%2d",this.dh[r][c]);
            writer.print("\t");
            writer.print("dsSelf");
            for (int r=0; r<2; r++) for (int c=0; c<2; c++)
                    writer.printf("%2d",this.dsSelf[r][c]);
            writer.print("\t");
            writer.print("dsOther");
            for (int r=0; r<2; r++) for (int c=0; c<2; c++)
                    writer.printf("%2d",this.dsOther[r][c]);
        }
        else
            writer.printf("\tpay %.2f \t ~fit %.3f \t score %d",
                this.payoff,this.fitness,this.score);
        return;
    }
    
    public void zeroPayoff() { this.payoff = 0.0; }
    public void setPayoff(double val) { this.payoff = val; }
    public double getPayoff() { return( this.payoff ); }

    public void setFitness(double val) { this.fitness = val; }
    public double getFitness() { return( this.fitness ); }

    public void feelBenefit() { 
        this.payoff = this.payoff + BENEFIT; 
        //System.out.printf("ag %d felt benefit \n",this.index); 
    }
    public void feelCost() { 
        this.payoff = this.payoff - COST; 
        //System.out.printf("ag %d felt cost\n",this.index);
    }    
    public void feelInteractCost() { this.payoff = this.payoff - INTERACTIONCOST; }
    
    public void setScore(int s) { this.score = s; }
    public int  getScore() { return(this.score); }
    public void incrementScore() { this.score = Math.min(NumScoreLevels-1,this.score+1); }
    public void decrementScore() { this.score = Math.max(0,this.score-1); }    
    
    public void setAvScore(double s) { this.avScore = s; }
    public double getAvScore() { return(this.avScore); }

    public void resetMaxMinScore()
    {
        this.maxScore = -1000000.0; 
        this.minScore =  1000000.0; 
    }
    public void setMaxMinScore(double s)
    {
        if (s > this.maxScore) this.maxScore = s; 
        if (s < this.minScore) this.minScore = s; 
    }

    public static void main(String[] args) {   }

}

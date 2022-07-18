import numpy as np
#import matplotlib
#matplotlib.use('Agg') # backend to use.
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import argparse

def do_box(ax,x,y,color,label,alpha):
    bh, bw = .3, .5  # box width and box height
    fancybox = mpatches.FancyBboxPatch((x-bw/2, y-bh/2), bw, bh,
        boxstyle=mpatches.BoxStyle("Round", pad=0.01, rounding_size=.1), 
        color=color, alpha=alpha)
    ax.add_patch(fancybox)
    plt.text(x,y,label, ha="center", va="center", 
         family='sans-serif', size=48, color='w')
    return


def do_hold(ax,x1,y1,x2,y2,colourname,alpha,curvesign):
    # don't go quite that far...
    FRACTION = .8
    x2 = x1 + FRACTION*(x2-x1)
    y2 = y1 + FRACTION*(y2-y1)
    properties = dict(arrowstyle='fancy', #'wedge'
                    alpha=alpha,fc=colourname, ec=colourname,
                    connectionstyle="arc3,rad={0}".format(0.1*curvesign))
    ax.annotate('', (x1,y1),(x2,y2),
                    ha="center", va="center",size=60,
                    arrowprops=properties)
    return

def do_circle(ax,x,y,colour,label,alpha,relative_size=1.0):
    radius = .1 * np.sqrt(relative_size)
    circle = mpatches.Circle((x,y),radius, ec=colour, fc=colour, lw=8,
                             alpha=alpha)
    ax.add_patch(circle)
    ax.text(x,y,label, ha="center", va="center", 
         family='sans-serif', size=48, color='w')
    return



def draw_state(state, args, labelsON=False):

    colorA, colorB = [.1,.01,.8], [.8,.1,.1]
    fig, ax = plt.subplots(1)
    alpha_main = 1.0
    alpha_faint = 0.6

    x,y = 0,1
    Ay, By = 0.5, -0.5
    obj1x, obj2x = -0.7, 0.7
    
    # A's holds, from left to right, are obj1, the other agent (B), and obj2.
    if state[0]: do_hold(ax,0,Ay,obj1x,0,colorA,alpha_main,-1)
    if state[1]: do_hold(ax,0,Ay,0,By,colorA,alpha_main,-1)
    if state[2]: do_hold(ax,0,Ay,obj2x,0,colorA,alpha_main,1)

    # B's holds: from left to right, are obj1, the other agent (A), and obj2.
    if state[3]: do_hold(ax,0,By,obj1x,0,colorB,alpha_main,1)
    if state[4]: do_hold(ax,0,By,0,Ay,colorB,alpha_main,-1)
    if state[5]: do_hold(ax,0,By,obj2x,0,colorB,alpha_main,-1)

    # this next part should be considered optional...
    # It is about setting the relative sizes of the objects being held.
    # e.g. if agent A holds obj1, it is worth args.VAL1A to it, which could determine its size.
    obj1_rel_size = np.mean([args.VAL1A, args.VAL1B])
    obj2_rel_size = np.mean([args.VAL2A, args.VAL2B])
    # The above are the default sizes. Currently, the average, which is a bit dumb.
    if state[0]: obj1_rel_size = args.VAL1A # agent A holds obj1
    if state[3]: obj1_rel_size = args.VAL1B # agent B holds obj1
    # TODO: what size to show if they BOTH hold it?!
    # TODO: what if NEITHER hold it?! 
    if state[2]: obj2_rel_size = args.VAL2A # agent A holds obj2
    if state[5]: obj2_rel_size = args.VAL2B # agent B holds obj2
    
    # okay draw the objects.
    if labelsON:
        do_circle(ax,obj1x,0,colorA,'a',alpha_faint,obj1_rel_size) # obj1 is the one on the left.
        do_circle(ax,obj2x,0,colorB,'b',alpha_faint,obj2_rel_size) # obj2 is the one on the right.
    else:
        do_circle(ax,obj1x,0,colorA,'',alpha_faint,obj1_rel_size)
        do_circle(ax,obj2x,0,colorB,'',alpha_faint,obj2_rel_size)
    
    do_box(ax, 0,Ay,colorA, 'A', alpha_main)
    do_box(ax, 0,By,colorB, 'B', alpha_main)

    #styles = mpatches.ArrowStyle.get_styles()
    #print(styles.keys())
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    plt.axis('equal')
    plt.axis('off')
    plt.draw()
    filename = str(state).replace('[','').replace(']','').replace(' ','').replace(',','')
    for imgformat in ['png','svg','pdf']:
        f = '{0}.{1}'.format(filename, imgformat)
        if labelsON: f = '{0}_labelled_obj.{1}'.format(filename, imgformat)
        plt.savefig(f,transparent=True)
        plt.close(f)
        print('wrote {0}'.format(f))
    


#==============================================================================

if __name__ == '__main__':
    import argparse        
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Optionally, we can specify the "sizes" of the circular objects, via cmd line, as follows.
    parser.add_argument('--VAL2A', action='store', type=float, default=4., help='VAL2A is val of obj2 to A (cf. default val of obj1 to A is 1).')
    parser.add_argument('--VAL1B', action='store', type=float, default=4., help='VAL1B is val of obj1 to B (cf. default val of obj2 to B is 1).')
    parser.add_argument('--VAL1A', action='store', type=float, default=1., help='VAL1A is val of obj1 to A.')
    parser.add_argument('--VAL2B', action='store', type=float, default=1., help='VAL2B is val of obj2 to B.')
    args = parser.parse_args()
    


    # okay, actually draw all the states.
    plt.ioff()


    for a in [0,1]:
        for b in [0,1]:
            for c in [0,1]:
                for d in [0,1]:
                    for e in [0,1]:
                        for f in [0,1]:
                            draw_state([a,b,c,d,e,f],args,False)
    for state in [[1,0,0,0,0,1], [0,0,1,1,0,0], [0,0,0,1,0,1]]:
        draw_state(state,args,True)


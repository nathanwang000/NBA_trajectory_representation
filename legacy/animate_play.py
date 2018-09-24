import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pickle
import matplotlib.patches as patches
from legacy.code_mapping import gid2name
from collections import Counter

# the court
def courtPlot(ax):
    # basic parameters
    width = 93.996
    height = 50
    r = 23.75
    # config ax
    ax.set_xlim([0, width])
    ax.set_ylim([0, height])
    # entities
    lbasket = (5.2493, 25)
    rbasket = (width-5.2493, 25)
    lchoop = plt.Circle(lbasket, 1.5/2, fill=False, color="k")
    rchoop = plt.Circle(rbasket, 1.5/2, fill=False, color="k")    
    lc3pt = patches.Arc(lbasket, r*2, r*2,
                       theta1=-68.31, theta2=68.31)
    rc3pt = patches.Arc(rbasket, r*2, r*2,
                       theta1=180-68.31, theta2=180+68.31)
    # entities to plot
    # court
    lhoop = ax.add_artist(lchoop)
    rhoop = ax.add_artist(rchoop)    
    l3pt = ax.add_patch(lc3pt)
    r3pt = ax.add_patch(rc3pt)    
    llt = ax.plot([0, 14], [47, 47], "k")
    rlt = ax.plot([width, width-14], [47, 47], "k")    
    llb = ax.plot([0, 14], [3, 3], "k")
    rlb = ax.plot([width, width-14], [3, 3], "k") 
    lft = ax.plot([19, 19], [17, 33], "k")
    rft = ax.plot([width-19, width-19], [17, 33], "k")
    hc = ax.plot([46.998, 46.998], [0, height], "k")
    return (lhoop, l3pt, llt, llb, lft,
            rhoop, r3pt, rlt, rlb, rft, hc)

def framePlot(ax):
    ball = ax.add_artist(plt.Circle((0,0), 0.4, fill=True, color="red"))

    defense_reach = 3.5 # that's half the average wingspan of NBA player
    shoulder_radius = 1 # 24 inch shoulder width is impressive: avg 17-18

    t0c = "black"
    team0 = [ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t0c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t0c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t0c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t0c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t0c))]

    t1c = "red"
    team1 = [ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t1c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t1c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t1c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t1c)),
             ax.add_artist(plt.Circle((0,0), shoulder_radius, fill=True, color=t1c))]

    alpha = 0.2
    t0reach = [ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t0c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t0c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t0c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t0c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t0c))]

    t1reach = [ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t1c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t1c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t1c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t1c)),
               ax.add_artist(plt.Circle((0,0), defense_reach, alpha=alpha, color=t1c))]
    
    team0text = [ax.text(0,0,'') for _ in range(5)]
    team1text = [ax.text(0,0,'') for _ in range(5)]    
    time_text = ax.text(0.05, -3, '')#, transform=ax.transAxes)

    matches = [ax.add_artist(plt.Line2D([0,0], [0,0])),
               ax.add_artist(plt.Line2D([0,0], [0,0])),
               ax.add_artist(plt.Line2D([0,0], [0,0])),
               ax.add_artist(plt.Line2D([0,0], [0,0])),
               ax.add_artist(plt.Line2D([0,0], [0,0]))]
    
    def setFrameTuple(frame, match):
        if frame.ball:
            ball.center = (frame.ball.x, frame.ball.y)

        teams = Counter(map(lambda p: p.team, frame.players))
        teams = list(teams.keys())
        # smaller first
        if teams[0] > teams[1]: teams[0], teams[1] = teams[1], teams[0]
        # plot team 1
        for i, p in enumerate(filter(lambda p: p.team==teams[0], frame.players)):
            x, y = p.x, p.y
            # team0[i].set_data([x], [y])
            player_name = gid2name(p.id)
            team0[i].center = (x, y)
            t0reach[i].center = (x, y)
            team0text[i].set_position([x-len(player_name) / 2 - 2, y+1.3])
            team0text[i].set_text(player_name)
        # plot team2
        for i, p in enumerate(filter(lambda p: p.team==teams[1], frame.players)):
            x, y = p.x, p.y
            #team1[i].set_data([x], [y])
            player_name = gid2name(p.id)
            team1[i].center = (x, y)
            t1reach[i].center = (x, y)            
            team1text[i].set_position([x - len(player_name) / 2 - 2, y+1.3])
            team1text[i].set_text(gid2name(p.id))
        time_text.set_text('time = %.2f' % frame.frameInfo.game_clock)
        if match is not None:
            # add in matches
            match_lines = []
            i = 0
            for player in frame.players:
                if player.id not in match:
                    continue
                def_x, def_y = player.x, player.y
                off = list(filter(lambda p: p.id == match[player.id],
                                  frame.players))[0]
                off_x, off_y = off.x, off.y
                # this might be horribly unstable 
                matches[i].set_xdata([def_x, off_x])
                matches[i].set_ydata([def_y, off_y])
                i += 1
            return (setFrameTuple, (ball,) + (time_text,) +
                    tuple(team0) + tuple(team1) + tuple(t0reach) + tuple(t1reach) + 
                    tuple(team0text) + tuple(team1text) + tuple(match_lines))
    return (setFrameTuple, (ball,) + (time_text,) +
            tuple(team0) + tuple(team1) + tuple(t0reach) + tuple(t1reach) + 
            tuple(team0text) + tuple(team1text))

if __name__ == '__main__':
    title = "nba game simulation for 2013032905"
    from frame import Frame
    frames = pickle.load(open('frames.pkl', 'rb'))
    
    fig = plt.figure()
    ax = plt.axes()
    plt.title(title)

    court_tuple = courtPlot(ax)
    setFrameTuple, frame_tuple = framePlot(ax)

    def update_frame(i):
        setFrameTuple(frames[i])
        return court_tuple + frame_tuple
    
    ani = animation.FuncAnimation(fig, update_frame,
                                  frames=len(frames),
                                  interval=40, blit=False)

    fn = "_".join(title.split()) + ".mp4"
    print("saving annimation ...........")
    ani.save(fn)
    plt.show()

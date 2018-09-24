import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as patches
import numpy as np

# design decision: fold region
REGIONS = 19

def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    return np.rad2deg((ang1 - ang2) % (2 * np.pi))

class Court(object):
    def __init__(self):
        # basic parameters
        self.width = 93.996
        self.height = 50
        self.radius = 23.75
        self.basket = np.array([5.2493, 25])

    def region(self, pts):
        res = []
        for x, y in pts:
            baseRegion = 0
            if x > self.width / 2:
                # map right court to left                
                x = self.width - x
                y = self.height - y
                baseRegion = 0 #REGIONS / 2 # fall back to left, was 19
            region_num = baseRegion + self.region_(x, y)
            res.append(region_num)
        return np.array(res)
        
    def region_(self, x, y):
        innerR = 19 - self.basket[0]
        outerR = 30
        
        basketvec = np.array([x, y]) - self.basket
        angle2basket = angle_between(np.array([0,1]), basketvec)
        angle2freethrow = angle_between(np.array([0,1]),
                                        np.array([19, 33]) - self.basket)
        distance2basket = np.linalg.norm(basketvec)
        # deal with rectangular regions
        if x <= 14 and y <= 3: return 16
        if x <= 14 and y >= 47: return 17
        if x <= self.basket[0]: # back of the board
            # [3, basket[1]-innerR, basket[1], basket[1]+innerR, 47]
            if y >= 3 and y <= 47:
                if y <= self.basket[1] - innerR:
                    return 10
                elif y <= self.basket[1]:
                    return 4
                elif y <= self.basket[1] + innerR:
                    return 5
                else:
                    return 11
        # circular regions
        if distance2basket < innerR:
            if angle2basket < angle2freethrow:
                return 0
            elif angle2basket < 90:
                return 1
            elif angle2basket < 180 - angle2freethrow:
                return 2
            elif angle2basket < 180:
                return 3
        elif distance2basket < self.radius:
            if angle2basket < angle2freethrow:
                return 6
            elif angle2basket < 90:
                return 7
            elif angle2basket < 180 - angle2freethrow:            
                return 8
            elif angle2basket < 180:
                return 9
        elif distance2basket < outerR:
            if angle2basket < angle2freethrow:
                return 12
            elif angle2basket < 90:
                return 13
            elif angle2basket < 180 - angle2freethrow:                        
                return 14
            elif angle2basket < 180:
                return 15
        return 18

    def plotRegion(self):
        xx, yy = np.meshgrid(np.linspace(0, self.width, 200),
                             np.linspace(0, self.height, 200))
        Z = self.region(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)

        # conclusion: hard to get the colors right, just use the original
        colors = ["#aaffc3", "#3cb44b", "#f58231", "#911eb4", "#46f0f0",
                  "#f032e6", "#d2f53c", "#fabebe", "#008080", "#e6beff",
                  "#aa6e28", "#fffac8", "#800000", "#aaffc3", "#808000",
                  "#ffd8b1", "#000080", "#808080", "#FFFFFF"]#, "#000000"]

        # cmap = matplotlib.cm.get_cmap('tab20')
        # colors = [cmap(i) for i in np.linspace(0.2,0.7,19)]
        # colors = colors[::2] + colors[1::2]

        # head = 0
        # end = len(colors)-1
        # new_colors = []
        # while head < end:
        #     new_colors.append(colors[head])
        #     new_colors.append(colors[end])
        #     head += 1
        #     end -= 1
        # if head == end: new_colors.append(colors[end])
        # colors = new_colors
        
        c = plt.contourf(xx, yy, Z, alpha=0.6, levels=[-0.1]+list(range(REGIONS)),
                         colors=colors)
        b = plt.colorbar(orientation='horizontal')
        return c, b
        
    def plot(self, ax):
        width, height, r = self.width, self.height, self.radius
        # config ax
        ax.set_xlim([0, width])
        ax.set_ylim([0, height])
        # entities
        lbasket = self.basket
        rbasket = np.array([self.width - self.basket[0], self.basket[1]])
        lchoop = plt.Circle(lbasket, 1.5/2, fill=False, color="k")
        rchoop = plt.Circle(rbasket, 1.5/2, fill=False, color="k")
        lc3pt = patches.Arc(lbasket, r*2, r*2,
                       theta1=-68.31, theta2=68.31)
        rc3pt = patches.Arc(rbasket, r*2, r*2,
                            theta1=180-68.31, theta2=180+68.31)
        # entities to plot
        lhoop = ax.add_artist(lchoop) # the basket left
        rhoop = ax.add_artist(rchoop) # the basket right
        l3pt = ax.add_patch(lc3pt) # 3 pointer line
        r3pt = ax.add_patch(rc3pt) # 3 pointer right
        llt = ax.plot([0, 14], [47, 47], "k") # top 3pt line left
        rlt = ax.plot([width, width-14], [47, 47], "k") # top 3pt line right
        llb = ax.plot([0, 14], [3, 3], "k") # bottom 3pt line left
        rlb = ax.plot([width, width-14], [3, 3], "k") # bottom 3pt line right
        lft = ax.plot([19, 19], [17, 33], "k") # left free throw line
        rft = ax.plot([width-19, width-19], [17, 33], "k") # right free throw line
        hc = ax.plot([46.998, 46.998], [0, height], "k") # half court line
        return (lhoop, l3pt, llt, llb, lft,
                rhoop, r3pt, rlt, rlb, rft, hc)

if __name__ == '__main__':
    fig = plt.figure()
    ax = plt.axes()
    c = Court()
    c.plot(ax)
    c.plotRegion()
    plt.show()


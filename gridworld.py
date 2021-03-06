import numpy as np
import gridrender as gui
import tkinter.font as tkfont
import numbers
import pdb

from collections import namedtuple
from tkinter import Tk

MDP = namedtuple('MDP', 'S,A,P,R,gamma,d0')


class GridWorld:
    def __init__(self, static_filter = lambda x: True, gamma=0.95, grid=None, render=False, reset_density = None):
        '''
            Tristan adds: reset_density
                If not None it has the dimension of the grid and specify the proba distrib for resetting. 
            Tristan adds: static_filter
            Should of the form:
                def static_filter(s,dist_to_goal=4):
                    objective = np.array([0,len(twoRooms_grid[0])-1])
                    coord_s = np.array(twoRooms.state2coord[s])
                    return np.linalg.norm(objective-coord_s) >= dist_to_goal
        '''
        self.grid = grid

        self.action_names = np.array(['right', 'down', 'left', 'up'])

        self.n_rows, self.n_cols = len(self.grid), max(map(len, self.grid))
        screenHeight = 1080
        screenWidth = 1920
        self.gridSize = min(screenHeight/self.n_rows, screenWidth/self.n_cols)
        
        # Create a map to translate coordinates [r,c] to scalar index
        # (i.e., state) and vice-versa
        self.coord2state = np.empty_like(self.grid, dtype=np.int)
        self.n_states = 0
        self.state2coord = []
        for i in range(self.n_rows):
            for j in range(len(self.grid[i])):
                if self.grid[i][j] != 'x':
                    self.coord2state[i, j] = self.n_states
                    self.n_states += 1
                    self.state2coord.append([i, j])
                else:
                    self.coord2state[i, j] = -1

        # compute the actions available in each state
        self.compute_available_actions()
        self.gamma = gamma
        self.proba_succ = 0.9
        self.render = render
        
        self.static_filter = static_filter
        
        if type(reset_density) == type(None):
            reset_density = 1.0/(self.n_states)*np.ones(self.coord2state.shape)
        
        self.reset_density = []
        for s in range(self.n_states):
            i,j = self.state2coord[s]
            self.reset_density.append(reset_density[i][j])


    def reset(self):
        """
        Returns:
            An initial state randomly drawn from
            the initial distribution
        """
        #x_0 = np.random.randint(0, self.n_states)
        x_0 = np.random.choice(range(self.n_states),p=self.reset_density)
        return x_0



    def step(self, state, action):
        """
        Args:
            state (int): the amount of good
            action (int): the action to be executed

        Returns:
            next_state (int): the state reached by performing the action
            reward (float): a scalar value representing the immediate reward
            absorb (boolean): True if the next_state is absorsing, False otherwise
        """
        r, c = self.state2coord[state]
        assert action in self.state_actions[state]
        if isinstance(self.grid[r][c], numbers.Number):
            return state, 0, True
        else:
            failed = np.random.rand(1) > self.proba_succ
            if action == 0:
                c = min(self.n_cols - 1, c + 1) if not failed else max(0, c - 1)
            elif action == 1:
                r = min(self.n_rows - 1, r + 1) if not failed else max(0, r - 1)
            elif action == 2:
                c = max(0, c - 1) if not failed else min(self.n_cols - 1, c + 1)
            elif action == 3:
                r = max(0, r - 1) if not failed else min(self.n_rows - 1, r + 1)

            if self.grid[r][c] == 'x':
                next_state = state
                r, c = self.state2coord[next_state]
            else:
                next_state = self.coord2state[r, c]
            if isinstance(self.grid[r][c], numbers.Number):
                reward = self.grid[r][c]
                absorb = True
            else:
                reward = 0.
                absorb = False

        if self.render:
            self.show(state, action, next_state, reward)

        return next_state, reward, absorb


    def show(self, state, action, next_state, reward):
        dim = 50
        rows, cols = len(self.grid) + 0.5, max(map(len, self.grid))
        if not hasattr(self, 'window'):
            root = Tk()
            self.window = gui.GUI(root)

            self.window.config(width=cols * (dim + 12), height=rows * (dim + 12))
            my_font = tkfont.Font(family="Arial", size=10, weight="bold")
            for s in range(self.n_states):
                r, c = self.state2coord[s]
                x, y = 10 + c * (dim + 4), 10 + r * (dim + 4)
                if isinstance(self.grid[r][c], numbers.Number):
                    self.window.create_polygon([x, y, x + dim, y, x + dim, y + dim, x, y + dim], outline='black',
                                               fill='blue', width=2)
                    self.window.create_text(x + dim / 2., y + dim / 2., text="{:.1f}".format(self.grid[r][c]),
                                            font=my_font, fill='white')
                else:
                    self.window.create_polygon([x, y, x + dim, y, x + dim, y + dim, x, y + dim], outline='black',
                                               fill='white', width=2)
            self.window.pack()

        my_font = tkfont.Font(family="Arial", size=32, weight="bold")

        r0, c0 = self.state2coord[state]
        r0, c0 = 10 + c0 * (dim + 4), 10 + r0 * (dim + 4)
        x0, y0 = r0 + dim / 2., c0 + dim / 2.
        r1, c1 = self.state2coord[next_state]
        r1, c1 = 10 + c1 * (dim + 4), 10 + r1 * (dim + 4)
        x1, y1 = r1 + dim / 2., c1 + dim / 2.

        if hasattr(self, 'oval2'):
            # self.window.delete(self.line1)
            # self.window.delete(self.oval1)
            self.window.delete(self.oval2)
            self.window.delete(self.text1)
            self.window.delete(self.text2)

        # self.line1 = self.window.create_arc(x0, y0, x1, y1, dash=(3,5))
        # self.oval1 = self.window.create_oval(x0 - dim / 20., y0 - dim / 20., x0 + dim / 20., y0 + dim / 20., dash=(3,5))
        self.oval2 = self.window.create_oval(x1 - dim / 5., y1 - dim / 5., x1 + dim / 5., y1 + dim / 5., fill='red')
        self.text1 = self.window.create_text(dim, (rows - 0.25) * (dim + 12), font=my_font,
                                             text="r= {:.1f}".format(reward), anchor='center')
        self.text2 = self.window.create_text(2 * dim, (rows - 0.25) * (dim + 12), font=my_font,
                                             text="action: {}".format(self.action_names[action]), anchor='center')
        self.window.update()


    def matrix_representation(self):
        """
        Returns:
             A representation of the MDP in matrix form MDP(S, A_s, P, R, gamma) where
             - S is the number of states
             - A_s contains the list of action indices available in each state, i.e.,
                A_s[3] is a list representing the index of actions available in such state
             - P the transition matrix of dimension S x max{|A_s|} x S
             - R the reward matrix of dimension S x max{|A_s|}
        """
        if hasattr(self, 'P_mat'):
            return MDP(self.n_states, self.state_actions, self.P_mat, self.R_mat, self.gamma, self.d0)

        nstates = self.n_states
        nactions = max(map(len, self.state_actions))
        self.P_mat = np.inf * np.ones((nstates, nactions, nstates))
        self.R_mat = np.inf * np.ones((nstates, nactions))
        for s in range(nstates):
            r, c = self.state2coord[s]
            for a_idx, action in enumerate(self.state_actions[s]):
                self.P_mat[s, a_idx].fill(0.)
                if isinstance(self.grid[r][c], numbers.Number):
                    self.P_mat[s, a_idx, s] = 1.
                    self.R_mat[s, a_idx] = 0.
                else:
                    ns_succ, ns_fail = np.inf, np.inf
                    if action == 0:
                        ns_succ = self.coord2state[r, min(self.n_cols - 1, c + 1)]
                        ns_fail = self.coord2state[r, max(0, c - 1)]
                    elif action == 1:
                        ns_succ = self.coord2state[min(self.n_rows - 1, r + 1), c]
                        ns_fail = self.coord2state[max(0, r - 1), c]
                    elif action == 2:
                        ns_succ = self.coord2state[r, max(0, c - 1)]
                        ns_fail = self.coord2state[r, min(self.n_cols - 1, c + 1)]
                    elif action == 3:
                        ns_succ = self.coord2state[max(0, r - 1), c]
                        ns_fail = self.coord2state[min(self.n_rows - 1, r + 1), c]

                    x, y = self.state2coord[ns_fail]
                    if ns_fail == -1 or self.grid[x][y] == 'x':
                        ns_fail = s

                    self.P_mat[s, a_idx, ns_succ] = self.proba_succ
                    self.P_mat[s, a_idx, ns_fail] = 1. - self.proba_succ

                    x, y = self.state2coord[ns_fail]
                    x2, y2 = self.state2coord[ns_succ]
                    r_succ, r_fail = 0., 0.
                    if isinstance(self.grid[x][y], numbers.Number):
                        r_fail = self.grid[x][y]
                    if isinstance(self.grid[x2][y2], numbers.Number):
                        r_succ = self.grid[x2][y2]

                    self.R_mat[s, a_idx] = self.proba_succ * r_succ + (1 - self.proba_succ) * r_fail

        self.d0 = np.ones((nstates,)) / nstates

        return MDP(nstates, self.state_actions, self.P_mat, self.R_mat, self.gamma, self.d0)


    def compute_available_actions(self):
        # define available actions in each state
        # actions are indexed by: 0=right, 1=down, 2=left, 3=up
        self.state_actions = []
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                if isinstance(self.grid[i][j], numbers.Number):
                    self.state_actions.append([0])
                elif self.grid[i][j] != 'x':
                    actions = [0, 1, 2, 3]
                    if i == 0:
                        actions.remove(3)
                    if j == self.n_cols - 1:
                        actions.remove(0)
                    if i == self.n_rows - 1:
                        actions.remove(1)
                    if j == 0:
                        actions.remove(2)

                    for a in actions.copy():
                        r, c = i, j
                        if a == 0:
                            c = min(self.n_cols - 1, c + 1)
                        elif a == 1:
                            r = min(self.n_rows - 1, r + 1)
                        elif a == 2:
                            c = max(0, c - 1)
                        else:
                            r = max(0, r - 1)
                        if self.grid[r][c] == 'x':
                            actions.remove(a)

                    self.state_actions.append(actions)


    def static_filter(state, dist_to_goal=4):
        # Returns a vector of boolean indicating, one for each state of trajectory
        objective = np.argwhere(array(twoRooms.grid) == '1').ravel()
        coords = np.array(self.state2coord)[state]
        return np.linalg.norm(objective-coords) >= dist_to_goal


# What does a grid look like?
# Permitted locations are ''
# Unavailable locations are 'x'
# Goal is 1
grid1 = [
    ['', '', '', 1],
    ['', 'x', '', -1],
    ['', '', '', '']
]

GridWorld1 = GridWorld(gamma=0.95, grid=grid1)


def two_rooms_grid(room_width, room_height, doorway_pos, doorway_height, goal_height):
    assert doorway_height > 0
    assert doorway_pos + doorway_height <= room_height
    grid_width = 2*room_width + 1
    grid_height = room_height
    grid = np.chararray((grid_height, grid_width))
    grid[:] = ''
    grid[:,room_width] = 'x'
    grid[
        grid_height-1-doorway_pos:grid_height-1-doorway_pos+doorway_height,
        room_width
    ] = ''
    grid = grid.tolist()
    grid[goal_height][grid_width-1] = 1
    return byteToString(grid)


def four_rooms_grid(room_width, room_height, doorway_pos_v, doorway_pos_h, doorway_height, goal_width, goal_height):
    assert doorway_height > 0
    assert doorway_pos_v + doorway_height <= room_width
    assert doorway_pos_h + doorway_height <= room_height
    grid_width = 2*room_width + 1
    grid_height = 2*room_height + 1
    grid = np.chararray((grid_height, grid_width))
    grid[:] = ''
    grid[:,room_width] = 'x'
    grid[room_height,:] = 'x'
    grid[
        room_height-1-doorway_pos_h:room_height-1-doorway_pos_h+doorway_height,
        room_width
    ] = ''
    grid[
        room_height+1+doorway_pos_h-doorway_height:room_height+1+doorway_pos_h,
        room_width
    ] = ''
    grid[
        room_height,
        room_width-1-doorway_pos_v:room_width-1-doorway_pos_v+doorway_height
    ] = ''
    grid[
        room_height,
        room_width+1+doorway_pos_v-doorway_height:room_width+1+doorway_pos_v,
    ] = ''
    grid = grid.tolist()
    grid[goal_height][goal_width] = 1
    return byteToString(grid)


def byteToString(grid):
    n = len(grid)
    for row in range(n):
        m = len(grid[row])
        for col in range(m):
            try:
                grid[row][col] = grid[row][col].decode('ascii')
            except AttributeError:
                pass
    return grid


def two_rooms_computeOptions(room_width, room_height, doorway_pos, doorway_height):
    grid_width = 2*room_width + 1
    grid_height = room_height
    
    upward_initSet = np.zeros((grid_height, grid_width))
    upward_initSet[grid_height-1-doorway_pos:,:room_width] = 1
    
    downward_initSet = np.zeros((grid_height, grid_width))
    downward_initSet[:grid_height-doorway_pos,:room_width] = 1    # Includes the medial line, if there is one
    
    quitMap = np.zeros((grid_height, grid_width))
    quitMap[grid_height-1-doorway_pos:grid_height-1-doorway_pos+doorway_height,room_width] = 1
    
    upward_policy = np.zeros((grid_height, grid_width))
    upward_policy[grid_height-1-doorway_pos+doorway_height:,:room_width] = 3
    upward_policy[grid_height-1-doorway_pos:grid_height-1-doorway_pos+doorway_height,:room_width+1] = 0

    downward_policy = np.zeros((grid_height, grid_width))
    downward_policy[:grid_height-1-doorway_pos,:room_width] = 1
    downward_policy[grid_height-1-doorway_pos:grid_height-1-doorway_pos+doorway_height,:room_width+1] = 0
    
    return [downward_initSet, upward_initSet, quitMap, downward_policy, upward_policy]


import pygame
from queue import PriorityQueue
import time

WIDTH = 800
WIN = pygame.display.set_mode((WIDTH,WIDTH))
pygame.display.set_caption("A* Path finding Algorithm : By CHIRAG GOYAL")

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165 ,0)
GREY = (128, 128, 128)
TURQUOISE = (64, 224, 208)

class Spot:
    def __init__(self,row,col,width,total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width
        self.color = WHITE
        self.neighbours = []
        self.width = width
        self.total_rows = total_rows
    
    def get_pos(self):
        return self.row,self.col
    
    def is_close(self):
        return self.color == RED

    def is_barrier(self):
        return self.color == BLACK
    
    def is_open(self):
        return self.color == GREEN;
    
    def is_start(self):
        return self.color == ORANGE
    
    def is_end(self):
        return self.color == PURPLE
    
    def reset(self):
        self.color = WHITE
    
    def make_closed(self):
        self.color = RED
    
    def make_open(self):
        self.color = GREEN
    
    def make_barrier(self):
        self.color = BLACK
    
    def make_start(self):
        self.color = ORANGE

    def make_end(self):
        self.color = TURQUOISE
    
    def make_path(self):
        self.color = PURPLE
    
    def draw(self,win):
        pygame.draw.rect(win,self.color,(self.x,self.y,self.width,self.width))
    
    def check(self,row,col,tot,grid):
        return row >= 0 and row < tot and col >= 0 and col < tot and not grid[row][col].is_barrier();

    def update_neighbours(self,grid):
        self.neighbours = []
        row = self.row
        col =self.col
        tot = self.total_rows

        if(self.check(row,col-1,tot,grid)):
            self.neighbours.append(grid[row][col-1])
        if(self.check(row+1,col,tot,grid)):
            self.neighbours.append(grid[row+1][col])
        if(self.check(row,col+1,tot,grid)):
            self.neighbours.append(grid[row][col+1])
        if(self.check(row-1,col,tot,grid)):
            self.neighbours.append(grid[row-1][col])

    def __lt__(self,other):
        return False

def h(p1,p2):
    x1,y1 = p1
    x2,y2 = p2
    return abs(x1-x2) + abs(y1-y2)

# making final path
def reconstruct(draw,cameFrom,curr):
    while curr in cameFrom:
        curr.make_path()
        curr = cameFrom[curr]
        draw()


def algorithm(draw,grid,start,end):
    # draw() # lambda function
    count = 0
    openSet = PriorityQueue()
    openSet.put((0,count,start))
    cameFrom = {}
    gScore = {spot: float("inf") for row in grid for spot in row}
    gScore[start] = 0
    fScore = {spot: float("inf") for row in grid for spot in row}
    fScore[start] = h(start.get_pos(),end.get_pos())

    openSetHash = {start}
    while not openSet.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        current = openSet.get()[2];
        openSetHash.remove(current)

        if current == end:
            reconstruct(draw,cameFrom,end)
            start.make_open()
            end.make_closed()
            draw()
            return True
        
        for neighbour in current.neighbours:
            # time.sleep(0.09)
            temp_gScore = gScore[current] + 1
            if temp_gScore < gScore[neighbour]:
                cameFrom[neighbour] = current
                gScore[neighbour] = temp_gScore
                fScore[neighbour] = gScore[neighbour] + h(neighbour.get_pos(),end.get_pos())
                # time.sleep(0.09)

                if neighbour not in openSetHash:
                    count += 1
                    openSet.put((fScore[neighbour],count,neighbour))
                    openSetHash.add(neighbour)
                    neighbour.make_open()
                    draw()
                    time.sleep(0.01)
        draw()
        # time.sleep(0.2)
        if current != start:
            current.make_closed() 
    return False


def make_grid(rows,width):
    grid = []
    gap = width//rows

    for i in range(rows):
        grid.append([])
        for j in range(rows):
            spot = Spot(i,j,gap,rows)
            grid[i].append(spot)
    return grid

def draw_grid(win,rows,width):
    gap = width//rows
    # rows grid lines
    for i in range(rows):
        pygame.draw.line(win,GREY,(0,i*gap),(width,i*gap)) 
    # columns grid lines
    for i in range(rows):
        pygame.draw.line(win,GREY,(i*gap,0),(i*gap,width))

def draw(win,grid,rows,width):
    win.fill(WHITE)

    for row in grid:
        for spot in row:
            spot.draw(win)
    draw_grid(win,rows,width)
    pygame.display.update()

def get_clicked_pos(pos,rows,width):
    gap = width//rows
    x,y = pos
    row = x//gap
    col = y//gap

    return row,col


def main(win,width):
    ROWS = 50
    grid = make_grid(ROWS,width)

    start = None
    end = None

    run = True
    while(run):
        draw(win,grid,ROWS,width)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                row,col = get_clicked_pos(pos,ROWS,width)
                spot = grid[row][col]
                if not start and spot != end:
                    start = spot
                    start.make_start()
                elif not end and spot != start:
                    end = spot
                    end.make_end()
                
                elif spot != end and spot != start:
                    spot.make_barrier()

            elif pygame.mouse.get_pressed()[2]:
                pass

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and start and end:
                    for row in grid:
                        for spot in row:
                            # Checking for free neighbours (not barriers) and appending them into self.neighbours
                            spot.update_neighbours(grid)
                    # Starting Algorithm
                    algorithm(lambda: draw(win,grid,ROWS,width),grid,start,end)
                if event.key == pygame.K_r:
                    start = None
                    end = None
                    grid = make_grid(ROWS,width)

    pygame.quit();

#Calling main function
main(WIN,WIDTH)
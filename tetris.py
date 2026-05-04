import curses
import random
import time

# CONFIGURAÇÕES 

COLS, ROWS = 8, 15    # tamanho do grid
FPS = 2               # velocidade de queda

COLOR_BLACK = 0
COLOR_CYAN = 1
COLOR_BLUE = 2
COLOR_ORANGE = 3
COLOR_YELLOW = 4
COLOR_GREEN = 5
COLOR_MAGENTA = 6
COLOR_RED = 7


# lista de cores das peças
COLORS = [COLOR_CYAN, COLOR_BLUE, COLOR_ORANGE, COLOR_YELLOW, COLOR_GREEN, COLOR_MAGENTA, COLOR_RED]

# formatos das peças
SHAPES = [
    [[1,1,1,1]],
    [[2,0,0],[2,2,2]],
    [[0,0,3],[3,3,3]],
    [[4,4],[4,4]],
    [[0,5,5],[5,5,0]],
    [[0,6,0],[6,6,6]],
    [[7,7,0],[0,7,7]]
]

BLOCK = "#"

# SAFE DRAW 
def safe_addstr(scr, y, x, text, attr=0):
    h, w = scr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        try:
            scr.addstr(y, x, text, attr)
        except:
            pass

# RANK 

def get_name(scr):
    curses.echo()
    scr.clear()
    scr.addstr(5,5,"Nome (3 letras): ")
    scr.refresh()

    name = ""
    while len(name) < 3:
        ch = scr.getch()
        if ch in range(65,91) or ch in range(97,123):
            name += chr(ch).upper()
            scr.addstr(5,25+len(name)-1,name[-1])
            scr.refresh()

    curses.noecho()
    return name

def save_score(name, score):
    with open("ranking.txt","a") as f:
        f.write(f"{name} {score}\n")

def load_rank():
    scores=[]
    try:
        with open("ranking.txt") as f:
            for l in f:
                n,s=l.split()
                scores.append((n,int(s)))
    except:
        pass
    return sorted(scores,key=lambda x:x[1],reverse=True)[:10]

def show_rank(scr):
    scores = load_rank()

    while True:
        scr.erase()

        scr.addstr(2,5,"=== RANKING ===")

        for i,(n,s) in enumerate(scores):
            scr.addstr(4+i,5,f"{i+1}. {n} - {s}")

        scr.addstr(16,5,"Pressione qualquer tecla...")
        scr.refresh()

        key = scr.getch()
        if key != -1:
            break

        time.sleep(0.05)

    curses.flushinp()
    scr.erase()
    scr.refresh()

# LÓGICA DO JOGO 

class Piece:
    # representa uma peça do tetris
    def __init__(self,x,y,shape,color):
        self.x=x
        self.y=y
        self.shape=shape
        self.color=color

    def rotate(self):
        # rotaciona a peça
        self.shape=[list(r) for r in zip(*self.shape[::-1])]


def new_piece():
    # cria nova peça aleatória
    i=random.randint(0,6)
    return Piece(3,0,[row[:] for row in SHAPES[i]],COLORS[i])


def grid_from_locked(locked):
    # cria grid com peças fixas
    g=[[0]*COLS for _ in range(ROWS)]
    for (x,y),c in locked.items():
        if 0<=x<COLS and 0<=y<ROWS:
            g[y][x]=c
    return g


def positions(p):
    # retorna posições ocupadas pela peça
    return [(p.x+j,p.y+i)
            for i,r in enumerate(p.shape)
            for j,v in enumerate(r) if v]


def valid(p, grid):
    # verifica colisão e limites
    for x,y in positions(p):
        if x < 0 or x >= COLS:
            return False
        if y >= ROWS:
            return False
        if y >= 0 and grid[y][x] != 0:
            return False
    return True


def clear_rows(grid, locked):
    # remove linhas
    cleared = 0

    for y in range(ROWS-1, -1, -1):
        if 0 not in grid[y]:
            cleared += 1

            for x in range(COLS):
                locked.pop((x,y), None)

            for (lx, ly) in sorted(list(locked), key=lambda k:k[1], reverse=True):
                if ly < y:
                    locked[(lx, ly+1)] = locked.pop((lx, ly))

    return cleared


# GAME

class Game:
    # classe principal do jogo
    def __init__(self,scr):
        self.s=scr
        curses.curs_set(0)
        curses.start_color()
        self.s.nodelay(True)
        self.s.keypad(True)

        for c in COLORS:
            curses.init_pair(c,c,curses.COLOR_BLACK)

        self.locked={}
        self.piece=new_piece()
        self.next=new_piece()
        self.last=time.time()
        self.speed=1/FPS
        self.score=0
        self.over=False


    def draw(self):
        # desenha jogo na tela
        self.s.erase()

        sy,sx=1,2

        safe_addstr(self.s,sy-1,sx-1,"+"+"-"*(COLS*2)+"+")
        for y in range(ROWS):
            safe_addstr(self.s,sy+y,sx-1,"|")
            safe_addstr(self.s,sy+y,sx+COLS*2,"|")
        safe_addstr(self.s,sy+ROWS,sx-1,"+"+"-"*(COLS*2)+"+")

        grid=grid_from_locked(self.locked)

        for y in range(ROWS):
            for x in range(COLS):
                if grid[y][x]:
                    safe_addstr(self.s,sy+y,sx+x*2,BLOCK+" ",curses.color_pair(grid[y][x]))

        for x,y in positions(self.piece):
            if y>=0:
                safe_addstr(self.s,sy+y,sx+x*2,BLOCK+" ",curses.color_pair(self.piece.color))

        safe_addstr(self.s,1,COLS*2+5,f"Score: {self.score}")

        self.s.refresh()


    def update(self):
        # atualiza lógica do jogo
        if time.time() - self.last > self.speed:
            self.last = time.time()

            self.piece.y += 1
            grid = grid_from_locked(self.locked)

            if not valid(self.piece, grid):
                self.piece.y -= 1

                for x, y in positions(self.piece):
                    if y >= 0:
                        self.locked[(x, y)] = self.piece.color

                self.piece = self.next
                self.next = new_piece()

                grid = grid_from_locked(self.locked)

                self.score += clear_rows(grid, self.locked) * 10

                if any(y < 1 for _, y in self.locked):
                    self.over = True


    def input(self):
        # captura input do jogador
        k=self.s.getch()
        grid = grid_from_locked(self.locked)

        if k==ord('q'):
            self.over=True
        elif k==curses.KEY_LEFT:
            self.piece.x-=1
            if not valid(self.piece,grid): self.piece.x+=1
        elif k==curses.KEY_RIGHT:
            self.piece.x+=1
            if not valid(self.piece,grid): self.piece.x-=1
        elif k==curses.KEY_DOWN:
            self.piece.y+=1
            if not valid(self.piece,grid): self.piece.y-=1
        elif k==curses.KEY_UP:
            old=self.piece.shape
            self.piece.rotate()
            if not valid(self.piece,grid):
                self.piece.shape=old


    def run(self):
        # loop principal do jogo
        while True:
            self.input()
            self.update()
            self.draw()

            if self.over:
                name=get_name(self.s)
                save_score(name,self.score)
                show_rank(self.s)
                return


# MENU

def menu(scr):
    # menu inicial
    opt=0
    items=["Jogar","Ranking","Sair"]

    while True:
        scr.erase()

        scr.addstr(3,5,"=== TETRIS ===")

        for i,t in enumerate(items):
            attr=curses.A_REVERSE if i==opt else 0
            scr.addstr(6+i,5,t,attr)

        scr.refresh()

        k=scr.getch()

        if k==curses.KEY_UP: opt=(opt-1)%3
        elif k==curses.KEY_DOWN: opt=(opt+1)%3
        elif k==10: return opt

        time.sleep(0.05)


# MAIN

def main(stdscr):
    # controla fluxo do jogo
    while True:
        c=menu(stdscr)
        if c==0:
            Game(stdscr).run()
        elif c==1:
            show_rank(stdscr)
        else:
            break

curses.wrapper(main)
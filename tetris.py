import pygame
import random

CELL_SIZE = 30
COLS = 10
ROWS = 20
WIDTH = CELL_SIZE * COLS
HEIGHT = CELL_SIZE * ROWS
FPS = 60

BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
COLORS = [
    (0, 255, 255),  # I
    (0, 0, 255),    # J
    (255, 165, 0),  # L
    (255, 255, 0),  # O
    (0, 255, 0),    # S
    (128, 0, 128),  # T
    (255, 0, 0)     # Z
]
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[2, 0, 0], [2, 2, 2]],  # J
    [[0, 0, 3], [3, 3, 3]],  # L
    [[4, 4], [4, 4]],  # O
    [[0, 5, 5], [5, 5, 0]],  # S
    [[0, 6, 0], [6, 6, 6]],  # T
    [[7, 7, 0], [0, 7, 7]]   # Z
]

class Tetromino:
    def __init__(self, x, y, shape, color):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = color

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def create_grid(locked_positions={}):
    grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
    for y in range(ROWS):
        for x in range(COLS):
            if (x, y) in locked_positions:
                grid[y][x] = locked_positions[(x, y)]
    return grid

def convert_shape_format(piece):
    positions = []
    for i, row in enumerate(piece.shape):
        for j, val in enumerate(row):
            if val:
                positions.append((piece.x + j, piece.y + i))
    return positions

def valid_space(piece, grid):
    accepted = [[(x, y) for x in range(COLS) if grid[y][x] == BLACK] for y in range(ROWS)]
    accepted = [x for row in accepted for x in row]
    formatted = convert_shape_format(piece)
    for pos in formatted:
        if pos not in accepted:
            if pos[1] > -1:
                return False
    return True

def check_lost(positions):
    for _, y in positions:
        if y < 1:
            return True
    return False

def clear_rows(grid, locked):
    inc = 0
    for i in range(ROWS - 1, -1, -1):
        row = grid[i]
        if BLACK not in row:
            inc += 1
            for j in range(COLS):
                try:
                    del locked[(j, i)]
                except:
                    continue
    if inc > 0:
        # Move todas as linhas acima para baixo
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < i:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)
    return inc

def draw_grid(surface, grid):
    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(surface, grid[y][x], (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 0)
            pygame.draw.rect(surface, GRAY, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

def draw_window(surface, grid, score=0):
    surface.fill(BLACK)
    draw_grid(surface, grid)
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render(f'Score: {score}', 1, (255, 255, 255))
    surface.blit(label, (10, 10))

def get_shape():
    index = random.randint(0, len(SHAPES) - 1)
    return Tetromino(3, 0, SHAPES[index], COLORS[index])

def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Tetris')
    clock = pygame.time.Clock()
    locked_positions = {}
    grid = create_grid(locked_positions)

    current_piece = get_shape()
    next_piece = get_shape()
    fall_time = 0
    fall_speed = 0.5
    score = 0
    run = True
    change_piece = False

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        clock.tick(FPS)

        if fall_time / 1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    old_shape = current_piece.shape
                    current_piece.rotate()
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                        if not valid_space(current_piece, grid):
                            current_piece.x += 2
                            if not valid_space(current_piece, grid):
                                current_piece.shape = old_shape
                                current_piece.x -= 1

        shape_pos = convert_shape_format(current_piece)
        for x, y in shape_pos:
            if y > -1:
                grid[y][x] = current_piece.color

        if change_piece:
            for pos in shape_pos:
                locked_positions[pos] = current_piece.color
            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            score += clear_rows(grid, locked_positions) * 10

        draw_window(win, grid, score)
        pygame.display.update()

        if check_lost(locked_positions):
            run = False

    pygame.quit()

if __name__ == '__main__':
    main()
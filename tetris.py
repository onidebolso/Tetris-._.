import curses
import random
import time

COLS = 8
ROWS = 15
FPS = 2  # Blocks fall every ~0.5 seconds (1/FPS)

# Color indices for curses (using terminal color pairs)
COLOR_BLACK = 0
COLOR_CYAN = 1
COLOR_BLUE = 2
COLOR_ORANGE = 3
COLOR_YELLOW = 4
COLOR_GREEN = 5
COLOR_MAGENTA = 6
COLOR_RED = 7

# Map piece color indices to curses color pairs
COLORS = [
    COLOR_CYAN,     # I
    COLOR_BLUE,     # J
    COLOR_ORANGE,   # L
    COLOR_YELLOW,   # O
    COLOR_GREEN,    # S
    COLOR_MAGENTA,  # T
    COLOR_RED       # Z
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

# Character to represent a block (use simple char for compatibility)
BLOCK_CHAR = '#'
EMPTY_CHAR = ' '

class Tetromino:
    def __init__(self, x, y, shape, color):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = color

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def create_grid(locked_positions=None):
    if locked_positions is None:
        locked_positions = {}
    grid = [[COLOR_BLACK for _ in range(COLS)] for _ in range(ROWS)]
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
    accepted = [[(x, y) for x in range(COLS) if grid[y][x] == COLOR_BLACK] for y in range(ROWS)]
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
        if COLOR_BLACK not in row:
            inc += 1
            for j in range(COLS):
                try:
                    del locked[(j, i)]
                except:
                    continue
    if inc > 0:
        # Move all lines above down
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < i:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)
    return inc


def get_shape():
    index = random.randint(0, len(SHAPES) - 1)
    return Tetromino(3, 0, [row[:] for row in SHAPES[index]], COLORS[index])

class TetrisGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # Check terminal size
        min_height = ROWS + 5  # grid + borders + info
        min_width = COLS * 2 + 15  # grid + borders + info
        if curses.LINES < min_height or curses.COLS < min_width:
            stdscr.addstr(0, 0, f"Terminal too small. Need at least {min_width}x{min_height}, got {curses.COLS}x{curses.LINES}")
            stdscr.refresh()
            stdscr.getch()
            raise SystemExit("Terminal size too small")
        
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        stdscr.timeout(50)  # 50ms timeout for getch
        
        # Initialize colors
        self._init_colors()
        
        # Game state
        self.locked_positions = {}
        self.grid = create_grid(self.locked_positions)
        self.current_piece = get_shape()
        self.next_piece = get_shape()
        self.fall_time = 0
        self.fall_speed = 1.0 / FPS  # Fall every 0.5 seconds
        self.score = 0
        self.change_piece = False
        self.game_over = False
        self.last_fall_time = time.time()

    def _init_colors(self):
        """Initialize curses color pairs"""
        curses.init_pair(COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
        # Orange is approximated with red (terminal limitation)
        curses.init_pair(COLOR_ORANGE, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def update(self):
        """Update game logic"""
        if self.game_over:
            return
        
        self.grid = create_grid(self.locked_positions)
        
        # Check if piece should fall
        current_time = time.time()
        if current_time - self.last_fall_time > self.fall_speed:
            self.last_fall_time = current_time
            self.current_piece.y += 1
            
            if not valid_space(self.current_piece, self.grid) and self.current_piece.y > 0:
                self.current_piece.y -= 1
                self.change_piece = True

        if self.change_piece:
            shape_pos = convert_shape_format(self.current_piece)
            for pos in shape_pos:
                self.locked_positions[pos] = self.current_piece.color
            self.current_piece = self.next_piece
            self.next_piece = get_shape()
            self.change_piece = False
            
            # Clear rows and update score
            rows_cleared = clear_rows(self.grid, self.locked_positions)
            self.score += rows_cleared * 10

            if check_lost(self.locked_positions):
                self.game_over = True

    def _draw_grid(self, start_y, start_x):
        """Draw the game grid"""
        # Draw border
        self.stdscr.addstr(start_y - 1, start_x - 1, '+' + '-' * (COLS * 2) + '+')
        for y in range(ROWS):
            self.stdscr.addstr(start_y + y, start_x - 1, '|')
            self.stdscr.addstr(start_y + y, start_x + COLS * 2, '|')
        self.stdscr.addstr(start_y + ROWS, start_x - 1, '+' + '-' * (COLS * 2) + '+')
        
        # Draw locked positions
        for y in range(ROWS):
            for x in range(COLS):
                color = self.grid[y][x]
                if color != COLOR_BLACK:
                    attr = curses.color_pair(color) | curses.A_BOLD
                    self.stdscr.addstr(start_y + y, start_x + x * 2, BLOCK_CHAR + ' ', attr)
                else:
                    self.stdscr.addstr(start_y + y, start_x + x * 2, '  ')

    def _draw_falling_piece(self, start_y, start_x):
        """Draw the current falling piece"""
        shape_pos = convert_shape_format(self.current_piece)
        for x, y in shape_pos:
            if 0 <= y < ROWS and 0 <= x < COLS and y > -1:
                attr = curses.color_pair(self.current_piece.color) | curses.A_BOLD
                self.stdscr.addstr(start_y + y, start_x + x * 2, BLOCK_CHAR + ' ', attr)

    def _draw_info(self, start_y):
        """Draw score and next piece info"""
        info_y = start_y
        self.stdscr.addstr(info_y, COLS * 2 + 5, f'Score: {self.score}')
        self.stdscr.addstr(info_y + 2, COLS * 2 + 5, 'Next:')
        
        # Draw next piece
        next_y = info_y + 3
        next_x = COLS * 2 + 5
        for i, row in enumerate(self.next_piece.shape):
            for j, val in enumerate(row):
                if val:
                    attr = curses.color_pair(self.next_piece.color) | curses.A_BOLD
                    self.stdscr.addstr(next_y + i, next_x + j * 2, BLOCK_CHAR + ' ', attr)

    def _draw_controls(self, start_y):
        """Draw control instructions"""
        ctrl_y = start_y + 12
        ctrl_x = COLS * 2 + 5
        self.stdscr.addstr(ctrl_y, ctrl_x, 'Controls:')
        self.stdscr.addstr(ctrl_y + 1, ctrl_x, 'LEFT/RIGHT - Move')
        self.stdscr.addstr(ctrl_y + 2, ctrl_x, 'DOWN - Drop')
        self.stdscr.addstr(ctrl_y + 3, ctrl_x, 'UP - Rotate')
        self.stdscr.addstr(ctrl_y + 4, ctrl_x, 'Q - Quit')

    def draw(self):
        """Draw the game board"""
        self.stdscr.clear()
        start_y = 1
        start_x = 2
        
        self._draw_grid(start_y, start_x)
        self._draw_falling_piece(start_y, start_x)
        self._draw_info(start_y)
        self._draw_controls(start_y)
        
        if self.game_over:
            msg = 'GAME OVER! Press Q to quit.'
            self.stdscr.addstr(start_y + ROWS + 2, start_x, msg, curses.A_BOLD)
        
        self.stdscr.refresh()

    def handle_input(self):
        """Handle keyboard input"""
        try:
            ch = self.stdscr.getch()
        except:
            ch = -1
        
        if ch == -1:
            return
        
        # Convert character to key name
        if ch == ord('q') or ch == ord('Q'):
            self.game_over = True
        elif ch == curses.KEY_LEFT or ch == ord('a'):
            self.current_piece.x -= 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.x += 1
        elif ch == curses.KEY_RIGHT or ch == ord('d'):
            self.current_piece.x += 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.x -= 1
        elif ch == curses.KEY_DOWN or ch == ord('s'):
            self.current_piece.y += 1
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.y -= 1
        elif ch == curses.KEY_UP or ch == ord('w') or ch == ord(' '):
            old_shape = [row[:] for row in self.current_piece.shape]
            self.current_piece.rotate()
            if not valid_space(self.current_piece, self.grid):
                self.current_piece.x -= 1
                if not valid_space(self.current_piece, self.grid):
                    self.current_piece.x += 2
                    if not valid_space(self.current_piece, self.grid):
                        self.current_piece.shape = old_shape
                        self.current_piece.x -= 1

    def run(self):
        """Main game loop"""
        while True:
            self.handle_input()
            self.update()
            self.draw()
            
            if self.game_over:
                # Wait for quit input
                try:
                    ch = self.stdscr.getch()
                    if ch == ord('q') or ch == ord('Q'):
                        break
                except:
                    pass


def main(stdscr):
    game = TetrisGame(stdscr)
    try:
        game.run()
    finally:
        curses.curs_set(1)  # Show cursor again


if __name__ == '__main__':
    curses.wrapper(main)
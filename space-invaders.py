import curses # based on ncurses in C; handles text-based UIs that run in terminal
import time

class SpaceInvaders:
    def __init__(self, stdscr, debug):
        self.stdscr = stdscr # stdscr is 'standard screen' in C
        self.height, self.width = stdscr.getmaxyx() # number of rows and columns
        self.debug = debug
        self.counter = 0
        self.update_freq = 5 # 5 is slow; enemy position is updated every 5 clock ticks to start
        
        # game area dimensions (leave border)
        self.game_width = min(self.width - 6, 20) 
        self.game_height = min(self.height - 6, 16)

        # upper left corner origin
        self.start_x = (self.width - self.game_width) // 2
        self.start_y = (self.height - self.game_height) // 2
        
        # starting player position (middle bottom)
        self.player_x = self.game_width // 2
        self.player_y = self.game_height - 1
        
        # Initialize enemies; 2 rows of 3 enemies each
        self.enemies = []
        self.enemy_direction = "right"
        self.init_enemies()
        
        # game loop setting
        self.running = True

        # Setup curses 
        stdscr.keypad(True)    # Enable special keys (arrows, function keys, etc.)
        curses.curs_set(0)     # Hide cursor
        stdscr.timeout(100)    # 100ms timeout for input (comment out to step through on input
        self.stdscr.nodelay(True) # Turn off automatic refresh

    def init_enemies(self):
        """Initialize a 2x3 grid of enemies"""
        self.enemies = []
        start_x = 3
        start_y = 1
        spacing_x = 4
        spacing_y = 2
        
        for row in range(2):
            for col in range(3):
                enemy = {
                    'x': start_x + col * spacing_x,
                    'y': start_y + row * spacing_y,
                    'alive': True
                }
                self.enemies.append(enemy)

    def debug_message(self, message, line=1):
        if self.debug:
            self.stdscr.addstr(line, 0, str(message)[:self.width])

        
    def draw_border(self):
        # Top and bottom borders
        for x in range(self.game_width + 1):
            self.stdscr.addch(self.start_y, self.start_x + x, '-')
            self.stdscr.addch(self.start_y + self.game_height, self.start_x + x, '_')
        
        # Left and right borders
        for y in range(self.game_height + 1):
            self.stdscr.addch(self.start_y + y, self.start_x, '|')
            self.stdscr.addch(self.start_y + y, self.start_x + self.game_width, '|')
    
        # joystick
        self.stdscr.addstr(self.start_y + self.game_height + 2, self.start_x + self.game_width // 2, '🕹️')

    def draw_player(self):
        self.stdscr.addch(self.start_y + self.player_y, self.start_x + self.player_x, '^')
    
    def draw_enemies(self):
        """draw all living enemies (and check if any alive while we're at it)"""
        any_alive = False

        for enemy in self.enemies:
            if enemy['alive']:
                any_alive = True
                self.stdscr.addch(self.start_y + enemy['y'], self.start_x + enemy['x'], '👾')
        
        if not any_alive:
            mid_screen_y = self.start_y + self.game_height // 2
            mid_screen_x = self.start_x + self.game_width // 2
            self.stdscr.addstr(mid_screen_y, mid_screen_x, '🐐')
            
    def update_enemies(self):
        """move all enemies"""
        if self.counter % self.update_freq == 0:  # Move every 3 frames for slower movement
            # Check if we need to change direction
            leftmost = min(enemy['x'] for enemy in self.enemies if enemy['alive'])
            rightmost = max(enemy['x'] for enemy in self.enemies if enemy['alive'])
            
            if self.enemy_direction == "right" and rightmost >= self.game_width - 2:
                # Hit right wall - move down, change direction, speed up
                self.enemy_direction = "left"
                for enemy in self.enemies:
                    if enemy['alive']:
                        enemy['y'] += 1
                self.update_freq = max(self.update_freq - 1, 1)
            elif self.enemy_direction == "left" and leftmost <= 1:
                # Hit left wall - move down, change direction, speed up
                self.enemy_direction = "right"
                for enemy in self.enemies:
                    if enemy['alive']:
                        enemy['y'] += 1
                self.update_freq = max(self.update_freq - 1, 1)
            else:
                # Normal horizontal movement
                move_amount = 1 if self.enemy_direction == "right" else -1
                for enemy in self.enemies:
                    if enemy['alive']:
                        enemy['x'] += move_amount

    def handle_input(self):
        key = self.stdscr.getch()
        self.debug_message(f"input key: {key}", line=0)

        if key == 27 or key == ord('q'): # 'esc' key ASCII value is 27
            self.running = False
        elif key == curses.KEY_LEFT:
            if self.player_x > 1:
                self.player_x -= 1
        elif key == curses.KEY_RIGHT:
            if self.player_x < self.game_width - 1:
                self.player_x += 1
    
    def update_state(self):
        self.counter = (self.counter + 1) % (5*4*3) # Mod is Lowest Common Multiple of possible update frequencies (1 to 5)

    def collision_check(self):
        """check collision with any living enemy"""
        alive_enemies = [e for e in self.enemies if e['alive']]
        enemy_positions = [(e['x'], e['y']) for e in alive_enemies]
    
        self.debug_message(f"{enemy_positions=}", line=7)
        self.debug_message(f"player position: ({self.player_x=}, {self.player_y=})", line=8)

        for enemy in alive_enemies:
            if enemy['x'] == self.player_x and enemy['y'] == self.player_y:
                self.running = False
                break

    def run(self):
        """game loop"""
        while self.running:
            self.stdscr.clear() 

            self.draw_border()
            self.draw_player()
            self.draw_enemies() 
            
            # Update game state
            # question: why is there blinking for debug messages in these methods? 
            self.update_enemies() 
            self.handle_input()
            self.collision_check()
            self.update_state()

            self.debug_message(f"{self.game_width=} x {self.game_height=}", line=12)
            self.debug_message(f"{self.counter=}", line=13)
            self.debug_message(f"{self.update_freq=}", line=14)
            
            # screen refresh
            self.stdscr.refresh()
            
            # slow frame rate for consistent animation clock tick and retro feel
            time.sleep(0.2)

def main():
    """
    Initialize curses, start the game, and clean-up curses afterwards.
    The clean-up restores the terminal to the normal state in event of crash or Ctrl + C exit.
    """
        
    try:
        # init curses returns the standard screen
        stdscr = curses.initscr()

        game = SpaceInvaders(stdscr, debug=True)
        game.run()

    # no error message when Ctrl + C to quit (and curses clean-up still happens)
    except KeyboardInterrupt:
        pass
    finally: # finally ensures curses.endwin() runs, even if our program crashes or is exited through ctrl + c
        # clean-up curses
        # exiting without calling curses.endwin() will mess up your terminal and you'll need to quit it
        curses.endwin()

if __name__ == "__main__":
    main()
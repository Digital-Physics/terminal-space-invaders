import curses # based on ncurses in C; handles text-based UIs that run in terminal
import time

class SpaceInvaders:
    def __init__(self, stdscr, debug):
        self.stdscr = stdscr # stdscr is 'standard screen' in C
        self.height, self.width = stdscr.getmaxyx() # number of rows and columns
        self.debug = debug
        self.counter = 0
        self.update_freq = 5 # 5 is slow; enemy position is updated every 5 clock ticks to start
        
        # game area dimensions
        self.game_width = 20 
        self.game_height = 16

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
        stdscr.timeout(100)    # 100ms timeout for input (comment out to step through on input)
        self.stdscr.nodelay(True) # getch() will be non-blocking and return immediately

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
        for enemy in self.enemies:
            if enemy['alive']:
                # if somehow the player avoided the enemies but they got to the bottom anyway, end the game
                self.debug_message(f"{enemy['y']=}, {self.game_height=}", line=2)
                if enemy['y'] > self.game_height: 
                    self.running = False
                    break  

                self.stdscr.addch(self.start_y + enemy['y'], self.start_x + enemy['x'], '👾')
    
    def check_enemies(self):
        """check if any enemies are alive, and if not, show the end screen"""     
        # end screen check 
        # for enemy in self.enemies:
        #     enemy['alive'] = False 

        if not any(enemy['alive'] for enemy in self.enemies):
            mid_screen_y = self.start_y + self.game_height // 2
            mid_screen_x = self.start_x + self.game_width // 2
            self.stdscr.addstr(mid_screen_y, mid_screen_x, '🤖')
            
    def update_enemies(self):
        """move all enemies"""
        if self.counter % self.update_freq == 0:  # Move every n frames for slower movement
            # Check if we need to change direction
            if any(enemy['alive'] for enemy in self.enemies):
                leftmost = min(enemy['x'] for enemy in self.enemies if enemy['alive']) 
                rightmost = max(enemy['x'] for enemy in self.enemies if enemy['alive'])
                
                if self.enemy_direction == "right" and rightmost >= self.game_width - 2:
                    # Hit right wall - change direction, move down, speed up
                    self.enemy_direction = "left"
                    for enemy in self.enemies:
                        if enemy['alive']:
                            enemy['y'] += 1
                    self.update_freq = max(self.update_freq - 1, 1)
                elif self.enemy_direction == "left" and leftmost <= 1:
                    # Hit left wall - change direction, move down, speed up
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

        # 'esc' (ASCII value is 27) or 'q' to quit
        if key == 27 or key == ord('q'): 
            self.running = False
        elif key == curses.KEY_LEFT:
            if self.player_x > 1:
                self.player_x -= 1
        elif key == curses.KEY_RIGHT:
            if self.player_x < self.game_width - 1:
                self.player_x += 1
    
    def update_state(self):
        """state is only referenced for enemy speed at this point"""
        self.counter = (self.counter + 1) % (5*4*3) # Mod is Lowest Common Multiple of each possible update frequency (1 to 5)

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
            
            # Update game state
            self.update_state()
            self.handle_input()
            self.update_enemies() 
            self.collision_check()

            self.check_enemies() # show end screen if no enemies

            self.draw_border()
            self.draw_player()
            self.draw_enemies() 

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

        game = SpaceInvaders(stdscr, debug=False)

        if game.width < game.game_width or game.height < game.game_height:
            print("😵 make terminal window bigger")
            time.sleep(3)
        else:
            game.run()
    except KeyboardInterrupt:  # no error message when Ctrl + C to quit (and curses clean-up still happens)
        pass
    finally: # finally runs after program ends, program crashes, or it is interrupted and exited through Ctrl + c
        # clean-up curses
        # exiting without calling curses.endwin() will mess up your terminal and you'll need to quit it
        curses.endwin()

if __name__ == "__main__":
    main()
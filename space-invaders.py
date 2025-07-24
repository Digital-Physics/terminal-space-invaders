import curses # based on ncurses in C; handles text-based UIs that run in terminal
import time

class SpaceInvaders:
    def __init__(self, stdscr, debug):
        self.stdscr = stdscr # stdscr is 'standard screen' in C
        self.height, self.width = stdscr.getmaxyx() # number of rows and columns
        self.debug = debug
        
        self.screen_frame_offset = 2   # Cabinet frame (around the screen)
        self.cabinet_depth = 3 
        
        # game area dimensions
        self.game_width = 20 
        self.game_height = 16

        # upper left corner origin
        self.start_x = (self.width - self.game_width) // 2
        self.start_y = (self.height - self.game_height) // 2
        
        # Game states
        self.running = True
        self.game_over = False
        self.game_won = False
        
        # Setup curses 
        stdscr.keypad(True)    # Enable special keys (arrows, function keys, etc.)
        curses.curs_set(0)     # Hide cursor
        stdscr.timeout(100)    # 100ms timeout for input (comment out to step through on input)
        self.stdscr.nodelay(True) # getch() will be non-blocking and return immediately
        
        # Initialize game state
        self.reset_game()

    def reset_game(self):
        """Reset all game variables to initial state"""
        self.counter = 0
        self.update_freq = 5 # 5 is slow; enemy position is updated every 5 clock ticks to start
        
        # starting player position (middle bottom)
        self.player_x = self.game_width // 2
        self.player_y = self.game_height - 1
        
        # Initialize enemies; 2 rows of 3 enemies each
        self.enemies = []
        self.enemy_direction = "right"
        self.init_enemies()

        # bullets
        self.bullets = []
        
        # Reset game state flags
        self.game_over = False
        self.game_won = False

    def init_enemies(self):
        """Initialize a 2x3 grid of enemies"""
        self.enemies = []
        start_x = 3
        start_y = 2
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
        
    def add_char_safe(self, y, x, char):
        """Helper to safely add a character, checking bounds"""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.stdscr.addch(y, x, char)

    def add_string_safe(self, y, x, text):
        """Helper to safely add a string, checking bounds"""
        if 0 <= y < self.height and 0 <= x < self.width:
            if x + len(text) > self.width:
                text = text[:self.width - x]
            self.stdscr.addstr(y, x, text)

    def draw_border(self):
        # Original game area borders (screen)
        for x in range(self.game_width + 1):
            self.add_char_safe(self.start_y, self.start_x + x, '-')
            self.add_char_safe(self.start_y + self.game_height, self.start_x + x, '_')
        
        for y in range(self.game_height + 1):
            self.add_char_safe(self.start_y + y, self.start_x, '|')
            self.add_char_safe(self.start_y + y, self.start_x + self.game_width, '|')

        # Calculate key X coordinates
        cabinet_front_left_x = self.start_x - self.screen_frame_offset
        cabinet_front_right_x = self.start_x + self.game_width + self.screen_frame_offset
        right_depth_x = cabinet_front_right_x + self.cabinet_depth
        
        # top cabinet border to back edge
        for x in range(cabinet_front_left_x - 1, cabinet_front_right_x + 1):
            self.add_char_safe(self.start_y - self.screen_frame_offset - 1, x, '^')
        self.add_char_safe(self.start_y - self.screen_frame_offset - 1, cabinet_front_right_x + 2, '\\')
        self.add_string_safe(self.start_y - self.screen_frame_offset, cabinet_front_left_x + 5, 'Space Invaders 👾')
        self.add_string_safe(self.start_y - self.screen_frame_offset + 1, cabinet_front_left_x + 1, '=======================')

        # Left cabinet border (sides of the screen part)
        for y in range(self.start_y - self.screen_frame_offset - 1, self.start_y + self.game_height + self.screen_frame_offset + 1):
            self.add_char_safe(y, cabinet_front_left_x - 1, '*')
        
        # Right "depth" line of the cabinet (continuous vertical line)
        cabinet_total_height = (self.start_y - self.screen_frame_offset) + (self.game_height + 1) + (self.screen_frame_offset + 1) + 4 + 8 + 1 # Calculate total height based on elements
        for y in range(self.start_y - self.screen_frame_offset + 1, cabinet_total_height - 1): # Start 1 char down to allow for top slant
             self.add_char_safe(y, right_depth_x, '|') 

        # Slants connecting game screen to cabinet frame
        # Top-left slant
        self.add_char_safe(self.start_y, self.start_x, '\\')

        # Top-right slant (from game screen top right to cabinet top right front)
        self.add_char_safe(self.start_y, self.start_x + self.game_width, '/')

        # Bottom-left slant (from game screen bottom left to cabinet bottom left)
        self.add_char_safe(self.start_y + self.game_height + 1, self.start_x - 1, '/')
        self.add_char_safe(self.start_y + self.game_height + 2, self.start_x - 2, '/')

        # Bottom-right slant (from game screen bottom right to cabinet's right depth line)
        for i in range(self.cabinet_depth - 1): # Connect across the depth
            self.add_string_safe(self.start_y + self.game_height + self.screen_frame_offset - 1 + i, 
                               cabinet_front_right_x + i - 1, '\\')

        # Top perspective line of the cabinet from top-right front to top-right depth
        self.add_char_safe(self.start_y - self.screen_frame_offset, right_depth_x, '\\') # Top right corner of the cabinet

        # Vertical right of the screen
        for y in range(self.start_y - self.screen_frame_offset - 1, self.start_y + self.game_height + self.screen_frame_offset + 1):
            self.add_char_safe(y, cabinet_front_right_x + 1, '*')

        # Control Panel Front Top Edge
        control_panel_top_y = self.start_y + self.game_height + self.screen_frame_offset + 1
        for x in range(cabinet_front_left_x, cabinet_front_right_x + 1):
            self.add_char_safe(control_panel_top_y, x, '=')

        # Joystick
        self.add_string_safe(control_panel_top_y - 1, self.start_x + self.game_width // 2, '🕹️')

        # Control Panel Front Sides
        for y_offset in range(4): # Height of front control panel area
            self.add_char_safe(control_panel_top_y + y_offset, cabinet_front_left_x - 1, '[') # Left edge of front panel
            self.add_char_safe(control_panel_top_y + y_offset, cabinet_front_right_x + 1, ']') # Right edge of front panel

        # Bottom of control panel (front)
        control_panel_bottom_y = control_panel_top_y + 3
        for x in range(cabinet_front_left_x, cabinet_front_right_x + 1):
            self.add_char_safe(control_panel_bottom_y, x, '_')

        # Cabinet Body - Main front section
        body_top_y = control_panel_bottom_y + 1
        body_height = 8 # Height of the main body section

        for y in range(body_height):
            self.add_char_safe(body_top_y + y, cabinet_front_left_x, '|') # Left edge of front body
            self.add_char_safe(body_top_y + y, cabinet_front_right_x, '|') # Right edge of front body

        # Cabinet Base
        base_y = body_top_y + body_height
        
        # Front part of the base
        for x in range(cabinet_front_left_x, cabinet_front_right_x + 1):
            self.add_char_safe(base_y, x, '=') # Flat bottom front

        # Right side of the base (depth) - ensures it closes off neatly # Base slant to meet depth line
        self.add_char_safe(base_y - 1, cabinet_front_right_x + 2, '/') 
        self.add_char_safe(base_y, cabinet_front_right_x + 1, '/')

        # coin slots
        self.add_string_safe(control_panel_bottom_y + 3, self.start_x + self.game_width // 2 - 2, '|$|')
        self.add_string_safe(control_panel_bottom_y + 3, self.start_x + self.game_width // 2 + 2, '|$|')

    def draw_player(self):
        if not self.game_over:
            self.add_char_safe(self.start_y + self.player_y, self.start_x + self.player_x, '^')

    def draw_score(self):
        self.add_string_safe(self.start_y + 1, self.start_x + 2, str(6 - len([enemy for enemy in self.enemies if enemy['alive']])) + "/6")

    def draw_enemies(self):
        for enemy in self.enemies:
            if enemy['alive']:
                self.debug_message(f"{enemy['y']=}, {self.game_height=}", line=2)
                if enemy['y'] > self.game_height:
                    self.game_over = True
                    break
                # using 👾 sometimes leads to shifting of border so we use @ for enemy instead 
                self.add_string_safe(self.start_y + enemy['y'], self.start_x + enemy['x'], '@')
    
    def draw_bullets(self):
        if not self.game_over:
            for bullet in self.bullets:
                self.debug_message(f"{bullet['y']=}", line=3)
                self.add_char_safe(self.start_y + bullet['y'], self.start_x + bullet['x'], '•')
    
    def check_enemies(self):
        """check if any enemies are alive, and if not, show the end screen"""  
        if not any(enemy['alive'] for enemy in self.enemies):
            self.game_won = True
            
    def draw_game_over_screen(self):
        """Draw game over or victory screen with reset option"""
        mid_screen_y = self.start_y + self.game_height // 2
        mid_screen_x = self.start_x + self.game_width // 2
        
        if self.game_won:
            self.add_string_safe(mid_screen_y - 2, mid_screen_x - 4, 'YOU WON!')
            self.add_char_safe(mid_screen_y - 1, mid_screen_x, '🎉')
        else:
            self.add_string_safe(mid_screen_y - 2, mid_screen_x - 4, 'GAME OVER')
            self.add_char_safe(mid_screen_y - 1, mid_screen_x, '💀')
        
        self.add_string_safe(mid_screen_y + 1, mid_screen_x - 7, 'Press R to Reset')
        self.add_string_safe(mid_screen_y + 2, mid_screen_x - 6, 'Press Q to Quit')

    def update_enemies(self):
        """move all enemies"""
        if not self.game_over and self.counter % self.update_freq == 0:
            if any(enemy['alive'] for enemy in self.enemies):
                leftmost = min(enemy['x'] for enemy in self.enemies if enemy['alive']) 
                rightmost = max(enemy['x'] for enemy in self.enemies if enemy['alive'])
                
                if self.enemy_direction == "right" and rightmost >= self.game_width - 2:
                    self.enemy_direction = "left"
                    for enemy in self.enemies:
                        if enemy['alive']:
                            enemy['y'] += 1
                    self.update_freq = max(self.update_freq - 1, 1)
                elif self.enemy_direction == "left" and leftmost <= 1:
                    self.enemy_direction = "right"
                    for enemy in self.enemies:
                        if enemy['alive']:
                            enemy['y'] += 1
                    self.update_freq = max(self.update_freq - 1, 1)
                else:
                    move_amount = 1 if self.enemy_direction == "right" else -1
                    for enemy in self.enemies:
                        if enemy['alive']:
                            enemy['x'] += move_amount
    
    def update_bullets(self):
        """move all bullets up one and discard ones that have gone past the top edge of the screen"""
        if not self.game_over:
            remove_bullets = []

            for i, bullet in enumerate(self.bullets):
                bullet['y'] -= 1
                if bullet['y'] < 1:
                    remove_bullets.append(i)
            
            self.bullets = [bullet for i, bullet in enumerate(self.bullets) if i not in remove_bullets]

    def handle_input(self):
        key = self.stdscr.getch()
        self.debug_message(f"input key: {key}", line=0)

        if key == 27 or key == ord('q'):
            self.running = False
        elif self.game_over or self.game_won:
            # Handle game over/won state input
            if key == ord('r') or key == ord('R'):
                self.reset_game()
        else:
            # Handle normal gameplay input
            if key == curses.KEY_LEFT:
                if self.player_x > 1:
                    self.player_x -= 1
            elif key == curses.KEY_RIGHT:
                if self.player_x < self.game_width - 1:
                    self.player_x += 1
            elif key == ord(' '):
                self.bullets.append({"y": self.player_y, "x": self.player_x})
    
    def update_state(self):
        """state is only referenced for enemy speed at this point"""
        if not self.game_over:
            self.counter = (self.counter + 1) % (5*4*3)

    def collision_check_enemy(self):
        """check collision with any living enemy"""
        if not self.game_over:
            alive_enemies = [e for e in self.enemies if e['alive']]
            enemy_positions = [(e['x'], e['y']) for e in alive_enemies]
        
            self.debug_message(f"{enemy_positions=}", line=7)
            self.debug_message(f"player position: ({self.player_x=}, {self.player_y=})", line=8)

            for enemy in alive_enemies:
                if enemy['x'] == self.player_x and enemy['y'] == self.player_y:
                    self.game_over = True
                    break
    
    def collision_check_bullet(self):
        """check bullet-enemy collision"""
        if not self.game_over:
            remove_bullets = []

            self.debug_message(f"{self.bullets=}", line=8)

            # can we speed this nested for loop up if we sort x and y positions?
            for enemy in self.enemies:
                for i, bullet in enumerate(self.bullets):
                    if enemy['alive'] and bullet["x"] == enemy['x'] and bullet["y"] == enemy['y']:
                        remove_bullets.append(i)
                        enemy['alive'] = False

            self.bullets = [bullet for i, bullet in enumerate(self.bullets) if i not in remove_bullets]

    def run(self):
        """game loop"""
        while self.running:
            self.stdscr.clear() 
            
            self.update_state()
            self.handle_input()
            
            if not (self.game_over or self.game_won):
                self.update_enemies() 
                self.update_bullets()
                self.collision_check_enemy()
                self.collision_check_bullet()
                self.check_enemies()

            self.draw_border()
            
            if self.game_over or self.game_won:
                self.draw_game_over_screen()
            else:
                self.draw_player()
                self.draw_enemies() 
                self.draw_bullets()
                self.draw_score()

            self.debug_message(f"{self.game_width=} x {self.game_height=}", line=12)
            self.debug_message(f"{self.counter=}", line=13)
            self.debug_message(f"{self.update_freq=}", line=14)
            self.debug_message(f"game_over={self.game_over}, game_won={self.game_won}", line=15)
            
            self.stdscr.refresh()
            curses.flushinp()  # This flushes the input buffer
            time.sleep(0.2)

def main():
    """
    Initialize curses, start the game, and clean-up curses afterwards.
    The clean-up restores the terminal to the normal state in event of crash or Ctrl + C exit.
    """
    try:
        stdscr = curses.initscr()
        game = SpaceInvaders(stdscr, debug=False)
        
        # Calculate required dimensions
        required_width = game.start_x + game.game_width + game.screen_frame_offset + game.cabinet_depth + 10
        required_height = game.start_y + game.game_height + game.screen_frame_offset + 10

        if game.width < required_width or game.height < required_height:
            print(f"👾 Make terminal window bigger. Minimum size: {required_height}x{required_width}. Your window is {game.height}x{game.width}.")
            time.sleep(3)
        else:
            game.run()
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()

if __name__ == "__main__":
    main()
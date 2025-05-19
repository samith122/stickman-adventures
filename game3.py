import pygame, sys, random, math
from pygame import mixer

# Initialize pygame and mixer
pygame.init()
mixer.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Stick Man Adventures")
clock = pygame.time.Clock()

# Load sounds
try:
    jump_sound = mixer.Sound("jump.wav")
    death_sound = mixer.Sound("death.wav")
    victory_sound = mixer.Sound("victory.wav")
except:
    jump_sound = mixer.Sound(buffer=bytearray([128]*1000))
    death_sound = mixer.Sound(buffer=bytearray([0, 255]*500))
    victory_sound = mixer.Sound(buffer=bytearray([64, 128, 192, 255]*250))

# Game states
MENU, PLAYING, GAME_OVER, LEVEL_COMPLETE = 0, 1, 2, 3
game_state = MENU
level_index = 0
colors = {
    'WHITE': (255,255,255), 'BLACK': (0,0,0), 'BLUE': (0,0,255),
    'GREEN': (0,128,0), 'DARK_GREEN': (0,100,0), 'BROWN': (139,69,19),
    'SKY_BLUE': (135,206,235), 'CLOUD_WHITE': (240,240,240), 'RED': (255,0,0),
    'GOLD': (255,215,0), 'DOOR_BROWN': (101, 67, 33)
}

# Load background image (fallback if not found)
try:
    bg_image = pygame.image.load("background.png").convert()
    bg_image = pygame.transform.scale(bg_image, (800, 600))
except:
    bg_image = pygame.Surface((800, 600))
    for y in range(600):
        r,g,b = 135+100*y//600, 206+39*y//600, 235+20*y//600
        pygame.draw.line(bg_image, (r,g,b), (0,y), (800,y))

# Create realistic door surface
def create_door():
    door = pygame.Surface((120, 80), pygame.SRCALPHA)
    pygame.draw.rect(door, colors['DOOR_BROWN'], (0, 0, 120, 80), border_radius=5)
    for i in range(4):
        pygame.draw.rect(door, (colors['DOOR_BROWN'][0]-20, colors['DOOR_BROWN'][1]-10, colors['DOOR_BROWN'][2]-5),
                        (10, 10+i*18, 100, 15))
    pygame.draw.circle(door, colors['GOLD'], (100, 40), 5)
    pygame.draw.circle(door, (colors['GOLD'][0]//2, colors['GOLD'][1]//2, colors['GOLD'][2]//2), (100, 40), 3)
    return door

door_img = create_door()

player = {
    'x': 100, 'y': 510, 'vel_x': 0, 'vel_y': 0,
    'w': 20, 'h': 40, 'speed': 5, 'jump_power': 13,  # Increased jump power
    'facing': 1,
    'leg_angle': 0, 'leg_speed': 0.2,
    'arm_angle': 0, 'arm_speed': 0.15,
    'jump_cooldown': 0
}

gravity = 0.7
camera_offset = 0
on_ground = False

levels = [
    {   # Level 1
        'platforms': [
            {'x': 0, 'y': 550, 'w': 800, 'h': 50},
            {'x': 100, 'y': 420, 'w': 200, 'h': 20},
            {'x': 350, 'y': 340, 'w': 200, 'h': 20},
            {'x': 150, 'y': 260, 'w': 200, 'h': 20},
            {'x': 400, 'y': 180, 'w': 200, 'h': 20},
            {'x': 200, 'y': 100, 'w': 200, 'h': 20},
            {'x': 450, 'y': 20, 'w': 200, 'h': 20}
        ],
        'obstacles': [
            {'x': 300, 'y': 390, 'w': 30, 'h': 30},
            {'x': 200, 'y': 230, 'w': 30, 'h': 30}
        ],
        'exit': {'x': 450, 'y': 20, 'w': 120, 'h': 80}
    },
    {   # Level 2
        'platforms': [
            {'x': 0, 'y': 550, 'w': 800, 'h': 50},
            {'x': 200, 'y': 400, 'w': 150, 'h': 20},
            {'x': 400, 'y': 300, 'w': 150, 'h': 20},
            {'x': 600, 'y': 200, 'w': 150, 'h': 20},
            {'x': 300, 'y': 100, 'w': 200, 'h': 20}
        ],
        'obstacles': [
            {'x': 250, 'y': 370, 'w': 30, 'h': 30},
            {'x': 450, 'y': 270, 'w': 30, 'h': 30}
        ],
        'exit': {'x': 300, 'y': 100, 'w': 120, 'h': 80}
    },
    {   # Level 3
        'platforms': [
            {'x': 0, 'y': 550, 'w': 800, 'h': 50},
            {'x': 100, 'y': 450, 'w': 200, 'h': 20},
            {'x': 500, 'y': 350, 'w': 200, 'h': 20},
            {'x': 300, 'y': 250, 'w': 150, 'h': 20},
            {'x': 100, 'y': 150, 'w': 150, 'h': 20},
            {'x': 500, 'y': 60, 'w': 150, 'h': 20}
        ],
        'obstacles': [
            {'x': 150, 'y': 420, 'w': 30, 'h': 30},
            {'x': 520, 'y': 320, 'w': 30, 'h': 30},
            {'x': 120, 'y': 120, 'w': 30, 'h': 30}
        ],
        'exit': {'x': 500, 'y': 60, 'w': 120, 'h': 80}
    }
]

clouds = [[random.randint(0,800), random.randint(50,150), random.uniform(0.5,1.5), random.randint(30,60)] for _ in range(5)]

def reset_game():
    global player, camera_offset, on_ground
    player.update({
        'x': 100, 'y': 510, 'vel_x': 0, 'vel_y': 0,
        'facing': 1, 'leg_angle': 0, 'arm_angle': 0,
        'jump_cooldown': 0
    })
    camera_offset = 0
    on_ground = False

def draw_text(text, size, color, y_offset):
    font = pygame.font.SysFont("Arial", size, bold=True)
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, (400 - text_surf.get_width()//2, y_offset))

def draw_menu():
    screen.blit(bg_image, (0, 0))
    draw_text("Stick Man Adventures", 64, colors['BLACK'], 150)
    draw_text("Press SPACE to start", 36, colors['BLACK'], 300)

def draw_game_over():
    screen.blit(bg_image, (0, 0))
    draw_text("Game Over", 64, colors['RED'], 150)
    draw_text("Press SPACE to try again", 36, colors['BLACK'], 300)

def draw_level_complete():
    screen.blit(bg_image, (0, 0))
    draw_text("Level Complete!", 64, colors['GOLD'], 150)
    draw_text("Press SPACE for next level", 36, colors['BLACK'], 300)

def draw_stick_man(x, y, facing, leg_angle, arm_angle, camera_offset):
    pygame.draw.circle(screen, colors['BLACK'], (x + 10, y + 10 + camera_offset), 10)
    body_end_y = y + 40 + camera_offset
    pygame.draw.line(screen, colors['BLACK'], (x + 10, y + 20 + camera_offset), (x + 10, body_end_y), 2)
    arm_length = 15
    left_arm_x = x + 10 - arm_length * math.cos(arm_angle) * facing
    left_arm_y = y + 30 + camera_offset - arm_length * math.sin(arm_angle)
    right_arm_x = x + 10 + arm_length * math.cos(arm_angle) * facing
    right_arm_y = y + 30 + camera_offset + arm_length * math.sin(arm_angle)
    pygame.draw.line(screen, colors['BLACK'], (x + 10, y + 30 + camera_offset), (left_arm_x, left_arm_y), 2)
    pygame.draw.line(screen, colors['BLACK'], (x + 10, y + 30 + camera_offset), (right_arm_x, right_arm_y), 2)
    leg_length = 20
    left_leg_x = x + 10 - leg_length * math.sin(leg_angle) * facing
    left_leg_y = body_end_y + leg_length * math.cos(leg_angle)
    right_leg_x = x + 10 + leg_length * math.sin(leg_angle) * facing
    right_leg_y = body_end_y + leg_length * math.cos(leg_angle)
    pygame.draw.line(screen, colors['BLACK'], (x + 10, body_end_y), (left_leg_x, left_leg_y), 2)
    pygame.draw.line(screen, colors['BLACK'], (x + 10, body_end_y), (right_leg_x, right_leg_y), 2)

running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if game_state == MENU:
                reset_game()
                game_state = PLAYING
                level_index = 0
            elif game_state == GAME_OVER:
                reset_game()
                game_state = PLAYING
            elif game_state == LEVEL_COMPLETE:
                level_index += 1
                if level_index >= len(levels):
                    level_index = 0
                reset_game()
                game_state = PLAYING
            elif game_state == PLAYING and on_ground and player['jump_cooldown'] <= 0:
                player['vel_y'] = -player['jump_power']
                on_ground = False
                player['jump_cooldown'] = 0.2
                jump_sound.play()

    if game_state == PLAYING:
        if player['jump_cooldown'] > 0:
            player['jump_cooldown'] -= dt
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        if move_left and not move_right:
            player['vel_x'] = -player['speed']
            player['facing'] = -1
            player['leg_angle'] += player['leg_speed']
            player['arm_angle'] += player['arm_speed']
        elif move_right and not move_left:
            player['vel_x'] = player['speed']
            player['facing'] = 1
            player['leg_angle'] += player['leg_speed']
            player['arm_angle'] += player['arm_speed']
        else:
            player['vel_x'] = 0
            player['leg_angle'] *= 0.9
            player['arm_angle'] *= 0.9
        player['vel_y'] += gravity
        player['y'] += player['vel_y']
        player['x'] = max(0, min(780, player['x'] + player['vel_x']))
        on_ground = False
        for p in levels[level_index]['platforms']:
            if (player['x'] + player['w'] > p['x'] and player['x'] < p['x'] + p['w'] and
                player['y'] + player['h'] >= p['y'] and player['y'] + player['h'] <= p['y'] + 20):
                player['y'] = p['y'] - player['h']
                player['vel_y'] = 0
                on_ground = True
        for o in levels[level_index]['obstacles']:
            if (player['x'] + player['w'] > o['x'] and player['x'] < o['x'] + o['w'] and
                player['y'] + player['h'] > o['y'] and player['y'] < o['y'] + o['h']):
                game_state = GAME_OVER
                death_sound.play()
        exit_rect = levels[level_index]['exit']
        if (player['x'] + player['w'] > exit_rect['x'] and player['x'] < exit_rect['x'] + exit_rect['w'] and
            player['y'] + player['h'] > exit_rect['y'] and player['y'] < exit_rect['y'] + exit_rect['h']):
            game_state = LEVEL_COMPLETE
            victory_sound.play()
        camera_offset = max(0, 300 - player['y'])

    if game_state == MENU:
        draw_menu()
    elif game_state == GAME_OVER:
        draw_game_over()
    elif game_state == LEVEL_COMPLETE:
        draw_level_complete()
    else:
        screen.blit(bg_image, (0, 0))
        for c in clouds:
            pygame.draw.circle(screen, colors['CLOUD_WHITE'], (int(c[0]), int(c[1]+camera_offset*0.5)), c[3])
            pygame.draw.circle(screen, colors['CLOUD_WHITE'], (int(c[0]+c[3]*0.7), int(c[1]+camera_offset*0.5)), int(c[3]*0.8))
            pygame.draw.circle(screen, colors['CLOUD_WHITE'], (int(c[0]-c[3]*0.5), int(c[1]+camera_offset*0.5)), int(c[3]*0.6))
            c[0] -= c[2]
            if c[0] < -c[3]*2:
                c[0:2] = [800+random.randint(100,200), random.randint(50,150)]
        for p in levels[level_index]['platforms']:
            pygame.draw.rect(screen, colors['GREEN'], (p['x'], p['y']+camera_offset, p['w'], p['h']))
        for o in levels[level_index]['obstacles']:
            pygame.draw.rect(screen, colors['RED'], (o['x'], o['y']+camera_offset, o['w'], o['h']))
        exit_rect = levels[level_index]['exit']
        screen.blit(door_img, (exit_rect['x'], exit_rect['y']+camera_offset))
        draw_stick_man(
            player['x'], player['y'],
            player['facing'], player['leg_angle'],
            player['arm_angle'], camera_offset
        )

    pygame.display.flip()

pygame.quit()
sys.exit()

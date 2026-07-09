from raylib import *

SCREEN_W = 800
SCREEN_H = 600

PADDLE_W = 100
PADDLE_H = 12
PADDLE_Y = SCREEN_H - 40
BALL_R = 7
BALL_SPEED = 350.0

ROWS = 6
COLS = 10
BRICK_W = 68
BRICK_H = 20
BRICK_GAP = 4
BG_COLOR = [26, 26, 46, 255]
ROW_COLORS = [MAROON, BROWN, GOLD, DARKGREEN, DARKBLUE, DARKPURPLE]
PADDLE_COLOR = LIGHTGRAY
BALL_COLOR = LIGHTGRAY
UI_COLOR = GRAY

paddle_x = 0
ball_x = 0.0
ball_y = 0.0
ball_vx = 0.0
ball_vy = 0.0
score = 0
lives = 0
bricks = []
game_state = 0


def make_bricks():
    result = []
    x0 = (SCREEN_W - COLS * (BRICK_W + BRICK_GAP) + BRICK_GAP) / 2
    for r in range(ROWS):
        for c in range(COLS):
            x = x0 + c * (BRICK_W + BRICK_GAP)
            y = 50 + r * (BRICK_H + BRICK_GAP)
            result.append([x, y, True, r])
    return result


def reset_ball():
    global ball_x, ball_y, ball_vx, ball_vy
    ball_x = SCREEN_W / 2.0
    ball_y = SCREEN_H * 0.65
    ball_vx = BALL_SPEED * 0.6
    ball_vy = -BALL_SPEED * 0.8


def reset_game():
    global paddle_x, score, lives, bricks, game_state
    paddle_x = (SCREEN_W - PADDLE_W) // 2
    score = 0
    lives = 3
    bricks = make_bricks()
    game_state = 0
    reset_ball()


reset_game()
InitWindow(SCREEN_W, SCREEN_H, b"Breakout")

while not WindowShouldClose():
    dt = GetFrameTime()
    if dt > 0.05:
        dt = 0.05

    if game_state == 0:
        paddle_x = GetMouseX() - PADDLE_W // 2
        if paddle_x < 0:
            paddle_x = 0
        if paddle_x > SCREEN_W - PADDLE_W:
            paddle_x = SCREEN_W - PADDLE_W

        ball_x += ball_vx * dt
        ball_y += ball_vy * dt

        if ball_x - BALL_R < 0:
            ball_x = float(BALL_R)
            ball_vx = abs(ball_vx)
        if ball_x + BALL_R > SCREEN_W:
            ball_x = float(SCREEN_W - BALL_R)
            ball_vx = -abs(ball_vx)
        if ball_y - BALL_R < 0:
            ball_y = float(BALL_R)
            ball_vy = abs(ball_vy)

        if ball_y > SCREEN_H + BALL_R:
            lives -= 1
            if lives <= 0:
                game_state = 2
            else:
                reset_ball()

        if (ball_vy > 0
                and paddle_x - BALL_R < ball_x < paddle_x + PADDLE_W + BALL_R
                and PADDLE_Y <= ball_y + BALL_R <= PADDLE_Y + PADDLE_H + 8):
            ratio = (ball_x - paddle_x) / PADDLE_W
            ratio = max(-0.92, min(0.92, (ratio - 0.5) * 1.6))
            ball_vx = BALL_SPEED * ratio
            ball_vy = -(BALL_SPEED ** 2 - ball_vx ** 2) ** 0.5
            ball_y = float(PADDLE_Y - BALL_R)

        for b in bricks:
            if not b[2]:
                continue
            bx, by = b[0], b[1]
            if (ball_x + BALL_R > bx
                    and ball_x - BALL_R < bx + BRICK_W
                    and ball_y + BALL_R > by
                    and ball_y - BALL_R < by + BRICK_H):
                b[2] = False
                score += 10
                dx = min(ball_x + BALL_R - bx, bx + BRICK_W - ball_x + BALL_R)
                dy = min(ball_y + BALL_R - by, by + BRICK_H - ball_y + BALL_R)
                if dx < dy:
                    ball_vx = -ball_vx
                else:
                    ball_vy = -ball_vy
                break

        if all(not b[2] for b in bricks):
            game_state = 1

    elif IsKeyPressed(KEY_R):
        reset_game()

    BeginDrawing()
    ClearBackground(BG_COLOR)

    for b in bricks:
        if b[2]:
            DrawRectangle(int(b[0]), int(b[1]), BRICK_W, BRICK_H, ROW_COLORS[b[3]])

    DrawRectangle(paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H, PADDLE_COLOR)
    DrawCircle(int(ball_x), int(ball_y), BALL_R, BALL_COLOR)

    DrawText(str(score).encode(), 10, 10, 20, UI_COLOR)
    for i in range(lives):
        DrawCircle(SCREEN_W - 20 - i * 25, 20, 8, MAROON)

    if game_state == 1:
        t = b"YOU WIN!"
        DrawText(t, (SCREEN_W - MeasureText(t, 40)) // 2, 270, 40, GREEN)
        t = b"Press R to play again"
        DrawText(t, (SCREEN_W - MeasureText(t, 20)) // 2, 320, 20, UI_COLOR)
    elif game_state == 2:
        t = b"GAME OVER"
        DrawText(t, (SCREEN_W - MeasureText(t, 40)) // 2, 270, 40, MAROON)
        t = b"Press R to play again"
        DrawText(t, (SCREEN_W - MeasureText(t, 20)) // 2, 320, 20, UI_COLOR)

    EndDrawing()

CloseWindow()

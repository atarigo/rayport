from raylib import *

frame = 0
InitWindow(800, 450, b"rayport test")
while not WindowShouldClose():
    frame += 1
    x = int(frame % 700)
    BeginDrawing()
    ClearBackground(RAYWHITE)
    DrawRectangle(x, 200, 60, 60, RED)
    DrawText(b"Hello from rayport!", 100, 100, 40, DARKGRAY)
    DrawText(str(frame).encode(), 10, 10, 20, GRAY)
    EndDrawing()
CloseWindow()

from raylib import *
InitWindow(800, 450, b"rayport test")
while not WindowShouldClose():
    BeginDrawing()
    ClearBackground(RAYWHITE)
    DrawText(b"Hello from rayport!", 100, 200, 40, RED)
    EndDrawing()
CloseWindow()

import sys, os, runpy
game_dir = "/usr/local/game"
os.chdir(game_dir)
sys.path.insert(0, game_dir)
runpy.run_path("main.py", run_name="__main__")

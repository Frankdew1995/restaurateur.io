from app import app
from pyfladesk import init_gui
from pathlib import Path

icon = str(Path(app.root_path) / 'static' / 'img' / 'logo.png')

if __name__ == "__main__":

    init_gui(app, port=5000, width=1000, height=500,
             window_title="Xstar Gastronomy Application", icon=icon)


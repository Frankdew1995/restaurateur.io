from app import app
from pyfladesk import init_gui
from pathlib import Path

icon = str(Path(app.root_path) / 'static' / 'img' / 'logo.ico')

if __name__ == "__main__":

    app.run(port=5000)
    # init_gui(app, port=8080, width=1000,
    #          height=500, window_title="Xstar Gastronomy Application", icon=icon)


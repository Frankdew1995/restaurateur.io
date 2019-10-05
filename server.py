from app import app
from pyfladesk import init_gui
from pathlib import Path
from app.utilities import start_ngrok

icon = str(Path(app.root_path) / 'static' / 'img' / 'swiftify_logo.png')

if __name__ == "__main__":

    # try:
    #     start_ngrok(port=5000)
    # except Exception as e:
    #     print(str(e))

    app.run(port=5000)
    # init_gui(app,
    #          port=5000,
    #          width=1000,
    #          height=500,
    #          window_title="Swiftify Gastronomy Application",
    #          icon=icon)


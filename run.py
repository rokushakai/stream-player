import os

# Add project directory to PATH so python-mpv can find libmpv-2.dll
os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ["PATH"]

from src.app import App

if __name__ == "__main__":
    app = App()
    app.run()

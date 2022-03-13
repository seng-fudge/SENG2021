import config
import enviro # pylint: disable=import-error
from app import init_app, email
from flask import Flask
import signal

def graceful_exit(*args):
    email.exit()
    exit(0)

app = init_app()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_exit)
    app.run(port = config.port, debug = True)
#!/bin/bash


cd /var/www/contingent

VENV_DIR="/var/www/contingent/.venv"

source "$VENV_DIR/bin/activate"

waitress-serve --listen localhost:5000 run:app

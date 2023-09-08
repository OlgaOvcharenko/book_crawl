#!/bin/bash

if [[ ! -d "python_env" ]]; then
  echo "Create Python Virtual Environment on $HOSTNAME"

  python3 -m venv python_venv

  source "python_venv/bin/activate"
  pip3 install -r requirements.txt
fi

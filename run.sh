# Setup virt. env. and requirements if not already
./setup_venv.sh
source "python_venv/bin/activate"
pip install --upgrade pip
mkdir -p embeddings

# Run actual script
python rest.py

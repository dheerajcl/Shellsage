# Create virtual environment
python3 -m venv error_assist_env
source error_assist_env/bin/activate

# Install dependencies
pip install requests click

# Install package in editable mode
pip install -e .

# Set Hyperbolic API key
export HYPERBOLIC_API_KEY='your_actual_api_key'
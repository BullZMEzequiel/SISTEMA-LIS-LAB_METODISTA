import sys
from pathlib import Path

# Agregar el directorio raíz del backend al path de Python
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))
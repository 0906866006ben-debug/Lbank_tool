import os
import sys
from pathlib import Path

# Ensure `import app...` works when running pytest from anywhere.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Force mock mode + in-memory-ish test DB for the whole suite.
os.environ.setdefault("LBANK_WIDGET_MOCK_MODE", "true")
os.environ.setdefault("LBANK_DB_URL", "sqlite:///./test_lbank_widget.db")

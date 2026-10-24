import sys
from pathlib import Path
BASE = Path(r'C:\Users\DIANA\bot-minecraft')
sys.path.insert(0, str(BASE))
import main as m
from auth import API_KEY
print('API_KEY set:', bool(API_KEY))
print('ROUTES:')
for r in m.app.routes:
    methods = getattr(r, 'methods', None)
    print(getattr(r, 'path', r), methods)

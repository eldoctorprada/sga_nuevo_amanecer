"""
WSGI entry point para Railway/Gunicorn
"""

import os
import sys

print("\n" + "="*70)
print("🔍 DIAGNOSTICO WSGI - INICIANDO")
print("="*70)
print(f"📌 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
print(f"📌 DATABASE_URL presente: {'✅ SÍ' if os.environ.get('DATABASE_URL') else '❌ NO'}")
print("="*70 + "\n")
sys.stdout.flush()

from app import create_app
from models import db

app = create_app('production')

try:
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada exitosamente")
except Exception as e:
    print(f"❌ Error al inicializar base de datos: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

if __name__ == '__main__':
    app.run()
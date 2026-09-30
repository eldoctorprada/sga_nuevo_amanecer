"""
WSGI entry point para Railway/Gunicorn
Este archivo es el punto de entrada que Gunicorn debe usar.
NO inicializa la base de datos - eso se hace en app.py durante desarrollo.
"""

import os
import sys

# Diagnóstico al iniciar
print("\n" + "="*70)
print("🔍 DIAGNOSTICO WSGI - INICIANDO")
print("="*70)
print(f"📌 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'production')}")
print(f"📌 DATABASE_URL presente: {'✅ SÍ' if os.environ.get('DATABASE_URL') else '❌ NO'}")
if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    masked_url = db_url[:20] + '***' + db_url[-30:] if len(db_url) > 50 else '***'
    print(f"📌 DATABASE_URL (masked): {masked_url}")
print("="*70)
sys.stdout.flush()

# Importar la aplicación
print("\n🚀 Importando aplicación Flask...")
sys.stdout.flush()

try:
    from app import create_app
    app = create_app('production')
    print("✅ Aplicación cargada exitosamente")
except Exception as e:
    print(f"❌ ERROR al cargar la aplicación: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    raise

print("\n" + "="*70)
print("✅ WSGI LISTO - Gunicorn puede usar el app")
print("="*70 + "\n")
sys.stdout.flush()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
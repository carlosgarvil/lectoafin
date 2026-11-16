"""Bookcrush · punto de entrada de la aplicación.

Ejecutar en modo desarrollo:
    flask --app run run --debug
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

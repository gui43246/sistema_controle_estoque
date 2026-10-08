"""Inicializa e executa o servidor Flask da aplicação."""
from app import app

if __name__=="__main__":
    app.run(debug=True)
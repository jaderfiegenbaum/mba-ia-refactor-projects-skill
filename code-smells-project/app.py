from src.app import create_app
from src.config.settings import DEBUG, HOST, PORT

app = create_app()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)

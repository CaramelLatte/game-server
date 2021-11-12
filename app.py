from flask import Flask
from routes.minecraft import check, normalize, closeGame

app = Flask(__name__)

@app.route("/")
def startGame():
  normalize()
  return "<p>Starting game</p>"
@app.route("/close")
def close():
  returnval = closeGame()
  return returnval
@app.route("/check")
def check_status():
  returnval = check()
  return returnval



if __name__ == "__main__":
    from waitress import serve
    host = "0.0.0.0"
    port = 8080
    serve(app, host=host, port=port)
    print("Running server on ", host, port)
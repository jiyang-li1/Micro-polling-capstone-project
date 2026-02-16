from flask import Flask

app = Flask(__name__)


from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>Index Page</h1>
    <form method="post" action="/hello">
        <input type="text" name="go to hello" placeholder="enter something">
        <button type="submit">Continue</button>
    </form>
    '''
@app.route('/hello', methods=['POST']) 
def hello():
    return 'Hello, World'

if __name__ == '__main__':
    app.run(debug=True)
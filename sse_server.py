
import functools
from flask import Flask, render_template, request, redirect, url_for, session ,Response
import json
import time
import threading
import random
import queue

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' 
users = {"sami":"sami", "rami": "rami "} # simple user database
# global list of SSE connections for all useres
sse_connections = []


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


#runs in a background thread
# this will generate event that will send to all connection 
def generate_stock_data():
    """Simulate real-time stock price updates"""
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    while True:
        stock = random.choice(stocks)
        price = round(random.uniform(100, 500), 2)
        change = round(random.uniform(-5, 5), 2)
        data = {
            'symbol': stock,
            'price': price,
            'change': change,
            'timestamp': time.time()
        }
        send_sse_event('stock_update', data) # go to send the event to sse connections

        news_data = {
            'headline': f"{stock} hits {price}",
            'timestamp': time.time()
        }
        send_sse_event('news_update', news_data)
        time.sleep(2)


# Sending SSE events to all connected (subsicribe)clients
# this function will send the event to all active sse connection
def send_sse_event(event_type, data):
    event_data = f"data: {json.dumps(data)}\n\n"# format of sse event
    global sse_connections
    active_connections = []
    # So this is where all clients get the same update.
    for connection in sse_connections:
        try:
            #connection queue
            connection.put(event_data)
            active_connections.append(connection) # list of queues
            #active_connections is used to remove any dead/disconnected clients.
        except:
            pass
    sse_connections = active_connections


@app.route('/')
@login_required
def index():
    return render_template('trads.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username 
            return render_template('trads.html')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# this will create active connection in sse_connections
# and track events for each connection
@app.route('/events')
def events():
    """SSE endpoint"""
    def event_stream():
        # each client conected has queue 
        connection_queue = queue.Queue()# when dissconected the queue will removed 
        sse_connections.append(connection_queue)
        # add queue to global sse_connections
        try:
            while True:
                try:
                    data = connection_queue.get(timeout=30)#Remove and return an item from the queue
                    yield data
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            if connection_queue in sse_connections:
                sse_connections.remove(connection_queue)# remove queue when client disconnected

    return Response(event_stream(),
                    mimetype="text/event-stream",
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Access-Control-Allow-Origin': '*'
                    })

def start_background_tasks():
    stock_thread = threading.Thread(target=generate_stock_data, daemon=True)# thread work in the background 
    stock_thread.start()


if __name__ == "__main__":
    start_background_tasks()
    app.run(debug=True, threaded=True)


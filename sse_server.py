
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


sse_channels = {
    'stock_update': set(),
    'news_update': set()
}

message_history = {
    "stock_update": [],
    "news_update": []
}


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
        event_data = f"data: {json.dumps(data)}\n\n"#
        message_history['stock_update'].append(event_data)
        news_data = {
            'headline': f"{stock} hits {price}",
            'timestamp': time.time()
        }
        send_sse_event('news_update', news_data)
        event_data = f"data: {json.dumps(news_data)}\n\n"#
        message_history['news_update'].append(event_data)

        time.sleep(2)

def send_sse_event(channel, data):
    
    event_data = f"data: {json.dumps(data)}\n\n"#
    active_connections = []
    global sse_channels
    for q in list(sse_channels[channel]):
        try:
            q.put(event_data)
            

            active_connections.append(q)
        except:
            pass 
    sse_channels[channel] = active_connections

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
            return render_template('home.html')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


@app.route('/subscribe/<channel>')
def subscribe(channel):
    if channel not in sse_channels:
        return "Channel not found", 404

    def event_stream():
        q = queue.Queue()  # Each client gets its own queue
        sse_channels[channel].append(q)
        for msg in message_history[channel]:
            q.put(msg)
        try:
            while True:
                data = q.get()  # Wait for new events
                yield f"event: {channel}\ndata: {json.dumps(data)}\n\n"
        finally:
            sse_channels[channel].remove(q)

    return Response(event_stream(), mimetype='text/event-stream')
def start_background_tasks():
    stock_thread = threading.Thread(target=generate_stock_data, daemon=True)# thread work in the background 
    stock_thread.start()


if __name__ == "__main__":
    start_background_tasks()
    app.run(debug=True, threaded=True)


from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Database setup
def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (user_id INTEGER, contact_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (sender_id INTEGER, receiver_id INTEGER, message TEXT)''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username) VALUES (?)', (username,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'User added'})

@app.route('/find_user', methods=['GET'])
def find_user():
    username = request.args.get('username')
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({'status': 'User found', 'user': user})
    else:
        return jsonify({'status': 'User not found'})

@app.route('/add_contact', methods=['POST'])
def add_contact():
    user_id = request.form['user_id']
    contact_id = request.form['contact_id']
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)', (user_id, contact_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'Contact added'})

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message = data['message']
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)', (sender_id, receiver_id, message))
    conn.commit()
    conn.close()
    emit('receive_message', data, room=receiver_id)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('status', {'msg': username + ' has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('status', {'msg': username + ' has left the room.'}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
DB = 'connectit.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            area TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            price TEXT DEFAULT 'Free',
            organizer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Seed sample Mumbai events
    count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    if count == 0:
        sample_events = [
            ('Sunburn Arena ft. Martin Garrix', 'The biggest electronic music festival hits Mumbai with world-class DJs and an incredible stage production.', 'Music', 'MMRDA Grounds, BKC', 'Bandra-Kurla Complex', '2025-02-15', '6:00 PM', '₹2,500', 'Percept Live'),
            ('Kala Ghoda Arts Festival', 'Mumbai\'s iconic 9-day multicultural festival celebrating art, music, dance, theatre, cinema and literature.', 'Culture', 'Kala Ghoda, Fort', 'Fort', '2025-02-01', '11:00 AM', 'Free', 'Kala Ghoda Association'),
            ('IIT Bombay Techfest', 'Asia\'s largest science and technology festival with robotics, coding competitions, guest lectures and exhibitions.', 'Tech', 'IIT Bombay Campus, Powai', 'Powai', '2025-01-17', '9:00 AM', 'Free', 'IIT Bombay'),
            ('Mumbai Street Food Festival', 'Celebrate Mumbai\'s legendary street food culture — vada pav, pav bhaji, bhel puri and more from 100+ stalls.', 'Food', 'Juhu Beach', 'Juhu', '2025-02-22', '4:00 PM', '₹100', 'Mumbai Foodie Club'),
            ('Mood Indigo - IITB Culturals', 'Asia\'s largest college cultural festival with 500+ events, celebrity performances and competitions.', 'College Fest', 'IIT Bombay, Powai', 'Powai', '2025-12-20', '10:00 AM', 'Free', 'IIT Bombay Students'),
            ('Mumbai Marathon 2025', 'The iconic 42km full marathon through the streets of Mumbai — run past iconic landmarks like Marine Drive.', 'Sports', 'Azad Maidan, CST', 'Fort', '2025-01-19', '5:30 AM', '₹600', 'Procam International'),
            ('Bollywood Night - Live Orchestra', 'An evening of classic and modern Bollywood hits performed live by a 40-piece orchestra under the stars.', 'Music', 'Rang Sharda Auditorium, Bandra', 'Bandra', '2025-02-08', '7:30 PM', '₹800', 'Musik Events'),
            ('Versova Art Walk', 'Explore Versova\'s colourful street art and murals with a guided community walk and interaction with local artists.', 'Art', 'Versova Village, Andheri', 'Andheri', '2025-02-09', '9:00 AM', 'Free', 'Versova Residents Welfare'),
            ('Python & AI Workshop', 'Beginner-friendly 6-hour hands-on workshop on Python programming and Artificial Intelligence fundamentals.', 'Tech', 'VJTI Campus, Matunga', 'Matunga', '2025-02-16', '10:00 AM', '₹299', 'TechLearn Mumbai'),
            ('Farmers Market Bandra', 'Shop fresh organic produce, homemade food, handcrafted goods and sustainable products every Sunday.', 'Food', 'Mount Mary Steps, Bandra', 'Bandra', '2025-02-02', '9:00 AM', 'Free', 'Bandra Collective'),
            ('Kabaddi Premier League - Mumbai', 'Watch Mumbai\'s top kabaddi teams battle it out in this electrifying local league tournament.', 'Sports', 'Cooperage Ground, Churchgate', 'Churchgate', '2025-02-12', '5:00 PM', '₹200', 'Mumbai Kabaddi Association'),
            ('Ganesh Utsav Cultural Program', 'Traditional dance, music and drama performances celebrating Ganesh Chaturthi across multiple stages.', 'Culture', 'Lalbaug, Parel', 'Parel', '2025-09-02', '6:00 PM', 'Free', 'Lalbaug Mandal'),
        ]
        conn.executemany('''
            INSERT INTO events (title, description, category, location, area, date, time, price, organizer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_events)
    conn.commit()
    conn.close()

# ── Serve frontend ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── API Routes ──────────────────────────────────────────────────────────────
@app.route('/api/events', methods=['GET'])
def get_events():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    area = request.args.get('area', '')

    conn = get_db()
    query = 'SELECT * FROM events WHERE 1=1'
    params = []

    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)
    if search:
        query += ' AND (title LIKE ? OR description LIKE ? OR location LIKE ?)'
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if area and area != 'All':
        query += ' AND area = ?'
        params.append(area)

    query += ' ORDER BY date ASC'
    events = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(e) for e in events])

@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.json
    required = ['title', 'category', 'location', 'area', 'date']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    conn = get_db()
    conn.execute('''
        INSERT INTO events (title, description, category, location, area, date, time, price, organizer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'], data.get('description', ''), data['category'],
        data['location'], data['area'], data['date'],
        data.get('time', ''), data.get('price', 'Free'), data.get('organizer', '')
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event added successfully!'}), 201

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = get_db()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cats = conn.execute('SELECT DISTINCT category FROM events ORDER BY category').fetchall()
    conn.close()
    return jsonify(['All'] + [c['category'] for c in cats])

@app.route('/api/areas', methods=['GET'])
def get_areas():
    conn = get_db()
    areas = conn.execute('SELECT DISTINCT area FROM events ORDER BY area').fetchall()
    conn.close()
    return jsonify(['All'] + [a['area'] for a in areas])

if __name__ == '__main__':
    init_db()
    print("\n🚀 Connect_it is running!")
    print("👉 Open your browser and go to: http://localhost:5000\n")
    app.run(debug=True, port=5000)

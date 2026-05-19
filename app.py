import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sanat_galerisi_gizli_anahtar_burak'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, fullname TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, profile_image TEXT DEFAULT 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png', is_admin INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS artworks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, price REAL, image_path TEXT NOT NULL, category TEXT DEFAULT 'Genel', is_sold INTEGER DEFAULT 0, views INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, artwork_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (artwork_id) REFERENCES artworks (id) ON DELETE CASCADE, UNIQUE(user_id, artwork_id))''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, artwork_id INTEGER NOT NULL, comment_text TEXT NOT NULL, owner_reply TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (artwork_id) REFERENCES artworks (id) ON DELETE CASCADE)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS workshops (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, w_date TEXT NOT NULL, w_time TEXT NOT NULL, price REAL, capacity INTEGER, image_path TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, e_date TEXT NOT NULL, e_time TEXT NOT NULL, price REAL, capacity INTEGER, image_path TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, artwork_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (artwork_id) REFERENCES artworks (id) ON DELETE CASCADE, UNIQUE(user_id, artwork_id))''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_type TEXT NOT NULL, item_id INTEGER NOT NULL, tickets INTEGER NOT NULL, payment_status TEXT DEFAULT 'Ödenmedi', total_price REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, artwork_id INTEGER NOT NULL, price REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, FOREIGN KEY (artwork_id) REFERENCES artworks (id) ON DELETE CASCADE)''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_type TEXT NOT NULL, item_id INTEGER NOT NULL, review_text TEXT NOT NULL, event_rating INTEGER DEFAULT 0, owner_reply TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS comment_ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, comment_id INTEGER NOT NULL, rating INTEGER NOT NULL, UNIQUE(user_id, comment_id))''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS review_ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, review_id INTEGER NOT NULL, rating INTEGER NOT NULL, UNIQUE(user_id, review_id))''')
    
    c.execute(
        '''CREATE TABLE IF NOT EXISTS support_tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT NOT NULL, message TEXT NOT NULL, admin_reply TEXT, status TEXT DEFAULT 'Açık', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    
    c.execute(
        '''CREATE TABLE IF NOT EXISTS live_chat (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, message TEXT NOT NULL, is_from_admin INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS user_coupons (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, code TEXT NOT NULL, discount_rate REAL NOT NULL, is_used INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    
    c.execute(
        '''CREATE TABLE IF NOT EXISTS saved_comparisons (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, comp_type TEXT NOT NULL, item_ids TEXT NOT NULL, title TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')

    conn.commit()
    conn.close()


@app.route('/')
def login_page(): return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    conn = None
    try:
        is_admin = 1 if request.form.get('is_admin') == '1' else 0
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (fullname, email, password, is_admin) VALUES (?, ?, ?, ?)", (
        request.form['fullname'], request.form['email'], generate_password_hash(request.form['password']), is_admin))
        user_id = c.lastrowid
        
        if not is_admin:
            c.execute("INSERT INTO user_coupons (user_id, code, discount_rate) VALUES (?, ?, ?)", (user_id, 'HOSGELDIN20', 0.20))
            
        conn.commit()
    except sqlite3.IntegrityError:
        return "Bu e-posta zaten kayıtlı!"
    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"
    finally:
        if conn:
            conn.close()
    return redirect(url_for('login_page'))


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        conn = None
        try:
            conn = sqlite3.connect('users.db')
            conn.execute("INSERT INTO users (fullname, email, password, is_admin) VALUES (?, ?, ?, ?)", (
            request.form['fullname'], request.form['email'], generate_password_hash(request.form['password']), 1))
            conn.commit()
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError:
            return "Bu e-posta zaten kayıtlı!"
        except Exception as e:
            return f"Bir hata oluştu: {str(e)}"
        finally:
            if conn:
                conn.close()
    return render_template('admin_register.html')


@app.route('/login', methods=['POST'])
def login():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, password, is_admin FROM users WHERE email = ?", (request.form['email'],))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], request.form['password']):
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        return redirect(url_for('home'))
    return "Hatalı e-posta veya şifre!"


@app.route('/logout')
def logout(): session.pop('user_id', None); return redirect(url_for('login_page'))


@app.route('/home')
def home():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template('home.html')


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session: return jsonify({'success': False})
    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT profile_image FROM users WHERE id=?", (user_id,))
        img = c.fetchone()[0]
        file = request.files.get('profile_img')
        if file and file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}_{secure_filename(file.filename)}")
            file.save(filepath)
            img = '/' + filepath.replace('\\', '/')
        if request.form.get('password'):
            c.execute("UPDATE users SET fullname=?, email=?, password=?, profile_image=? WHERE id=?", (
            request.form.get('fullname'), request.form.get('email'),
            generate_password_hash(request.form.get('password')), img, user_id))
        else:
            c.execute("UPDATE users SET fullname=?, email=?, profile_image=? WHERE id=?",
                      (request.form.get('fullname'), request.form.get('email'), img, user_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Profil güncellendi!'})
    except:
        return jsonify({'success': False})
    finally:
        conn.close()


@app.route('/api/add_art', methods=['POST'])
def add_art():
    if 'user_id' not in session: return jsonify({'success': False})
    file = request.files.get('art_image')
    if not file: return jsonify({'success': False})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                            f"art_{session['user_id']}_{random.randint(1000, 9999)}_{secure_filename(file.filename)}")
    file.save(filepath)
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO artworks (user_id, title, description, price, image_path, category) VALUES (?, ?, ?, ?, ?, ?)", (
    session['user_id'], request.form.get('title'), request.form.get('desc'), request.form.get('price'),
    '/' + filepath.replace('\\', '/'), request.form.get('category', 'Genel')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/add_workshop', methods=['POST'])
def add_workshop():
    if 'user_id' not in session: return jsonify({'success': False})
    file = request.files.get('w_image')
    if not file: return jsonify({'success': False})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                            f"ws_{session['user_id']}_{random.randint(1000, 9999)}_{secure_filename(file.filename)}")
    file.save(filepath)
    conn = sqlite3.connect('users.db')
    conn.execute(
        "INSERT INTO workshops (user_id, title, description, w_date, w_time, price, capacity, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session['user_id'], request.form.get('title'), request.form.get('desc'), request.form.get('date'),
         request.form.get('time'), request.form.get('price'), request.form.get('capacity'),
         '/' + filepath.replace('\\', '/')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/add_event', methods=['POST'])
def add_event():
    if 'user_id' not in session: return jsonify({'success': False})
    file = request.files.get('e_image')
    if not file: return jsonify({'success': False})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                            f"ev_{session['user_id']}_{random.randint(1000, 9999)}_{secure_filename(file.filename)}")
    file.save(filepath)
    conn = sqlite3.connect('users.db')
    conn.execute(
        "INSERT INTO events (user_id, title, description, e_date, e_time, price, capacity, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session['user_id'], request.form.get('title'), request.form.get('desc'), request.form.get('date'),
         request.form.get('time'), request.form.get('price'), request.form.get('capacity'),
         '/' + filepath.replace('\\', '/')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/get_details/<int:art_id>')
def get_details(art_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE artworks SET views = views + 1 WHERE id = ?", (art_id,))
    conn.commit()

    c.execute('''SELECT c.id, c.user_id, c.comment_text, c.owner_reply, c.created_at, u.fullname, u.profile_image, 
                 IFNULL((SELECT AVG(rating) FROM comment_ratings WHERE comment_id = c.id), 0) as avg_rating 
                 FROM comments c JOIN users u ON c.user_id = u.id WHERE c.artwork_id = ? ORDER BY c.created_at DESC''',
              (art_id,))
    comments = [
        {'id': row[0], 'user_id': row[1], 'text': row[2], 'reply': row[3], 'created_at': row[4], 'author': row[5],
         'img': row[6], 'rating': round(row[7], 1)} for row in c.fetchall()]
    user_liked = user_favorited = False
    if 'user_id' in session:
        c.execute("SELECT 1 FROM likes WHERE user_id=? AND artwork_id=?", (session['user_id'], art_id))
        if c.fetchone(): user_liked = True
        c.execute("SELECT 1 FROM favorites WHERE user_id=? AND artwork_id=?", (session['user_id'], art_id))
        if c.fetchone(): user_favorited = True
    conn.close()
    return jsonify({'comments': comments, 'user_liked': user_liked, 'user_favorited': user_favorited,
                    'current_user_id': session.get('user_id')})


@app.route('/api/get_reviews/<type>/<int:item_id>')
def get_reviews(type, item_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT r.id, r.user_id, r.review_text, r.owner_reply, r.created_at, u.fullname, u.profile_image,
                 IFNULL((SELECT AVG(rating) FROM review_ratings WHERE review_id = r.id), 0) as avg_rating
                 FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.item_type = ? AND r.item_id = ? ORDER BY r.created_at DESC''',
              (type, item_id))
    reviews = [
        {'id': row[0], 'user_id': row[1], 'text': row[2], 'reply': row[3], 'created_at': row[4], 'author': row[5],
         'img': row[6], 'rating': round(row[7], 1)} for row in c.fetchall()]
    conn.close()
    return jsonify({'reviews': reviews, 'current_user_id': session.get('user_id')})


@app.route('/api/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session: return jsonify({'success': False})
    data = request.json
    item_type, item_id, text, event_rating = data.get('item_type'), data.get('item_id'), data.get('review'), int(
        data.get('event_rating', 5))
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO reviews (user_id, item_type, item_id, review_text, event_rating) VALUES (?, ?, ?, ?, ?)",
                 (session['user_id'], item_type, item_id, text, event_rating))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/get_summary/<item_type>/<int:item_id>')
def get_summary(item_type, item_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    table = 'workshops' if item_type == 'workshop' else 'events'

    c.execute(f"SELECT price, capacity FROM {table} WHERE id=?", (item_id,))
    res = c.fetchone()
    if not res: conn.close(); return jsonify({'success': False})
    price, capacity = res

    try:
        c.execute("SELECT SUM(IFNULL(total_price, tickets * ?)), SUM(tickets) FROM reservations WHERE item_type=? AND item_id=? AND payment_status='Ödendi'", (price, item_type, item_id))
    except sqlite3.OperationalError:
        c.execute("SELECT SUM(tickets * ?), SUM(tickets) FROM reservations WHERE item_type=? AND item_id=? AND payment_status='Ödendi'", (price, item_type, item_id))
        
    res_data = c.fetchone()
    total_revenue = res_data[0] or 0
    total_paid_tickets = res_data[1] or 0

    c.execute("SELECT AVG(event_rating), COUNT(id) FROM reviews WHERE item_type=? AND item_id=?", (item_type, item_id))
    avg, count = c.fetchone()
    avg_rating = round(avg or 0, 1)
    total_reviews = count or 0

    conn.close()
    return jsonify({
        'success': True,
        'total_revenue': total_revenue,
        'total_paid_tickets': total_paid_tickets,
        'capacity': capacity,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews
    })


@app.route('/api/create_ticket', methods=['POST'])
def create_ticket():
    if 'user_id' not in session: return jsonify({'success': False})
    data = request.json
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO support_tickets (user_id, subject, message) VALUES (?, ?, ?)",
                 (session['user_id'], data.get('subject'), data.get('message')))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Talebiniz gönderildi.'})


@app.route('/api/reply_ticket', methods=['POST'])
def reply_ticket():
    if 'user_id' not in session or session.get('is_admin', 0) != 1: return jsonify({'success': False})
    data = request.json
    ticket_id = data.get('ticket_id')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT status FROM support_tickets WHERE id=?", (ticket_id,))
    ticket = c.fetchone()
    if ticket and ticket[0] == 'Yanıtlandı':
        conn.close()
        return jsonify({'success': False, 'message': 'Bu talep zaten yanıtlanmış ve değiştirilemez.'})
        
    c.execute("UPDATE support_tickets SET admin_reply=?, status='Yanıtlandı' WHERE id=?",
                 (data.get('reply'), ticket_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/send_chat', methods=['POST'])
def send_chat():
    if 'user_id' not in session: return jsonify({'success': False})
    data = request.json
    user_id = data.get('user_id') if session.get('is_admin') else session['user_id']
    is_from_admin = 1 if session.get('is_admin') else 0
    message = data.get('message')
    if not message: return jsonify({'success': False})
    
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO live_chat (user_id, message, is_from_admin) VALUES (?, ?, ?)",
                 (user_id, message, is_from_admin))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/get_chat')
@app.route('/api/get_chat/<int:user_id>')
def get_chat(user_id=None):
    if 'user_id' not in session: return jsonify({'success': False})
    target_user_id = user_id if session.get('is_admin') else session['user_id']
    if not target_user_id: return jsonify({'success': False})
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT message, is_from_admin, created_at FROM live_chat WHERE user_id = ? ORDER BY created_at ASC", (target_user_id,))
    messages = [{'message': row[0], 'is_from_admin': row[1], 'time': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'messages': messages})


@app.route('/api/get_chat_users')
def get_chat_users():
    if 'user_id' not in session or session.get('is_admin', 0) != 1: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT DISTINCT u.id, u.fullname, u.profile_image, 
                 (SELECT MAX(created_at) FROM live_chat WHERE user_id = u.id) as last_msg 
                 FROM users u JOIN live_chat l ON u.id = l.user_id 
                 ORDER BY last_msg DESC''')
    users = [{'id': row[0], 'name': row[1], 'img': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'users': users})


@app.route('/api/check_notifications')
def check_notifications():
    if 'user_id' not in session: return jsonify({'success': False})
    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM live_chat WHERE user_id = ? AND is_from_admin = 1", (user_id,))
    chat_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM support_tickets WHERE user_id = ? AND status = 'Yanıtlandı'", (user_id,))
    ticket_count = c.fetchone()[0]
    
    conn.close()
    return jsonify({'success': True, 'chat_count': chat_count, 'ticket_count': ticket_count})


@app.route('/api/add_comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO comments (user_id, artwork_id, comment_text) VALUES (?, ?, ?)",
                 (session['user_id'], request.json.get('art_id'), request.json.get('comment')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/like_art', methods=['POST'])
def like_art():
    if 'user_id' not in session: return jsonify({'success': False})
    art_id, user_id = request.json.get('art_id'), session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO likes (user_id, artwork_id) VALUES (?, ?)", (user_id, art_id)); liked = True
    except sqlite3.IntegrityError:
        c.execute("DELETE FROM likes WHERE user_id=? AND artwork_id=?", (user_id, art_id)); liked = False
    conn.commit()
    c.execute("SELECT COUNT(*) FROM likes WHERE artwork_id=?", (art_id,))
    new_count = c.fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'liked': liked, 'new_count': new_count})


@app.route('/api/toggle_favorite', methods=['POST'])
def toggle_favorite():
    if 'user_id' not in session: return jsonify({'success': False})
    art_id, user_id = request.json.get('art_id'), session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO favorites (user_id, artwork_id) VALUES (?, ?)", (user_id, art_id)); favorited = True
    except sqlite3.IntegrityError:
        c.execute("DELETE FROM favorites WHERE user_id=? AND artwork_id=?", (user_id, art_id)); favorited = False
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'favorited': favorited})


@app.route('/api/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session: return jsonify({'success': False})
    data = request.json
    p_type, p_id, user_id = data.get('type'), data.get('id'), session['user_id']
    coupon_code = data.get('coupon_code')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    if p_type == 'art':
        c.execute("SELECT is_sold, price FROM artworks WHERE id=?", (p_id,))
        art = c.fetchone()
        if not art or art[0] == 1: conn.close(); return jsonify(
            {'success': False, 'message': 'Maalesef bu eser az önce satıldı!'})
        
        final_price = art[1]
        if coupon_code:
            c.execute("SELECT discount_rate, is_used FROM user_coupons WHERE user_id = ? AND UPPER(code) = ?", (user_id, coupon_code.upper()))
            coupon = c.fetchone()
            if coupon and coupon[1] == 0:
                final_price = art[1] * (1 - coupon[0])
                c.execute("UPDATE user_coupons SET is_used=1 WHERE user_id = ? AND UPPER(code) = ?", (user_id, coupon_code.upper()))
        
        c.execute("UPDATE artworks SET is_sold=1 WHERE id=?", (p_id,))
        c.execute("INSERT INTO purchases (user_id, artwork_id, price) VALUES (?, ?, ?)", (user_id, p_id, final_price))
        
    elif p_type == 'reservation':
        c.execute("SELECT item_type, item_id, tickets FROM reservations WHERE id=? AND user_id=?", (p_id, user_id))
        res_data = c.fetchone()
        if res_data:
            item_type, item_id, tickets = res_data
            table = 'workshops' if item_type == 'workshop' else 'events'
            c.execute(f"SELECT price FROM {table} WHERE id=?", (item_id,))
            item_price = c.fetchone()[0]
            base_price = item_price * tickets
            final_price = base_price
            
            if coupon_code:
                c.execute("SELECT discount_rate, is_used FROM user_coupons WHERE user_id = ? AND UPPER(code) = ?", (user_id, coupon_code.upper()))
                coupon = c.fetchone()
                if coupon and coupon[1] == 0:
                    c.execute("UPDATE user_coupons SET is_used=1 WHERE user_id = ? AND UPPER(code) = ?", (user_id, coupon_code.upper()))
                    final_price = base_price * (1 - coupon[0])
                    
            c.execute("UPDATE reservations SET payment_status='Ödendi', total_price=? WHERE id=? AND user_id=?", (final_price, p_id, user_id))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Ödemeniz başarıyla alındı. Teşekkürler!'})


@app.route('/api/reserve', methods=['POST'])
def reserve():
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Lütfen giriş yapın.'})
    data = request.json
    item_type, item_id, tickets, user_id = data.get('type'), data.get('id'), int(data.get('tickets', 1)), session[
        'user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    table = 'workshops' if item_type == 'workshop' else 'events'
    c.execute(f"SELECT capacity FROM {table} WHERE id=?", (item_id,))
    total_capacity = c.fetchone()[0]
    c.execute("SELECT SUM(tickets) FROM reservations WHERE item_type=? AND item_id=?", (item_type, item_id))
    reserved = c.fetchone()[0] or 0
    if reserved + tickets > total_capacity: conn.close(); return jsonify(
        {'success': False, 'message': 'Maalesef yeterli kontenjan kalmadı!'})
    c.execute("INSERT INTO reservations (user_id, item_type, item_id, tickets) VALUES (?, ?, ?, ?)",
              (user_id, item_type, item_id, tickets))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Rezervasyon oluşturuldu. Lütfen ödeme işlemini tamamlayın.'})


@app.route('/api/update_reservation', methods=['POST'])
def update_reservation():
    if 'user_id' not in session: return jsonify({'success': False})
    res_id, tickets = request.json.get('res_id'), int(request.json.get('tickets'))
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT item_type, item_id FROM reservations WHERE id=? AND user_id=?", (res_id, session['user_id']))
    res = c.fetchone()
    if not res: conn.close(); return jsonify({'success': False, 'message': 'Bulunamadı.'})
    item_type, item_id = res
    table = 'workshops' if item_type == 'workshop' else 'events'
    c.execute(f"SELECT capacity FROM {table} WHERE id=?", (item_id,))
    capacity = c.fetchone()[0]
    c.execute("SELECT SUM(tickets) FROM reservations WHERE item_type=? AND item_id=? AND id!=?",
              (item_type, item_id, res_id))
    others = c.fetchone()[0] or 0
    if others + tickets > capacity: conn.close(); return jsonify(
        {'success': False, 'message': 'Yeterli kontenjan yok!'})
    c.execute("UPDATE reservations SET tickets=? WHERE id=? AND user_id=?", (tickets, res_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Güncellendi.'})


@app.route('/api/delete_comment/<int:cmt_id>', methods=['POST'])
def delete_comment(cmt_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM comments WHERE id=? AND user_id=?", (cmt_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/delete_review/<int:rev_id>', methods=['POST'])
def delete_review(rev_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM reviews WHERE id=? AND user_id=?", (rev_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/delete_art/<int:art_id>', methods=['POST'])
def delete_art(art_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM artworks WHERE id=? AND user_id=?", (art_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/delete_workshop/<int:w_id>', methods=['POST'])
def delete_workshop(w_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM workshops WHERE id=? AND user_id=?", (w_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/delete_event/<int:e_id>', methods=['POST'])
def delete_event(e_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM events WHERE id=? AND user_id=?", (e_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/cancel_reservation/<int:res_id>', methods=['POST'])
def cancel_reservation(res_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db'); conn.execute("DELETE FROM reservations WHERE id=? AND user_id=?", (res_id, session['user_id'])); conn.commit(); conn.close(); return jsonify({'success': True})


@app.route('/api/apply_coupon', methods=['POST'])
def apply_coupon():
    if 'user_id' not in session: return jsonify({'success': False, 'message': 'Oturum açmalısınız.'})
    data = request.json
    code = data.get('code', '').upper()
    user_id = session['user_id']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT discount_rate, is_used FROM user_coupons WHERE user_id = ? AND UPPER(code) = ?", (user_id, code))
    coupon = c.fetchone()
    conn.close()
    
    if not coupon:
        return jsonify({'success': False, 'message': 'Geçersiz kupon kodu.'})
    if coupon[1] == 1:
        return jsonify({'success': False, 'message': 'Bu kupon zaten kullanılmış.'})
        
    return jsonify({'success': True, 'discount_rate': coupon[0], 'message': f'%{int(coupon[0]*100)} indirim uygulandı!'})


@app.route('/api/get_items_for_comparison/<comp_type>')
def get_items_for_comparison(comp_type):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    items = []
    if comp_type == 'art':
        c.execute("SELECT a.id, a.title, a.price, a.category, u.fullname as artist FROM artworks a JOIN users u ON a.user_id = u.id")
        for row in c.fetchall():
            d = dict(row)
            d['unique_id'] = f"art_{d['id']}"
            items.append(d)
    else:
        c.execute("SELECT id, 'event' as type, title, price, capacity, e_date as date FROM events UNION SELECT id, 'workshop' as type, title, price, capacity, w_date as date FROM workshops")
        for row in c.fetchall():
            d = dict(row)
            d['unique_id'] = f"{d['type']}_{d['id']}"
            items.append(d)
    conn.close()
    return jsonify({'success': True, 'items': items})


@app.route('/api/save_comparison', methods=['POST'])
def save_comparison():
    if 'user_id' not in session: return jsonify({'success': False})
    data = request.json
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO saved_comparisons (user_id, comp_type, item_ids, title) VALUES (?, ?, ?, ?)",
                 (session['user_id'], data.get('type'), ",".join(map(str, data.get('ids'))), data.get('title')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/get_saved_comparisons')
def get_saved_comparisons():
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM saved_comparisons WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    comps = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'comparisons': comps})


@app.route('/api/delete_comparison/<int:comp_id>', methods=['POST'])
def delete_comparison(comp_id):
    if 'user_id' not in session: return jsonify({'success': False})
    conn = sqlite3.connect('users.db')
    conn.execute("DELETE FROM saved_comparisons WHERE id = ? AND user_id = ?", (comp_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/create_coupon', methods=['POST'])
def admin_create_coupon():
    if 'user_id' not in session or session.get('is_admin', 0) != 1: return jsonify({'success': False})
    data = request.json
    user_ids = data.get('user_ids', [])
    code = data.get('code', '').strip().upper()
    rate = float(data.get('rate', 0)) / 100
    
    if not user_ids or not code or rate <= 0:
        return jsonify({'success': False, 'message': 'Lütfen tüm alanları eksiksiz doldurun.'})
        
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        for uid in user_ids:
            c.execute("INSERT INTO user_coupons (user_id, code, discount_rate) VALUES (?, ?, ?)", (uid, code, rate))
        conn.commit()
        return jsonify({'success': True, 'message': f'{len(user_ids)} kullanıcıya kupon başarıyla tanımlandı.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Hata: {str(e)}'})
    finally:
        conn.close()


@app.route('/api/content/<page_name>')
def get_content(page_name):
    if 'user_id' not in session: return jsonify({'html': 'Giriş yapın.'})
    user_id = session['user_id']
    is_admin = session.get('is_admin', 0)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT fullname, email, profile_image FROM users WHERE id = ?", (user_id,))
    fullname, email, img = c.fetchone()

    sidebar_top = f'''
        <a href="#" onclick="loadContent('gallery')">Ana Sayfa</a>
        <a href="#" onclick="loadContent('workshops')">Atölyeler</a>
        <a href="#" onclick="loadContent('events')">Etkinlikler</a>
        <a href="#" onclick="loadContent('profile')">Profil</a>
    '''
    if is_admin:
        sidebar_top += '<a href="#" onclick="loadContent(\'admin_panel\')">Admin Paneli</a>'
    else:
        sidebar_top += f'''
            <a href="#" onclick="loadContent('create')">Oluştur</a>
            <a href="#" onclick="loadContent('favorites')">Favoriler</a>
            <a href="#" onclick="loadContent('purchases')">Alınan Eserler</a>
            <a href="#" onclick="loadContent('reservations')">Rezervasyonlar</a>
            <a href="#" onclick="loadContent('comparison')">Karşılaştırma</a>
            <a href="#" onclick="loadContent('support')" id="sidebar-support-link">Müşteri Destek</a>
        '''
    
    sidebar_links = f'''
        <div class="sidebar-top">{sidebar_top}</div>
        <div class="sidebar-bottom">
            <a href="#" onclick="loadContent('settings')">Ayarlar</a>
        </div>
    '''

    if page_name == 'gallery':
        c.execute('''SELECT a.id, a.user_id, a.title, a.description, a.price, a.image_path, a.is_sold, a.views, u.fullname, u.profile_image, 
                     (SELECT COUNT(*) FROM likes WHERE artwork_id = a.id) as like_count,
                     (SELECT COUNT(*) FROM comments WHERE artwork_id = a.id) as comment_count
                     FROM artworks a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC''')
        artworks = c.fetchall()
        art_cards_html, current_x = "", 100
        for art in artworks:
            art_id, owner_id, title, desc, price, img_path, is_sold, views, author_name, author_img, like_count, comment_count = art
            top_pos, card_scale = random.randint(5, 50), random.uniform(0.85, 1.15)
            anim_duration_y, anim_delay = random.uniform(3, 6), random.uniform(-5, 0)
            safe_title, safe_desc = title.replace("'", "\\'"), desc.replace("'", "\\'").replace('\n', ' ')
            is_owner = 'true' if owner_id == user_id else 'false'
            sold_overlay = '<div style="position:absolute; top:40%; left:50%; transform:translate(-50%, -50%) rotate(-15deg); background:rgba(231,76,60,0.9); color:white; padding:10px 20px; font-size:24px; font-weight:bold; border-radius:8px; border:3px solid white; z-index:100;">SATILDI</div>' if is_sold else ''

            art_cards_html += f'''
                <div class="floating-art-card" style="position: absolute; left: {current_x}px; top: {top_pos}%; transform: scale({card_scale}); animation: floatY {anim_duration_y}s ease-in-out infinite alternate {anim_delay}s;" 
                     onclick="openDetailModal({art_id}, '{safe_title}', '{safe_desc}', {price}, '{img_path}', '{author_name}', '{author_img}', {like_count}, {is_owner}, {is_sold})">
                    <img src="{author_img}" class="author-badge">
                    <div class="art-frame"><img src="{img_path}"> {sold_overlay}</div>
                    <div class="like-badge-floating" id="badge-like-{art_id}" style="display:flex; gap:10px;">
                        <span>👁️ {views}</span> <span>💬 {comment_count}</span> <span>❤️ {like_count}</span>
                    </div>
                </div>
            '''
            current_x += random.randint(350, 600)
        canvas_width = current_x + 800
        html_content = f'''<div class="fullscreen-gallery-wrapper"><div class="gallery-blur-bg"></div><div class="pan-arrow left" onclick="panGallery(-1)">&#10094;</div><div class="gallery-viewport"><div class="gallery-canvas" id="gallery-canvas" style="width: {canvas_width}px;">{art_cards_html if artworks else '<h2 style="color:white; margin:auto;">İlk eseri sen yükle!</h2>'}</div></div><div class="pan-arrow right" onclick="panGallery(1)">&#10095;</div></div>{get_art_modal_html()}{get_payment_modal_html()}'''
        conn.close()
        return jsonify({'html': html_content, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'workshops':
        c.execute('''SELECT w.id, w.user_id, w.title, w.description, w.w_date, w.w_time, w.price, w.capacity, w.image_path, u.fullname, u.profile_image,
                     IFNULL((SELECT SUM(tickets) FROM reservations WHERE item_type='workshop' AND item_id=w.id), 0) as reserved,
                     IFNULL((SELECT AVG(event_rating) FROM reviews WHERE item_type='workshop' AND item_id=w.id), 0) as avg_rating
                     FROM workshops w JOIN users u ON w.user_id = u.id ORDER BY w.created_at DESC''')
        workshops = c.fetchall()
        active_cards, past_cards = "", ""
        for w in workshops:
            safe_title, safe_desc = w[2].replace("'", "\\'"), w[3].replace("'", "\\'").replace('\n', ' ')
            is_owner = 'true' if w[1] == user_id else 'false'
            item_datetime = f"{w[4]} {w[5]}"
            is_past = 'true' if item_datetime < now_str else 'false'
            rating_html = f'<div style="position:absolute; top:10px; right:10px; background:rgba(0,0,0,0.7); color:#f1c40f; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:12px; z-index:10;">⭐ {round(w[12], 1)} / 5</div>' if w[12] > 0 else ''
            card_html = f'''<div class="info-card" style="cursor:pointer;" onclick="openInfoModal({w[0]}, 'workshop', '{safe_title}', '{safe_desc}', '{w[4]}', '{w[5]}', {w[6]}, {w[7]}, '{w[8]}', '{w[9]}', '{w[10]}', {is_owner}, {w[11]}, {is_past})">{rating_html}<img src="{w[8]}" class="info-card-img"><div class="info-card-body"><h3>{w[2]}</h3><p>{w[3]}</p><div class="info-card-footer"><span>📅 {w[4]}</span><span>💰 {w[6]} ₺</span></div></div></div>'''
            if item_datetime < now_str: past_cards += card_html
            else: active_cards += card_html
        html = f'''<div style="padding:40px;"><h2>🎨 Aktif Atölyeler</h2><div class="info-card-grid" style="margin-bottom: 50px;">{active_cards if active_cards else '<p>Aktif atölye yok.</p>'}</div><h2 style="color:#888;">⏳ Geçmiş Atölyeler (Değerlendirmeler)</h2><div class="info-card-grid" style="opacity: 0.8;">{past_cards if past_cards else '<p>Geçmiş atölye yok.</p>'}</div></div> {get_info_modal_html()}'''
        conn.close()
        return jsonify({'html': html, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'events':
        c.execute('''SELECT e.id, e.user_id, e.title, e.description, e.e_date, e.e_time, e.price, e.capacity, e.image_path, u.fullname, u.profile_image,
                     IFNULL((SELECT SUM(tickets) FROM reservations WHERE item_type='event' AND item_id=e.id), 0) as reserved,
                     IFNULL((SELECT AVG(event_rating) FROM reviews WHERE item_type='event' AND item_id=e.id), 0) as avg_rating
                     FROM events e JOIN users u ON e.user_id = u.id ORDER BY e.created_at DESC''')
        events = c.fetchall()
        active_cards, past_cards = "", ""
        for e in events:
            safe_title, safe_desc = e[2].replace("'", "\\'"), e[3].replace("'", "\\'").replace('\n', ' ')
            is_owner = 'true' if e[1] == user_id else 'false'
            item_datetime = f"{e[4]} {e[5]}"
            is_past = 'true' if item_datetime < now_str else 'false'
            rating_html = f'<div style="position:absolute; top:10px; right:10px; background:rgba(0,0,0,0.7); color:#f1c40f; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:12px; z-index:10;">⭐ {round(e[12], 1)} / 5</div>' if e[12] > 0 else ''
            card_html = f'''<div class="info-card" style="cursor:pointer;" onclick="openInfoModal({e[0]}, 'event', '{safe_title}', '{safe_desc}', '{e[4]}', '{e[5]}', {e[6]}, {e[7]}, '{e[8]}', '{e[9]}', '{e[10]}', {is_owner}, {e[11]}, {is_past})">{rating_html}<img src="{e[8]}" class="info-card-img"><div class="info-card-body"><h3>{e[2]}</h3><p>{e[3]}</p><div class="info-card-footer"><span>📅 {e[4]}</span><span>💰 {e[6]} ₺</span></div></div></div>'''
            if item_datetime < now_str: past_cards += card_html
            else: active_cards += card_html
        html = f'''<div style="padding:40px;"><h2>📅 Aktif Etkinlikler</h2><div class="info-card-grid" style="margin-bottom: 50px;">{active_cards if active_cards else '<p>Aktif etkinlik yok.</p>'}</div><h2 style="color:#888;">⏳ Geçmiş Etkinlikler (Değerlendirmeler)</h2><div class="info-card-grid" style="opacity: 0.8;">{past_cards if past_cards else '<p>Geçmiş etkinlik yok.</p>'}</div></div> {get_info_modal_html()}'''
        conn.close()
        return jsonify({'html': html, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'settings':
        conn.close()
        return jsonify({'html': '<div style="padding:40px;"><h2>⚙️ Ayarlar</h2><br><a href="/logout" class="btn" style="background:#ff4757; width:auto; padding:10px 20px;">Sistemden Çıkış Yap</a></div>', 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'purchases':
        c.execute('''SELECT a.id, a.title, a.description, p.price, a.image_path, u.fullname, u.profile_image 
                         FROM purchases p JOIN artworks a ON p.artwork_id = a.id 
                         JOIN users u ON a.user_id = u.id WHERE p.user_id = ? ORDER BY p.created_at DESC''', (user_id,))
        purchases = c.fetchall()
        cards = ""
        for p_art in purchases:
            art_id, title, desc, price, img_path, author_name, author_img = p_art
            safe_title, safe_desc = title.replace("'", "\\'"), desc.replace("'", "\\'").replace('\n', ' ')
            cards += f'''
                <div class="info-card" style="cursor:pointer;" onclick="openDetailModal({art_id}, '{safe_title}', '{safe_desc}', {price}, '{img_path}', '{author_name}', '{author_img}', 0, true, 1)">
                    <div style="position:absolute; top:10px; right:10px; background:#27ae60; color:#fff; padding:5px 10px; border-radius:5px; font-weight:bold; font-size:12px; z-index:10;">✓ Sizin Eseriniz</div>
                    <img src="{img_path}" class="info-card-img" style="height: 220px;">
                    <div class="info-card-body">
                        <h3>{title}</h3>
                        <div style="display:flex; align-items:center; gap:10px; margin: 10px 0;"><img src="{author_img}" style="width:30px; height:30px; border-radius:50%;"> <span style="font-size:14px; color:#555;">{author_name}</span></div>
                        <div class="info-card-footer" style="margin-top:auto;"><span>Ödenen: 💰 {price:.2f} ₺</span></div>
                    </div>
                </div>'''
        html = f'<div style="padding:40px;"><h2>🛍️ Alınan Eserlerim</h2><div class="info-card-grid">{cards if cards else "<p>Henüz bir eser satın almadınız.</p>"}</div></div> {get_art_modal_html()}'
        conn.close()
        return jsonify({'html': html, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'favorites':
        c.execute('''SELECT a.id, a.user_id, a.title, a.description, a.price, a.image_path, a.is_sold, u.fullname, u.profile_image,
                         (SELECT COUNT(*) FROM likes WHERE artwork_id = a.id) as like_count
                         FROM artworks a JOIN users u ON a.user_id = u.id JOIN favorites f ON a.id = f.artwork_id 
                         WHERE f.user_id = ? ORDER BY f.id DESC''', (user_id,))
        favorites = c.fetchall()
        cards = ""
        for f_art in favorites:
            art_id, owner_id, title, desc, price, img_path, is_sold, author_name, author_img, like_count = f_art
            safe_title, safe_desc = title.replace("'", "\\'"), desc.replace("'", "\\'").replace('\n', ' ')
            is_owner = 'true' if owner_id == user_id else 'false'
            sold_tag = '<span style="color:#e74c3c; font-weight:bold;">(SATILDI)</span>' if is_sold else ''
            cards += f'''
                <div class="info-card" style="cursor:pointer;" onclick="openDetailModal({art_id}, '{safe_title}', '{safe_desc}', {price}, '{img_path}', '{author_name}', '{author_img}', {like_count}, {is_owner}, {is_sold})">
                    <img src="{img_path}" class="info-card-img" style="height: 220px;">
                    <div class="info-card-body">
                        <h3>{title} {sold_tag}</h3>
                        <div style="display:flex; align-items:center; gap:10px; margin: 10px 0;"><img src="{author_img}" style="width:30px; height:30px; border-radius:50%;"> <span style="font-size:14px; color:#555;">{author_name}</span></div>
                        <div class="info-card-footer" style="margin-top:auto;"><span>💰 {price} ₺</span></div>
                    </div>
                </div>'''
        html = f'<div style="padding:40px;"><h2>📌 Favorilerim</h2><div class="info-card-grid">{cards if cards else "<p>Henüz favorilere eser eklemediniz.</p>"}</div></div> {get_art_modal_html()} {get_payment_modal_html()}'
        conn.close()
        return jsonify({'html': html, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'reservations':
        try:
            c.execute("SELECT id, item_type, item_id, tickets, payment_status, total_price FROM reservations WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            reservations = c.fetchall()
        except sqlite3.OperationalError:
            c.execute("SELECT id, item_type, item_id, tickets, payment_status, NULL as total_price FROM reservations WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            reservations = c.fetchall()

        active_cards, past_cards = "", ""
        for r in reservations:
            res_id, item_type, item_id, tickets, payment_status, total_price = r
            table = 'workshops' if item_type == 'workshop' else 'events'
            prefix = 'w' if item_type == 'workshop' else 'e'
            c.execute(f"SELECT {prefix}_date, {prefix}_time, title, price, image_path, capacity, user_id FROM {table} WHERE id=?", (item_id,))
            item = c.fetchone()
            if not item: continue
            date, time, title, price, img_path, cap, author_id = item
            c.execute("SELECT fullname FROM users WHERE id=?", (author_id,))
            author_name = c.fetchone()[0]
            c.execute("SELECT SUM(tickets) FROM reservations WHERE item_type=? AND item_id=? AND id!=?", (item_type, item_id, res_id))
            others = c.fetchone()[0] or 0
            max_allowed = cap - others
            safe_title = title.replace("'", "\\'")
            label = 'Atölye' if item_type == 'workshop' else 'Etkinlik'
            item_datetime = f"{date} {time}"
            is_past = 'true' if item_datetime < now_str else 'false'
            
            paid_text = f"Ödenen: {total_price:.2f} ₺" if total_price is not None else f"Toplam: {price * tickets} ₺"
            pay_tag = f'<span style="color:#27ae60; font-weight:bold;">✓ {payment_status} ({paid_text})</span>' if payment_status == 'Ödendi' else f'<span style="color:#e74c3c; font-weight:bold;">! {payment_status}</span>'
            card_html = f'''
                    <div class="info-card" style="cursor:pointer;" onclick="openReservationModal({res_id}, '{safe_title}', '{date}', '{time}', {price}, {tickets}, '{img_path}', '{author_name}', '{item_type}', {item_id}, {max_allowed}, '{payment_status}', {is_past})"> 
                        <img src="{img_path}" class="info-card-img" style="height: 180px;">
                        <div class="info-card-body">
                            <div style="background: #e8effc; color: #6a89cc; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight:bold; display:inline-block; margin-bottom: 5px;">{label}</div>
                            <h3>{title}</h3>
                            <p style="color:#666; font-size:14px; margin-top:5px;">🎫 <strong>{tickets} Bilet</strong> | {pay_tag}</p>
                            <div class="info-card-footer" style="margin-top:auto;"><span>📅 {date} | ⏰ {time}</span></div>
                        </div>
                    </div>'''
            if item_datetime < now_str: past_cards += card_html
            else: active_cards += card_html
        html = f'''<div style="padding:40px;"><h2>🎟️ Aktif Rezervasyonlarım</h2><div class="info-card-grid" style="margin-bottom: 50px;">{active_cards if active_cards else "<p>Aktif rezervasyonunuz bulunmuyor.</p>"}</div><h2 style="color:#888;">⏳ Geçmiş Rezervasyonlarım (Değerlendirebilirsiniz)</h2><div class="info-card-grid" style="opacity: 0.8;">{past_cards if past_cards else "<p>Geçmiş rezervasyonunuz bulunmuyor.</p>"}</div></div>{get_reservation_modal_html()}{get_payment_modal_html()}'''
        conn.close()
        return jsonify({'html': html, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'comparison':
        html_content = '''
        <div style="padding:40px;">
            <h2 style="margin-bottom:20px;">⚖️ Karşılaştırma Paneli</h2>
            <div style="display:flex; gap:10px; margin-bottom:30px; background:#f9f9f9; padding:20px; border-radius:12px; border:1px solid #eee;">
                <button class="btn" style="width:auto; background:#6a89cc;" onclick="openComparisonSelector('art')">🎨 Eserleri Karşılaştır</button>
                <button class="btn" style="width:auto; background:#e67e22;" onclick="openComparisonSelector('event')">📅 Etkinlikleri Karşılaştır</button>
            </div>
            <div id="comparison-result-area" style="margin-top:30px; overflow-x:auto;">
                <p style="color:#888; text-align:center; padding:50px; background:#fff; border:2px dashed #eee; border-radius:12px;">Karşılaştırmak istediğiniz öğeleri seçin.</p>
            </div>
            <div style="margin-top:50px;">
                <h3>💾 Kayıtlı Karşılaştırmalarım</h3>
                <div id="saved-comparisons-list" style="margin-top:20px;">Yükleniyor...</div>
            </div>
        </div>
        <div id="comp-selector-modal" class="modal-overlay">
            <div class="modal-content" style="width:500px;">
                <span class="close-btn" onclick="closeAnyModal('comp-selector-modal')">&times;</span>
                <h2 id="comp-selector-title">Öğe Seçin</h2>
                <div id="comp-selector-items" style="max-height:300px; overflow-y:auto; margin:20px 0; border:1px solid #eee; padding:10px; border-radius:8px;"></div>
                <button class="btn" onclick="startComparison()">Seçilenleri Karşılaştır</button>
            </div>
        </div>
        '''
        conn.close()
        return jsonify({'html': html_content, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'support':
        c.execute("SELECT id, subject, message, admin_reply, status, created_at FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        tickets = c.fetchall()
        tickets_html = ""
        for t in tickets:
            t_id, sub, msg, reply, status, c_at = t
            status_color = "#27ae60" if status == "Yanıtlandı" else "#e74c3c"
            reply_html = f"<div style='margin-top:10px; padding:10px; background:#e8effc; border-left:4px solid #6a89cc; border-radius:4px;'><strong>Yönetici Yanıtı:</strong> {reply}</div>" if reply else "<div style='margin-top:10px; font-style:italic; color:#888;'>Henüz yanıtlanmadı.</div>"
            tickets_html += f'''
            <div style="background:#fff; border:1px solid #eee; padding:15px; border-radius:8px; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <h3 style="margin:0; color:#333;">{sub}</h3>
                    <span style="background:{status_color}; color:#fff; padding:3px 8px; border-radius:4px; font-size:12px;">{status}</span>
                </div>
                <p style="margin:0; color:#555; font-size:14px;">{msg}</p>
                <div style="font-size:11px; color:#aaa; margin-top:5px;">Oluşturulma: {c_at}</div>
                {reply_html}
            </div>'''
        html_content = f'''
        <div style="padding:40px; max-width:800px; margin:auto;">
            <h2 style="color:#2c3e50; margin-bottom:20px;">Müşteri Destek</h2>
            <div style="background:#f9f9f9; padding:20px; border-radius:12px; margin-bottom:30px; border:1px solid #ddd;">
                <h3 style="margin-top:0;">Yeni Destek Talebi</h3>
                <form onsubmit="submitTicket(event)">
                    <div class="input-group">
                        <label>Konu</label>
                        <input type="text" id="ticket-subject" required style="width:100%; padding:10px; border:1px solid #ccc; border-radius:6px;">
                    </div>
                    <div class="input-group" style="margin-top:15px;">
                        <label>Mesajınız</label>
                        <textarea id="ticket-message" rows="4" required style="width:100%; padding:10px; border:1px solid #ccc; border-radius:6px; resize:vertical;"></textarea>
                    </div>
                    <button type="submit" class="btn" style="margin-top:15px; background:#6a89cc;">Gönder</button>
                </form>
            </div>
            <h3>Geçmiş Taleplerim</h3>
            <div>{tickets_html if tickets_html else '<p style="color:#777;">Henüz bir destek talebiniz bulunmuyor.</p>'}</div>
        </div>'''
        conn.close()
        return jsonify({'html': html_content, 'sidebar': sidebar_links, 'is_admin': is_admin})

    elif page_name == 'admin_panel':
        if not is_admin:
            conn.close()
            return jsonify({'html': 'Yetkiniz yok.', 'sidebar': sidebar_links, 'is_admin': is_admin})
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin=0")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM artworks")
        total_arts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM reservations WHERE payment_status='Ödendi'")
        total_sales = c.fetchone()[0]
        
        c.execute("SELECT id, fullname, email FROM users WHERE is_admin=0 ORDER BY fullname ASC")
        all_users = c.fetchall()
        user_options = "".join([f'<option value="{u[0]}">{u[1]} ({u[2]})</option>' for u in all_users])
        
        c.execute("SELECT fullname, email, created_at FROM users WHERE is_admin=0 ORDER BY created_at DESC LIMIT 5")
        latest_users = c.fetchall()
        user_list_html = "".join([f"<li><strong>{u[0]}</strong> ({u[1]}) - <span style='color:#888; font-size:12px;'>{u[2]}</span></li>" for u in latest_users])
        
        c.execute('''SELECT t.id, u.fullname, u.email, t.subject, t.message, t.admin_reply, t.status, t.created_at 
                     FROM support_tickets t JOIN users u ON t.user_id = u.id ORDER BY CASE WHEN t.status = 'Açık' THEN 0 ELSE 1 END, t.created_at DESC''')
        all_tickets = c.fetchall()
        admin_tickets_html = ""
        for t in all_tickets:
            t_id, u_name, u_email, sub, msg, reply, status, c_at = t
            status_color = "#27ae60" if status == "Yanıtlandı" else "#e74c3c"
            
            if status == "Yanıtlandı":
                reply_section = f'''
                    <div style="margin-top:10px; padding:10px; background:#e8effc; border-left:4px solid #6a89cc; border-radius:4px;">
                        <strong>Cevabınız:</strong><br>{reply}
                    </div>'''
            else:
                reply_section = f'''
                    <div style="margin-top:10px;">
                        <textarea id="admin-reply-{t_id}" rows="2" style="width:100%; padding:8px; border:1px solid #ccc; border-radius:4px; margin-bottom:5px;" placeholder="Kullanıcıya yanıt yaz..."></textarea>
                        <button class="btn" style="width:auto; padding:5px 15px; font-size:12px; background:#27ae60;" onclick="replyTicket({t_id})">Yanıtı Gönder</button>
                    </div>'''
            
            admin_tickets_html += f'''
            <div style="background:#fff; border:1px solid #eee; padding:15px; border-radius:8px; margin-bottom:15px; border-left:4px solid {status_color};">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <strong style="color:#2c3e50;">{sub}</strong>
                    <span style="font-size:12px; color:#888;">{c_at}</span>
                </div>
                <div style="font-size:12px; color:#666; margin-bottom:10px;">Gönderen: {u_name} ({u_email})</div>
                <p style="font-size:14px; color:#444; background:#f9f9f9; padding:10px; border-radius:4px;">{msg}</p>
                {reply_section}
            </div>'''
            
        html_content = f'''
            <div style="padding:40px;">
                <h2 style="color:#2c3e50;">Yönetici Paneli</h2>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:20px; margin-top:20px;">
                    <div style="background:#fff; padding:20px; border-radius:12px; border:1px solid #eee; text-align:center;">
                        <span style="font-size:14px; color:#666;">Toplam Kullanıcı</span><br><strong style="font-size:24px; color:#6a89cc;">{total_users}</strong>
                    </div>
                    <div style="background:#fff; padding:20px; border-radius:12px; border:1px solid #eee; text-align:center;">
                        <span style="font-size:14px; color:#666;">Toplam Eser</span><br><strong style="font-size:24px; color:#e67e22;">{total_arts}</strong>
                    </div>
                    <div style="background:#fff; padding:20px; border-radius:12px; border:1px solid #eee; text-align:center;">
                        <span style="font-size:14px; color:#666;">Bilet Satışları</span><br><strong style="font-size:24px; color:#27ae60;">{total_sales}</strong>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-top:40px;">
                    <div style="background:#fff; padding:25px; border-radius:12px; border:1px solid #eee;">
                        <h3>👥 Son Kayıt Olan Kullanıcılar</h3>
                        <ul style="list-style:none; padding:0; margin-top:15px; line-height:2;">{user_list_html if latest_users else '<li>Henüz kullanıcı yok.</li>'}</ul>
                    </div>
                    <div style="background:#fff; padding:25px; border-radius:12px; border:1px solid #eee; max-height: 500px; overflow-y: auto;">
                        <h3 style="margin-top:0;">Müşteri Destek Talepleri</h3>
                        <div style="margin-top:15px;">{admin_tickets_html if admin_tickets_html else '<p style="color:#888;">Açık destek talebi bulunmuyor.</p>'}</div>
                    </div>
                </div>
                <div style="margin-top:40px; background:#fff; padding:25px; border-radius:12px; border:1px solid #eee;">
                    <h3>💬 Canlı Destek (Anlık Mesajlaşma)</h3>
                    <div style="display:grid; grid-template-columns: 250px 1fr; gap:20px; margin-top:20px; height:400px; border:1px solid #eee; border-radius:8px; overflow:hidden;">
                        <div id="admin-chat-users" style="background:#f9f9f9; border-right:1px solid #eee; overflow-y:auto; padding:10px;"></div>
                        <div id="admin-chat-area" style="display:flex; flex-direction:column; background:#fff; height:400px; max-height:400px; overflow:hidden;">
                            <div id="admin-chat-messages" style="flex:1; padding:20px; overflow-y:auto; display:flex; flex-direction:column; gap:10px; min-height:0;">
                                <p style="text-align:center; color:#888; margin-top:150px;">Mesajlaşmak için bir kullanıcı seçin</p>
                            </div>
                            <div id="admin-chat-input-area" style="padding:15px; border-top:1px solid #eee; display:none; gap:10px; flex-shrink:0;">
                                <input type="text" id="admin-chat-input" placeholder="Mesajınızı yazın..." style="flex-grow:1; padding:10px; border:1px solid #ccc; border-radius:6px;" onkeypress="if(event.key==='Enter') sendAdminChatMessage()">
                                <button class="btn" style="width:auto; padding:10px 20px;" onclick="sendAdminChatMessage()">Gönder</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:40px; background:#fff; padding:25px; border-radius:12px; border:1px solid #eee;">
                    <h3>🎫 Kupon Tanımlama</h3>
                    <div style="margin-top:15px;">
                        <div class="input-group">
                            <label>Kullanıcı(lar) Seçin (Birden fazla için Ctrl ile tıklayın)</label>
                            <select id="admin-coupon-users" multiple style="width:100%; height:120px; padding:10px; border:1px solid #ccc; border-radius:6px; margin-top:5px;">
                                {user_options}
                            </select>
                        </div>
                        <div style="display:flex; gap:15px; margin-top:15px;">
                            <div class="input-group" style="flex:2;">
                                <label>Kupon Adı (Kod)</label>
                                <input type="text" id="admin-coupon-name" placeholder="Örn: OZEL50" style="width:100%; padding:10px; border:1px solid #ccc; border-radius:6px;">
                            </div>
                            <div class="input-group" style="flex:1;">
                                <label>İndirim Oranı (%)</label>
                                <input type="number" id="admin-coupon-rate" value="10" min="1" max="100" style="width:100%; padding:10px; border:1px solid #ccc; border-radius:6px;">
                            </div>
                        </div>
                        <button class="btn" style="margin-top:20px; background:#6a89cc;" onclick="submitAdminCoupon()">Kuponları Tanımla</button>
                        <p id="admin-coupon-message" style="margin-top:10px; font-weight:bold;"></p>
                    </div>
                </div>
            </div>'''
        conn.close()
        return jsonify({'html': html_content, 'sidebar': sidebar_links, 'is_admin': is_admin})



    elif page_name == 'profile':
        c.execute("SELECT code, discount_rate, is_used FROM user_coupons WHERE user_id = ?", (user_id,))
        coupons = c.fetchall()
        
        if is_admin:
            coupons_html = ""
        else:
            if coupons:
                coupons_list = "".join([f"""
                    <div style="background:white; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; {'opacity:0.6;' if c_row[2] else ''}">
                        <div>
                            <strong style="color:#6a89cc; font-size:16px;">{c_row[0]}</strong><br>
                            <span style="font-size:12px; color:#888;">%{int(c_row[1]*100)} İndirim</span>
                        </div>
                        <span style="font-size:12px; font-weight:bold; color:{'#e74c3c' if c_row[2] else '#27ae60'}">
                            { 'Kullanıldı' if c_row[2] else 'Aktif' }
                        </span>
                    </div>""" for c_row in coupons])
                
                coupons_html = f'''
                    <div style="margin-top:40px; background:#fff; padding:25px; border-radius:12px; border:1px solid #eee;">
                        <h3 style="margin-bottom:15px;">Kuponlarım</h3>
                        <div id="coupons-container" style="max-height:300px; overflow-y:auto;">
                            {coupons_list}
                        </div>
                    </div>
                '''
            else:
                coupons_html = '''
                    <div style="margin-top:40px; background:#fff; padding:25px; border-radius:12px; border:1px solid #eee;">
                        <h3>Kuponlarım</h3>
                        <div id="coupons-container" style="margin-top:15px; padding:15px; background:#f9f9f9; border-radius:8px; border:1px dashed #ccc; text-align:center; color:#888;">
                            Henüz bir kuponunuz bulunmuyor.
                        </div>
                    </div>
                '''
        
        html_content = f'''<div class="profile-container-inner"><div class="profile-preview"><div class="main-avatar-frame" onclick="document.getElementById('profile-upload').click()"><img id="current-avatar" src="{img}"><div class="avatar-overlay"><span>📷 Yükle</span></div></div><h2>{fullname}</h2><input type="file" id="profile-upload" accept="image/*" style="display: none;" onchange="previewImage(event, 'current-avatar')"></div><form id="profile-form" onsubmit="submitProfile(event)"><div class="input-group"><label>Ad Soyad</label><input type="text" id="prof-fullname" value="{fullname}" required></div><div class="input-group"><label>E-posta</label><input type="email" id="prof-email" value="{email}" required></div><div class="input-group"><label>Yeni Şifre</label><input type="password" id="prof-password" placeholder="Değiştirmeyecekseniz boş bırakın"></div><button type="submit" class="btn">Değişiklikleri Kaydet</button><p id="profile-message" class="status-msg"></p></form>{coupons_html}</div>'''
        conn.close()
        return jsonify({'html': html_content, 'is_admin': is_admin, 'sidebar': sidebar_links})

    elif page_name == 'create':
        html_content = f'''<div class="create-page-header"><h2>➕ Yeni Bir Şeyler Oluştur</h2><div class="create-options-container" style="display:flex; justify-content:center; gap:20px; margin-top:30px;"><div class="create-option-card" onclick="openAnyModal('art-modal')"><h3>🎨 Eser Ekle</h3></div><div class="create-option-card" onclick="openAnyModal('workshop-modal')"><h3>🛠️ Atölye Aç</h3></div><div class="create-option-card" onclick="openAnyModal('event-modal')"><h3>📅 Etkinlik Düzenle</h3></div></div></div><div id="art-modal" class="modal-overlay"><div class="modal-content"><span class="close-btn" onclick="closeAnyModal('art-modal')">&times;</span><h2>Eser Detayları</h2><form class="art-form-layout"><div class="art-upload-left"><div class="dashed-upload-box" onclick="document.getElementById('art-file').click()"><span id="upload-text">📷<br>Eser Yükle</span><img id="art-preview" src="" style="display: none;"></div><input type="file" id="art-file" accept="image/*" style="display: none;" onchange="previewImage(event, 'art-preview', 'upload-text')"></div><div class="art-details-right"><div class="input-group"><label>Eser Adı</label><input type="text" id="art-title" required></div><div class="input-group"><label>Kategori</label><input type="text" id="art-cat" placeholder="Örn: Yağlı Boya, Heykel..." required></div><div class="input-group"><label>Açıklama</label><textarea id="art-desc" rows="2" required></textarea></div><div class="input-group"><label>Fiyat (₺)</label><input type="number" id="art-price" required></div><button type="button" class="btn" onclick="submitArt()">Galeride Paylaş</button></div></form></div></div><div id="workshop-modal" class="modal-overlay"><div class="modal-content"><span class="close-btn" onclick="closeAnyModal('workshop-modal')">&times;</span><h2>Atölye Düzenle</h2><form class="art-form-layout"><div class="art-upload-left"><div class="dashed-upload-box" onclick="document.getElementById('w-file').click()"><span id="w-upload-text">📷<br>Atölye Afişi</span><img id="w-preview" src="" style="display: none;"></div><input type="file" id="w-file" accept="image/*" style="display: none;" onchange="previewImage(event, 'w-preview', 'w-upload-text')"></div><div class="art-details-right"><div class="input-group"><label>Atölye Adı</label><input type="text" id="w-title" required></div><div style="display:flex; gap:10px;"><div class="input-group" style="flex:1;"><label>Tarih</label><input type="date" id="w-date" required></div><div class="input-group" style="flex:1;"><label>Saat</label><input type="time" id="w-time" required></div></div><div style="display:flex; gap:10px;"><div class="input-group" style="flex:1;"><label>Ücret (₺)</label><input type="number" id="w-price" required></div><div class="input-group" style="flex:1;"><label>Kontenjan</label><input type="number" id="w-capacity" required></div></div><div class="input-group"><label>Açıklama</label><textarea id="w-desc" rows="2" required></textarea></div><button type="button" class="btn" onclick="submitWorkshop()">Atölyeyi Başlat</button></div></form></div></div><div id="event-modal" class="modal-overlay"><div class="modal-content"><span class="close-btn" onclick="closeAnyModal('event-modal')">&times;</span><h2>Etkinlik Düzenle</h2><form class="art-form-layout"><div class="art-upload-left"><div class="dashed-upload-box" onclick="document.getElementById('e-file').click()"><span id="e-upload-text">📷<br>Etkinlik Afişi</span><img id="e-preview" src="" style="display: none;"></div><input type="file" id="e-file" accept="image/*" style="display: none;" onchange="previewImage(event, 'e-preview', 'e-upload-text')"></div><div class="art-details-right"><div class="input-group"><label>Etkinlik Adı</label><input type="text" id="e-title" required></div><div style="display:flex; gap:10px;"><div class="input-group" style="flex:1;"><label>Tarih</label><input type="date" id="e-date" required></div><div class="input-group" style="flex:1;"><label>Saat</label><input type="time" id="e-time" required></div></div><div style="display:flex; gap:10px;"><div class="input-group" style="flex:1;"><label>Bilet Ücreti (₺)</label><input type="number" id="e-price" required></div><div class="input-group" style="flex:1;"><label>Kontenjan</label><input type="number" id="e-capacity" required></div></div><div class="input-group"><label>Açıklama</label><textarea id="e-desc" rows="2" required></textarea></div><button type="button" class="btn" onclick="submitEvent()">Etkinliği Duyur</button></div></form></div></div>'''
        conn.close()
        return jsonify({'html': html_content, 'is_admin': is_admin, 'sidebar': sidebar_links})
    conn.close()
    return jsonify({'html': 'Bilinmeyen sayfa.', 'sidebar': sidebar_links, 'is_admin': is_admin})


def get_art_modal_html():
    return '''
    <div id="art-detail-modal" class="modal-overlay">
        <div class="modal-content" style="max-height: 90vh; overflow-y: auto; position: relative;">
            <span class="close-btn" onclick="closeDetailModal()">&times;</span>
            <div id="art-owner-menu" class="three-dots-menu" style="display:none; position:absolute; top:25px; right:60px;">
                <button class="three-dots-btn">⋮</button><div class="three-dots-content"><a href="#" style="color:red;" onclick="deleteCurrentArt()">Sil</a></div>
            </div>
            <div class="art-form-layout">
                <div class="art-upload-left" style="display: flex; align-items: center; justify-content: center; background: #000; border-radius: 12px; overflow: hidden; max-height: 500px;"><img id="detail-img" src="" style="width: 100%; height: 100%; object-fit: contain;"></div>
                <div class="art-details-right" style="display: flex; flex-direction: column;">
                    <div class="user-info" style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;"><img id="detail-author-img" src="" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #6a89cc; object-fit: cover;"><div><span class="user-label">Sanatçı</span><span class="user-name" id="detail-author-name"></span></div></div>
                    <h2 id="detail-title" style="margin: 10px 0; font-size: 24px;"></h2><p id="detail-desc" style="color: #666; font-size: 14px; margin-bottom: 10px;"></p>
                    <div class="interaction-bar" style="border-top: 1px solid #eee; padding-top: 15px; flex-grow: 1; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div style="display:flex; gap:10px;"><button id="like-btn" class="btn" style="width: auto; background: #ff4757; padding: 8px 15px;" onclick="toggleLike()">🤍 Beğen (<span id="modal-like-count">0</span>)</button><button id="favorite-btn" class="btn" style="width: auto; background: #f1c40f; color: #333; padding: 8px 15px;" onclick="toggleFavorite()">📌 Favoriye Ekle</button><button id="buy-btn" class="btn" style="width: auto; background: #27ae60; padding: 8px 15px; display:none;" onclick="openPaymentModal('art', currentDetailArtId, currentDetailArtPrice)">💳 Satın Al</button><span id="sold-badge" style="display:none; color:#e74c3c; font-weight:bold; font-size:18px;">🔴 SATILDI</span></div>
                            <span style="font-size: 20px; font-weight: bold; color: #6a89cc;" id="detail-price"></span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px; margin-top:10px;"><h3 style="font-size:14px; color:#555;">Yorumlar</h3><select id="comment-sort" onchange="renderComments()" style="padding:2px 5px; border-radius:4px; font-size:12px; border:1px solid #ccc;"><option value="newest">En Yeni</option><option value="highest">En Yüksek Puanlı</option></select></div>
                        <div class="comments-section" id="comments-container" style="flex-grow: 1; min-height: 120px; max-height: 180px; overflow-y: auto; background: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 10px;"></div>
                        <div style="display: flex; gap: 10px;"><input type="text" id="new-comment" placeholder="Yorum yaz..." style="flex-grow: 1; padding: 10px; border-radius: 6px; border: 1px solid #ccc;"><button class="btn" style="width: auto; padding: 10px 15px;" onclick="postComment()">Gönder</button></div>
                    </div>
                </div>
            </div>
        </div>
    </div>'''


def get_info_modal_html():
    return '''
    <div id="info-detail-modal" class="modal-overlay">
        <div class="modal-content" style="max-height: 90vh; overflow-y: auto;">
            <span class="close-btn" onclick="closeAnyModal('info-detail-modal')">&times;</span>
            <div id="info-owner-menu" class="three-dots-menu" style="display:none; position:absolute; top:25px; right:60px;">
                <button class="three-dots-btn">⋮</button>
                <div class="three-dots-content">
                    <a href="#" style="color:#27ae60;" onclick="openSummaryReport()">📊 Özet Rapor</a>
                    <a href="#" style="color:red;" onclick="deleteCurrentInfo()">Sil</a>
                </div>
            </div>
            <div class="art-form-layout">
                <div class="art-upload-left" style="background:#000; border-radius:12px; overflow:hidden; max-height:400px;"><img id="info-img" src="" style="width:100%; height:100%; object-fit:cover;"></div>
                <div class="art-details-right" style="display:flex; flex-direction:column;">
                    <div class="user-info" style="display:flex; align-items:center; gap:15px; margin-bottom:10px;"><img id="info-author-img" src="" style="width:50px; height:50px; border-radius:50%; object-fit:cover;"><div><span class="user-label" id="info-role"></span><span class="user-name" id="info-author-name"></span></div></div>
                    <h2 id="info-title" style="margin:10px 0; font-size:26px;"></h2><p id="info-desc" style="color:#666; font-size:15px; flex-grow:1;"></p>
                    <div style="background:#f8f9fa; padding:15px; border-radius:8px; display:flex; justify-content:space-between; text-align:center; margin-top:20px;">
                        <div><span style="font-size:12px; color:#777;">Tarih/Saat</span><br><strong id="info-datetime"></strong></div><div><span style="font-size:12px; color:#777;">Kontenjan</span><br><strong id="info-capacity"></strong></div><div><span style="font-size:12px; color:#777;">Ücret</span><br><strong id="info-price" style="color:#6a89cc; font-size:18px;"></strong></div>
                    </div>
                    <div id="reservation-box" style="margin-top:15px; text-align:center; padding-top:15px; border-top:1px solid #eee;"></div>
                    <div id="summary-box" style="display:none; margin-top:15px; background:#e8effc; padding:20px; border-radius:8px; border:2px solid #6a89cc;">
                        <h3 style="margin-bottom:15px; color:#333;">📊 Yönetici Özet Raporu</h3>
                        <div style="display:flex; justify-content:space-between; text-align:center;">
                            <div><span style="font-size:12px; color:#555;">Satılan Bilet</span><br><strong id="sum-tickets" style="font-size:20px; color:#27ae60;"></strong></div>
                            <div><span style="font-size:12px; color:#555;">Toplam Gelir</span><br><strong id="sum-revenue" style="font-size:20px; color:#27ae60;"></strong></div>
                            <div><span style="font-size:12px; color:#555;">Genel Puan</span><br><strong id="sum-rating" style="font-size:20px; color:#f1c40f;"></strong></div>
                        </div>
                    </div>
                    <div style="margin-top:20px; border-top:1px solid #eee; padding-top:15px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;"><h3 style="font-size:14px; color:#555;">Kullanıcı Değerlendirmeleri</h3><select id="review-sort" onchange="renderReviews('info-reviews-container')" style="padding:2px 5px; border-radius:4px; font-size:12px; border:1px solid #ccc;"><option value="newest">En Yeni</option><option value="highest">En Yüksek Puanlı</option></select></div>
                        <div id="info-reviews-container" style="max-height: 120px; overflow-y: auto; background:#f9f9f9; padding:10px; border-radius:8px;">Yükleniyor...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>'''


def get_reservation_modal_html():
    return '''<div id="reservation-detail-modal" class="modal-overlay"><div class="modal-content" style="max-height: 90vh; overflow-y: auto;"><span class="close-btn" onclick="closeAnyModal('reservation-detail-modal')">&times;</span><div class="art-form-layout"><div class="art-upload-left" style="background:#000; border-radius:12px; overflow:hidden; max-height:400px;"><img id="res-img" src="" style="width:100%; height:100%; object-fit:cover;"></div><div class="art-details-right" style="display:flex; flex-direction:column;"><div class="user-info" style="margin-bottom:10px;"><span class="user-label" id="res-author" style="font-size:14px; font-weight:bold; color:#444;"></span></div><h2 id="res-title" style="margin:10px 0; font-size:26px;"></h2><div style="background:#f8f9fa; padding:15px; border-radius:8px; display:flex; justify-content:space-between; text-align:center; margin-top:10px;"><div><span style="font-size:12px; color:#777;">Tarih/Saat</span><br><strong id="res-datetime"></strong></div><div><span style="font-size:12px; color:#777;">Birim Ücret</span><br><strong id="res-price" style="color:#6a89cc; font-size:18px;"></strong></div></div><div id="res-management-area" style="margin-top:25px; padding:20px; border: 1px solid #eee; border-radius: 8px;"><h3 style="margin-bottom:15px; font-size:16px;">Rezervasyon Yönetimi</h3><div id="res-payment-area" style="text-align:center; margin-bottom:15px; padding-bottom:15px; border-bottom:1px dashed #ccc;"><button class="btn" style="background:#27ae60; padding:10px 30px; font-size:18px;" onclick="openPaymentModal('reservation', currentResId, currentResTotalPrice)">💳 Ödemeyi Tamamla</button></div><div id="res-update-area" style="display:flex; justify-content:space-between; align-items:center;"><div style="display:flex; align-items:center; gap:10px;"><label style="font-weight:bold; color:#555;">Kişi Sayısı:</label><input type="number" id="res-tickets-input" min="1" style="width:70px; padding:8px; border-radius:6px; border:1px solid #ccc;"></div><button class="btn" style="width:auto; padding:8px 20px; background:#6a89cc;" onclick="updateReservation()">Güncelle</button></div><div style="margin-top:20px; text-align:right;"><button class="btn" style="width:auto; padding:8px 20px; background:#ff4757;" onclick="cancelReservation()">İptal Et</button></div></div><div id="res-review-area" style="display:none; margin-top:20px; border-top:1px dashed #ccc; padding-top:20px;"><h3 style="font-size:16px; margin-bottom:15px; color:#27ae60;">🌟 Etkinliği Değerlendir</h3><div id="reviews-container" style="max-height: 150px; overflow-y: auto; margin-bottom:10px; background:#f9f9f9; padding:10px; border-radius:8px;"></div><div style="display:flex; gap:10px;"><select id="new-review-rating" style="padding:10px; border-radius:6px; border:1px solid #ccc;"><option value="5">5 ⭐</option><option value="4">4 ⭐</option><option value="3">3 ⭐</option><option value="2">2 ⭐</option><option value="1">1 ⭐</option></select><input type="text" id="new-review" placeholder="Deneyiminiz nasıldı? Yorum yazın..." style="flex-grow:1; padding:10px; border-radius:6px; border:1px solid #ccc;"><button class="btn" style="width:auto; padding:10px 15px; background:#27ae60;" onclick="postReview()">Gönder</button></div></div></div></div></div></div>'''


def get_payment_modal_html():
    return '''<div id="payment-modal" class="modal-overlay" style="z-index:3000;"><div class="modal-content" style="width: 400px; text-align:center;"><span class="close-btn" onclick="closeAnyModal('payment-modal')">&times;</span><h2 style="margin-bottom: 20px; color:#333;">💳 Güvenli Ödeme</h2><div style="background:#f4f4f9; padding:20px; border-radius:8px; margin-bottom:20px;"><p style="font-size:16px; color:#666; margin-bottom:5px;">Ödenecek Tutar</p><strong id="payment-amount" style="font-size:28px; color:#27ae60;"></strong></div>
    
    <div style="margin-bottom:20px; padding:0 20px;">
        <div style="display:flex; gap:10px;">
            <input type="text" id="coupon-code" placeholder="Kupon Kodu" style="flex-grow:1; padding:10px; border:1px solid #ccc; border-radius:6px;">
            <button class="btn" style="width:auto; padding:10px 15px; background:#6a89cc;" onclick="applyCoupon()">Uygula</button>
        </div>
        <p id="coupon-message" style="font-size:12px; margin-top:5px; display:none;"></p>
    </div>

    <div style="text-align:left; margin-bottom:20px; padding:0 20px;"><label style="display:block; margin-bottom:15px; font-size:16px; cursor:pointer;"><input type="radio" name="pay_method" checked style="transform:scale(1.2); margin-right:10px;"> Kredi / Banka Kartı</label><label style="display:block; font-size:16px; cursor:pointer;"><input type="radio" name="pay_method" style="transform:scale(1.2); margin-right:10px;"> Havale / EFT</label></div><button class="btn" style="background:#27ae60; width:100%; padding:15px; font-size:18px;" onclick="confirmPayment()">Onayla ve Öde</button></div></div>'''


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8080)

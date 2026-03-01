
import sqlite3
import os
DB_PATH = 'parking.db'
def ensure_db_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # إنشاء جدول users إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'operator'
    )''')
    # إنشاء جدول slots إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'free',
        car_number TEXT,
        user_id INTEGER
    )''')
    # إنشاء جدول revenue إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount INTEGER NOT NULL
    )''')
    # إنشاء جدول logs إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

ensure_db_tables()
import bcrypt
# إعادة تعيين كلمة مرور admin إلى admin123 دائماً
def reset_admin_password():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    hashed_admin = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute("UPDATE users SET password=?, role='admin' WHERE username='admin'", (hashed_admin,))
    conn.commit()
    conn.close()
reset_admin_password()
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash


app = Flask(__name__)
app.secret_key = 'smart-parking-secret-key'
DB_PATH = 'parking.db'

# --- Ensure DB migration: add user_id column if missing ---
def ensure_user_id_column():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(slots)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        try:
            c.execute('ALTER TABLE slots ADD COLUMN user_id INTEGER')
            conn.commit()
        except Exception:
            pass
    conn.close()

ensure_user_id_column()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[2]
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- Admin: Reset All Slots to Free ---
@app.route('/admin/reset_slots', methods=['POST'])
def reset_slots():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('غير مصرح', 'danger')
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE slots SET status='free', car_number=NULL")
    conn.commit()
    conn.close()
    flash('تم إعادة تعيين جميع المواقف إلى متاحة', 'success')
    return redirect(url_for('slots'))

# --- Car entry/exit route (fix for dashboard button) ---
@app.route('/slot/<int:slot_id>/toggle', methods=['POST'])
def slot_toggle(slot_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    # Allow admin, operator, and customer to toggle slot
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, car_number FROM slots WHERE id=?", (slot_id,))
    status = c.fetchone()
    if status:
        new_status = 'occupied' if status[0] == 'free' else 'free'
        car_number = request.form.get('car_number') if status[0] == 'free' else None
        hours = int(request.form.get('hours', 1)) if status[0] == 'free' else 0
        price_per_hour = 1000
        total_price = hours * price_per_hour
        from datetime import datetime, timedelta
        if new_status == 'occupied':
            # Restrict only customers to one active booking
            user_id = session.get('user_id') if role == 'customer' else None
            if role == 'customer':
                if not user_id:
                    flash('حدث خطأ في الجلسة. يرجى إعادة تسجيل الدخول.', 'danger')
                    conn.close()
                    return redirect(url_for('login'))
                c.execute("SELECT id FROM slots WHERE status='occupied' AND user_id=?", (user_id,))
                existing = c.fetchone()
                if existing:
                    flash('لا يمكنك حجز موقف آخر. لديك موقف محجوز بالفعل.', 'danger')
                    conn.close()
                    return redirect(url_for('dashboard'))
            # Car entry: require car_number
            if not car_number:
                flash('يرجى إدخال رقم السيارة', 'danger')
                conn.close()
                return redirect(url_for('dashboard'))
            entry_time = datetime.now()
            exit_time = entry_time + timedelta(hours=hours)
            # دائماً نخزن user_id إذا كان موجود (أي زبون)، ونخليه NULL إذا مشرف أو بدون مستخدم
            c.execute("UPDATE slots SET status=?, car_number=?, user_id=? WHERE id=?", (new_status, car_number, user_id, slot_id))
            # Add revenue only when car enters (slot becomes occupied)
            today = entry_time.strftime('%Y-%m-%d')
            c.execute("SELECT id, amount FROM revenue WHERE date=?", (today,))
            row = c.fetchone()
            if row:
                c.execute("UPDATE revenue SET amount=amount+? WHERE id=?", (total_price, row[0],))
            else:
                c.execute("INSERT INTO revenue (date, amount) VALUES (?, ?)", (today, total_price))
            # Store entry and exit time and total price in session for customer display
            session['entry_time'] = entry_time.strftime('%Y-%m-%d %H:%M')
            session['exit_time'] = exit_time.strftime('%Y-%m-%d %H:%M')
            session['slot_id'] = slot_id
            session['total_price'] = total_price
            flash(f'تم دخول السيارة. المجموع: {total_price} دينار', 'success')
        else:
            # Car exit: clear car_number and user_id for customers
            if role == 'customer':
                c.execute("UPDATE slots SET status=?, car_number=NULL, user_id=NULL WHERE id=?", (new_status, slot_id))
            else:
                c.execute("UPDATE slots SET status=?, car_number=NULL, user_id=NULL WHERE id=?", (new_status, slot_id))
        conn.commit()
        flash('تم تحديث حالة الموقف', 'success')
    else:
        flash('الموقف غير موجود', 'danger')
    conn.close()
    # Redirect to the correct dashboard based on role
    if role == 'customer':
        return redirect(url_for('dashboard'))
    return redirect(url_for('dashboard'))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'operator'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'free',
        car_number TEXT,
        user_id INTEGER
    )''')
    # Try to add columns if upgrading old DB
    try:
        c.execute('ALTER TABLE slots ADD COLUMN car_number TEXT')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE slots ADD COLUMN user_id INTEGER')
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount INTEGER NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        timestamp TEXT
    )''')
    hashed_admin = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_operator = bcrypt.hashpw('operator123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', hashed_admin, 'admin'))
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ('operator', hashed_operator, 'operator'))
    for i in range(1, 9):
        c.execute("INSERT OR IGNORE INTO slots (id, status) VALUES (?, ?)", (i, 'free'))
    conn.commit()
    # Removed misplaced booking logic from init_db()

@app.route('/logout')
def logout():
    username = session.get('username', 'غير معروف')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    from datetime import datetime
    c.execute("INSERT INTO logs (user, action, timestamp) VALUES (?, ?, ?)", (username, 'تسجيل الخروج', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, status, car_number FROM slots ORDER BY id")
    slots = c.fetchall()
    conn.close()
    # --- Late fee logic for customer ---
    if role == 'customer' and session.get('entry_time') and session.get('exit_time') and session.get('slot_id'):
        from datetime import datetime
        exit_time = datetime.strptime(session['exit_time'], '%Y-%m-%d %H:%M')
        now = datetime.now()
        if now > exit_time:
            late_hours = int((now - exit_time).total_seconds() // 3600) + 1
            late_fee_per_hour = 1000
            late_fee = late_hours * late_fee_per_hour
            if not session.get('late_fee_added'):
                session['total_price'] += late_fee
                session['late_fee'] = late_fee
                session['late_fee_added'] = True
                flash(f'انتهى وقتك وتمت إضافة رسوم تأخير: {late_fee} دينار', 'danger')
        else:
            session.pop('late_fee', None)
            session['late_fee_added'] = False
    if role == 'customer':
        return render_template('customer_dashboard.html', slots=slots, role=role)
    return render_template('dashboard.html', slots=slots, role=role)

@app.route('/slots', methods=['GET', 'POST'])
def slots():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    if role != 'admin':
        flash('هذه الصفحة متاحة فقط للمشرف', 'danger')
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        if slot_id:
            try:
                c.execute("INSERT OR IGNORE INTO slots (id, status) VALUES (?, ?)", (int(slot_id), 'free'))
                conn.commit()
                flash('تم إضافة الموقف بنجاح', 'success')
            except Exception:
                flash('حدث خطأ أثناء الإضافة', 'danger')
    c.execute("SELECT * FROM slots")
    slots = c.fetchall()
    conn.close()
    return render_template('slots.html', slots=slots)

@app.route('/slots/toggle/<int:slot_id>', methods=['POST'])
def slots_toggle(slot_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    if role != 'admin':
        flash('هذه الصفحة متاحة فقط للمشرف', 'danger')
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status FROM slots WHERE id=?", (slot_id,))
    status = c.fetchone()
    if status:
        new_status = 'occupied' if status[0] == 'free' else 'free'
        c.execute("UPDATE slots SET status=? WHERE id=?", (new_status, slot_id))
        conn.commit()
        flash('تم تحديث حالة الموقف', 'success')
    else:
        flash('الموقف غير موجود', 'danger')
    conn.close()
    return redirect(url_for('slots'))

@app.route('/slots/delete/<int:slot_id>', methods=['POST'])
def slots_delete(slot_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    if role != 'admin':
        flash('هذه الصفحة متاحة فقط للمشرف', 'danger')
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM slots WHERE id=?", (slot_id,))
    conn.commit()
    conn.close()
    flash('تم حذف الموقف بنجاح', 'success')
    return redirect(url_for('slots'))

@app.route('/users', methods=['GET', 'POST'])
def users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    if role != 'admin':
        flash('هذه الصفحة متاحة فقط للمشرف', 'danger')
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role_new = request.form.get('role')
        if username and password and role_new:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role_new))
                conn.commit()
                flash('تم إضافة المستخدم بنجاح', 'success')
            except sqlite3.IntegrityError:
                flash('اسم المستخدم موجود مسبقاً', 'danger')
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = session.get('username', '')
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        if new_password:
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, username))
            conn.commit()
            conn.close()
            flash('تم تحديث كلمة المرور بنجاح', 'success')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            from datetime import datetime
            c.execute("INSERT INTO logs (user, action, timestamp) VALUES (?, ?, ?)", (username, 'تغيير كلمة المرور', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
    return render_template('account.html', username=username)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role', 'operator')
    if role != 'admin':
        flash('هذه الصفحة متاحة فقط للمشرف', 'danger')
        return redirect(url_for('dashboard'))
    username = session.get('username', 'غير معروف')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    from datetime import datetime
    c.execute("INSERT INTO logs (user, action, timestamp) VALUES (?, ?, ?)", (username, 'دخول صفحة التحليلات', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute("SELECT date, SUM(amount) FROM revenue GROUP BY date ORDER BY date DESC LIMIT 7")
    data = c.fetchall()
    conn.commit()
    conn.close()
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return render_template('analytics.html', labels=labels, values=values)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Detect if request is from mobile
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(x in user_agent for x in ['android', 'iphone', 'ipad', 'mobile'])
    if not is_mobile:
        flash('إنشاء حساب متاح فقط من الموبايل', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # الدور دائماً زبون عند التسجيل من الموبايل
            role_new = 'customer'
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role_new))
                conn.commit()
                flash('تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن.', 'success')
                conn.close()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('اسم المستخدم موجود مسبقاً', 'danger')
                conn.close()
        else:
            flash('يرجى إدخال جميع الحقول', 'danger')
    return render_template('register.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # الدور دائماً زبون عند التسجيل من الموبايل
        role_new = 'customer'
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role_new))
            conn.commit()
            flash('تم إنشاء الحساب بنجاح! سجل دخولك الآن.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('اسم المستخدم موجود مسبقاً.', 'danger')
        finally:
            conn.close()
    return render_template('signup.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

# ตั้งค่าตำแหน่งไฟล์ฐานข้อมูล SQLite (สร้างในโฟลเดอร์ /tmp สำหรับ Vercel เพื่อให้อ่าน/เขียนไฟล์ได้)
DATABASE = '/tmp/todo_database.db' if os.environ.get('VERCEL') else 'todo_database.db'

def get_db():
    """ฟังก์ชันเชื่อมต่อฐานข้อมูล SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # ให้สามารถดึงข้อมูลแบบ Dictionary/Key ได้ง่าย
    return conn

def init_db():
    """ฟังก์ชันสร้างฐานข้อมูลและตารางเริ่มต้นโดยอัตโนมัติหากยังไม่มี"""
    with get_db() as conn:
        # 1. สร้างตารางผู้ใช้งาน
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        # 2. สร้างตารางบันทึกงาน Todo
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                done INTEGER DEFAULT 0,
                username TEXT,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # ใส่ข้อมูล Mock ข้อมูลแรกเข้าตาราง (ถ้ายังไม่มีข้อมูลใดๆ เลย)
        cursor = conn.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'password123'))
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('guest', 'guest123'))
            
            now_str = datetime.now().strftime('%Y-%m-%d')
            conn.execute('''
                INSERT INTO todos (title, description, start_date, end_date, done, username)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Deploy to Vercel', 'Fix SQLite Auto-creation database', now_str, now_str, 1, 'guest'))
            
            conn.execute('''
                INSERT INTO todos (title, description, start_date, end_date, done, username)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Review Portfolio Showcase', 'Test Full-Stack logic with SQLite', now_str, now_str, 0, 'guest'))
        conn.commit()

# เรียกใช้เพื่อเปิดแอปแล้วสร้างดสตาเบสทันที
init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM todos WHERE username = ?', (session['username'],))
        user_todos = cursor.fetchall()
        
    # ส่งค่า list เปล่าของ near_due_tasks และ overdue_tasks ไปด้วยเพื่อป้องกัน Template error
    return render_template('index.html', todos=user_todos, near_due_tasks=[], overdue_tasks=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user = cursor.fetchone()
            
        if user:
            session['username'] = username
            flash("Logged in successfully", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash("Username already exists", "error")
            else:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                flash("Registration successful! Please login.", "success")
                return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    title = request.form['title']
    description = request.form['description']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO todos (title, description, start_date, end_date, done, username)
            VALUES (?, ?, ?, ?, 0, ?)
        ''', (title, description, start_date, end_date, session['username']))
        conn.commit()
    
    flash("Task added successfully", "success")
    return redirect(url_for('index'))

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        if request.method == 'POST':
            conn.execute('''
                UPDATE todos 
                SET title = ?, description = ?, start_date = ?, end_date = ?
                WHERE id = ? AND username = ?
            ''', (request.form['title'], request.form['description'], request.form['start_date'], request.form['end_date'], task_id, session['username']))
            conn.commit()
            flash("Task updated successfully", "success")
            return redirect(url_for('index'))
        
        cursor = conn.execute('SELECT * FROM todos WHERE id = ? AND username = ?', (task_id, session['username']))
        task = cursor.fetchone()

    if task is None:
        flash("Task not found", "error")
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=task)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    with get_db() as conn:
        conn.execute('DELETE FROM todos WHERE id = ? AND username = ?', (task_id, session['username']))
        conn.commit()
        
    flash("Task deleted successfully", "success")
    return redirect(url_for('index'))

@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    with get_db() as conn:
        cursor = conn.execute('SELECT done FROM todos WHERE id = ? AND username = ?', (task_id, session['username']))
        task = cursor.fetchone()
        if task:
            new_status = 0 if task['done'] == 1 else 1
            conn.execute('UPDATE todos SET done = ? WHERE id = ?', (new_status, task_id))
            conn.commit()
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
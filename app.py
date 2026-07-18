from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 


def init_mock_db():
    """สร้าง Mock Data เริ่มต้นใน Session หากยังไม่มี"""
    if 'mock_users' not in session:

        session['mock_users'] = {
            'admin': 'password123',
            'guest': 'guest123'
        }
    if 'mock_todos' not in session:

        session['mock_todos'] = [
            {
                'id': 1,
                'title': 'Deploy to Vercel',
                'description': 'Fix Error 500 Internal Server Error by using Mock Session',
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'done': True,
                'username': 'guest'
            },
            {
                'id': 2,
                'title': 'Review Portfolio Showcase',
                'description': 'Test Full-Stack logic on the luxury gold theme site',
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'done': False,
                'username': 'guest'
            }
        ]
    if 'todo_id_counter' not in session:
        session['todo_id_counter'] = 3

@app.before_request
def before_request():
    init_mock_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_todos = [t for t in session['mock_todos'] if t['username'] == session['username']]
    return render_template('index.html', todos=user_todos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = session.get('mock_users', {})
        if username in users and users[username] == password:
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
        
        users = session.get('mock_users', {})
        if username in users:
            flash("Username already exists", "error")
        else:

            new_users = dict(users)
            new_users[username] = password
            session['mock_users'] = new_users
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
    
    current_counter = session.get('todo_id_counter', 1)
    
    new_task = {
        'id': current_counter,
        'title': title,
        'description': description,
        'start_date': start_date,
        'end_date': end_date,
        'done': False,
        'username': session['username']
    }
    
    todos = list(session.get('mock_todos', []))
    todos.append(new_task)
    session['mock_todos'] = todos
    session['todo_id_counter'] = current_counter + 1
    
    flash("Task added successfully", "success")
    return redirect(url_for('index'))

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    todos = list(session.get('mock_todos', []))
    task_index = next((i for i, t in enumerate(todos) if t['id'] == task_id), None)
    
    if task_index is None:
        flash("Task not found", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        todos[task_index]['title'] = request.form['title']
        todos[task_index]['description'] = request.form['description']
        todos[task_index]['start_date'] = request.form['start_date']
        todos[task_index]['end_date'] = request.form['end_date']
        
        session['mock_todos'] = todos
        flash("Task updated successfully", "success")
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=todos[task_index])

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    todos = list(session.get('mock_todos', []))
    # กรองเอา Task ที่มี ID ตรงกันออกไป
    filtered_todos = [t for t in todos if t['id'] != task_id]
    
    session['mock_todos'] = filtered_todos
    flash("Task deleted successfully", "success")
    return redirect(url_for('index'))

@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    todos = list(session.get('mock_todos', []))
    for t in todos:
        if t['id'] == task_id:
            t['done'] = not t['done']
            break
            
    session['mock_todos'] = todos
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
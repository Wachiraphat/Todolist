from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
 
# ตั้งค่า Flask และฐานข้อมูล
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # ต้องกำหนด secret key สำหรับ session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'  # ใช้ฐานข้อมูล todo.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # ปิดการติดตามการแก้ไขเพื่อประหยัดทรัพยากร
 
db = SQLAlchemy(app)
 
# สร้าง Model สำหรับ User และ Todo
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    todos = db.relationship('Todo', backref='owner', lazy=True)
 
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
 
# สร้างฐานข้อมูลและตาราง
with app.app_context():
    db.create_all()
 
# Route สำหรับหน้า Welcome
@app.route('/')
def welcome():
    return render_template('welcome.html')
 
# Route สำหรับการลงทะเบียนผู้ใช้
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
       
        # ตรวจสอบว่าผู้ใช้มีอยู่ในฐานข้อมูลหรือไม่
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return redirect(url_for('register'))

        # ตรวจสอบว่า password และ confirm_password ตรงกันหรือไม่
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('register'))
       
        # เพิ่มผู้ใช้ใหม่ในฐานข้อมูล
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
       
        flash("Registration successful", "success")
        return redirect(url_for('login'))
 
    return render_template('register.html')

 
# Route สำหรับการล็อกอิน
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))  # ถ้าผู้ใช้ล็อกอินแล้วให้ไปที่หน้าหลัก
 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
       
        # ค้นหาผู้ใช้จากฐานข้อมูล
        user = User.query.filter_by(username=username).first()
 
        # ตรวจสอบรหัสผ่าน
        if user and user.password == password:
            session['username'] = username  # บันทึกชื่อผู้ใช้ใน session
            flash("Login successful", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))
 
    return render_template('login.html')
 
# Route สำหรับการออกจากระบบ
@app.route('/logout')
def logout():
    session.pop('username', None)  # ลบชื่อผู้ใช้ใน session
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))  # กลับไปที่หน้า Login
 
# Route สำหรับหน้าแสดงรายการ To-Do
@app.route('/index')
def index():
    if 'username' not in session:  # ถ้ายังไม่ล็อกอินให้ไปที่หน้า Login
        return redirect(url_for('login'))
 
    user = User.query.filter_by(username=session['username']).first()  # ค้นหาผู้ใช้
    todos = Todo.query.filter_by(user_id=user.id).all()  # ดึงทูโดทั้งหมดของผู้ใช้จากฐานข้อมูล
 
    # ตรวจสอบวันที่ของแต่ละ task
    near_due_tasks = []
    overdue_tasks = []
    today = datetime.today().date()
 
    # ตรวจสอบงานที่ใกล้ครบกำหนด (2 วันก่อนกำหนด)
    for todo in todos:
        end_date = todo.end_date
       
        # งานที่ใกล้ครบกำหนด (2 วันก่อนกำหนด)
        if end_date - today <= timedelta(days=2) and not todo.done:
            near_due_tasks.append(todo)
       
        # งานที่เลยกำหนด
        if end_date < today and not todo.done:
            overdue_tasks.append(todo)
 
    return render_template('index.html', todos=todos, near_due_tasks=near_due_tasks, overdue_tasks=overdue_tasks)
 
# Route สำหรับการเพิ่ม To-Do ใหม่
@app.route('/add', methods=['POST'])
def add_task():
    if 'username' not in session:  # ถ้ายังไม่ล็อกอิน
        return redirect(url_for('login'))
 
    title = request.form['title']
    description = request.form['description']
    start_date = datetime.strptime(request.form['start_date'], "%Y-%m-%d").date()
    end_date = datetime.strptime(request.form['end_date'], "%Y-%m-%d").date()
 
    # ค้นหาผู้ใช้จาก session
    user = User.query.filter_by(username=session['username']).first()
 
    # เพิ่ม To-Do ใหม่ในฐานข้อมูล
    new_task = Todo(
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        done=False,
        user_id=user.id  # เก็บ user_id ของผู้ใช้ที่เพิ่ม To-Do
    )
    db.session.add(new_task)
    db.session.commit()
 
    flash("Task added successfully", "success")
    return redirect(url_for('index'))
 
# Route สำหรับการเปลี่ยนสถานะของ To-Do
@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    if 'username' not in session:  # ถ้ายังไม่ล็อกอิน
        return redirect(url_for('login'))
 
    # ค้นหา To-Do จากฐานข้อมูล
    task = Todo.query.get(task_id)
    if task:
        task.done = not task.done  # เปลี่ยนสถานะของ To-Do
        db.session.commit()
        flash("Task status updated", "success")
    else:
        flash("Task not found", "error")
   
    return redirect(url_for('index'))

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:  # ถ้ายังไม่ล็อกอิน
        return redirect(url_for('login'))

    # ค้นหา To-Do จากฐานข้อมูล
    task = Todo.query.get(task_id)
    if not task:
        flash("Task not found", "error")
        return redirect(url_for('index'))

    # ถ้าเป็นการ submit ฟอร์ม
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.start_date = datetime.strptime(request.form['start_date'], "%Y-%m-%d").date()
        task.end_date = datetime.strptime(request.form['end_date'], "%Y-%m-%d").date()

        db.session.commit()
        flash("Task updated successfully", "success")
        return redirect(url_for('index'))

    # ถ้าเป็นการเข้าไปที่หน้า edit โดยตรง ให้แสดงฟอร์ม
    return render_template('edit_task.html', task=task)
 
# Route สำหรับการลบ To-Do
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session:  # ถ้ายังไม่ล็อกอิน
        return redirect(url_for('login'))
 
    # ค้นหา To-Do จากฐานข้อมูล
    task = Todo.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully", "success")
    else:
        flash("Task not found", "error")
   
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
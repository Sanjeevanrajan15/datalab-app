from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import re, hashlib
from werkzeug.utils import secure_filename
import os
import pandas as pd

app = Flask(__name__)

# Set the secret key (used for both hashing and sessions)
secret_key = 'your_secret_key'
app.secret_key = secret_key

# MySQL connection
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Saranya@26',
    database='pythonlogin',
    cursorclass=pymysql.cursors.DictCursor
)

# CSV folder paths
ORIGINAL_FOLDER = 'uploads/original'
CLEANED_FOLDER = 'uploads/cleaned'

# Make folders if they don't exist
os.makedirs(ORIGINAL_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

app.config['ORIGINAL_FOLDER'] = ORIGINAL_FOLDER
app.config['CLEANED_FOLDER'] = CLEANED_FOLDER

# Allow only CSV files
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Data cleaning function
def clean_csv(original_path):
    df = pd.read_csv(original_path)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.drop_duplicates(inplace=True)
    df.dropna(how='all', inplace=True)

    cleaned_filename = "cleaned_" + os.path.basename(original_path)
    cleaned_path = os.path.join(CLEANED_FOLDER, cleaned_filename)
    df.to_csv(cleaned_path, index=False)

    return cleaned_filename, df


@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        print("Login attempt:")
        print("Username:", username)

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
            account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = f"Logged in successfully! Welcome, {account['username']}."
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
            print("Login failed.")

    return render_template('index.html', msg=msg)

# localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
   
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)

   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()

            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                # Hash password
                hash = hashlib.sha1((password + app.secret_key).encode()).hexdigest()
                cursor.execute('INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)', (username, hash, email))
                connection.commit()
                msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    
    return render_template('register.html', msg=msg)

# localhost:5000/pythinlogin/home - this will be the home page, only accessible for logged in users
@app.route('/pythonlogin/home')
def home():
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for logged in users
@app.route('/pythonlogin/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
            account = cursor.fetchone()
            # Show the profile page with account info
            return render_template('profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

@app.route('/pythonlogin/upload', methods=['GET', 'POST'])
def upload():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    msg = ''
    uploads = []
    tables = []
    cleaned_filename = ''

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        
        if uploaded_file and uploaded_file.filename.endswith('.csv'):
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config['ORIGINAL_FOLDER'], filename)
            uploaded_file.save(file_path)

            try:
                # Link file to user in DB
                with connection.cursor() as cursor:
                    sql = """INSERT INTO uploads (user_id, filename, upload_path)
                             VALUES (%s, %s, %s)"""
                    cursor.execute(sql, (session['id'], filename, file_path))
                    connection.commit()

                # Clean and display CSV
                cleaned_filename, df = clean_csv(file_path)
                tables = [df.to_html(classes='table table-bordered', index=False)]
                msg = 'File uploaded, cleaned, and linked to your account!'
            except Exception as e:
                connection.rollback()
                msg = f"Upload failed: {str(e)}"
        else:
            msg = 'Invalid file type. Only CSVs are allowed.'

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT filename, upload_time 
                FROM uploads 
                WHERE user_id = %s 
                ORDER BY upload_time DESC
            """, (session['id'],))
            uploads = cursor.fetchall()
    except Exception as e:
        msg += f" | Failed to fetch uploads: {str(e)}"

    return render_template('upload.html', msg=msg, uploads=uploads, tables=tables, cleaned_filename=cleaned_filename)

if __name__ == "__main__":
    app.run(debug=True)

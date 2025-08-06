from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import re, hashlib

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
def upload():     # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
            account = cursor.fetchone()
            # Show the profile page with account info
            return render_template('upload.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))  

if __name__ == "__main__":
    app.run(debug=True)

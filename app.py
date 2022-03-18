######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import email
from re import search
from tkinter import S
from unicodedata import name
import flask
from flask import Flask, Response, flash, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Y123456'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

### 					  ###
# User Login & Registration #
###						  ###

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html',message='Welecome to Photoshare!')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route('/userprofile', methods=['GET'])
@flask_login.login_required
def protected():
	email = flask_login.current_user.id
	uid = getUserIdFromEmail(email)
	# friend_list = getFriendSuggestion()
	return render_template('hello.html', name = email, albums = getUsersAlbums(uid),
							photos = getUsersPhotos(uid), )

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		gender = request.form.get('gender')
		dob = request.form.get('dob')
		hometown = request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, fname, lname, gender, dob, hometown) \
		VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(email, password, fname, lname, gender, dob, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return flask.redirect(flask.url_for('protected'))
	else:
		print('Account exists!')
		return flask.redirect(flask.url_for('register'))


# Functions to get user data
def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

@app.route("/search_friend", methods=['GET', 'POST'])
@flask_login.login_required
def search_friends():
	if request.method == 'POST':
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		cursor = conn.cursor()
		cursor.execute("SELECT fname, lname FROM Users \
						WHERE fname LIKE %s AND lname LIKE %s",(fname, lname))
		search = cursor.fetchall()
	return render_template("search_friend.html", searchs = search)

# def getUserNameFromEmail(email):
# 	cursor = conn.cursor()
# 	cursor.execute("SELECT fname,lname FROM Users WHERE email = '{0}'".format(email))
# 	return cursor.fetchone()[0]
#end login code


###
# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
###
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/create_album", methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aname = request.form.get('aname')
		date = request.form.get('date')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (aname, creation_date, user_id) \
			VALUES (%s, %s, %s)''',(aname,date,uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, 
								message='Album Created!')
	else:
		return render_template('create_album.html')

@app.route("/delete_album", methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aname = getAlbumNameFromAlbums(uid)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Albums WHERE aname = '{0}'".format(aname))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, 
								message='Album Deleted!')
	else:
		return render_template('delete_album.html')

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aid = getAlbumIdFromUsers(uid)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption, albums_id) \
			        	VALUES (%s, %s, %s, %s)''', (photo_data, uid, caption, aid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, 
								message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')

@app.route('/show_photo', methods=['GET', 'POST'])
@flask_login.login_required
def show_photo():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	aid = getAlbumIdFromUsers(uid)
	cursor = conn.cursor()
	cursor.execute("SELECT data, caption FROM Photos WHERE user_id = '{0}'".format(aid))
	return render_template('show_photo.html', name = getAlbumNameFromAlbums(uid), photos=getUsersPhotos(uid))
	
def getAlbumIdFromUsers(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getAlbumNameFromAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()


#end photo uploading code


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

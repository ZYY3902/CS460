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

from cgi import test
from dataclasses import dataclass
from getpass import getuser
import re
from tkinter.tix import ListNoteBook
from xml.etree.ElementTree import Comment
import flask
from flask import Flask, Response, flash, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

from matplotlib.pyplot import text


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

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare',)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <a href='/'>Home</a>
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
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

@app.route('/userprofile', methods=['GET'])
@flask_login.login_required
def protected():
	email = flask_login.current_user.id
	uid = getUserIdFromEmail(email)
	return render_template('hello.html', message="Here's your profile", name = email, albums = getUsersAlbums(uid),
							photos = getUsersPhotos(uid), base64 = base64,
							friends = getUserFriends(uid), friends_recommendation = friends_recommendation(),
							tags = getTagsNameUsedByUser(uid), userActivitys = userActivity())

# Functions in the template
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
# End of the template functions

def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname FROM Users \
					WHERE user_id IN (SELECT user_id2 \
									 FROM Friends \
									 WHERE user_id1 = '{0}')".format(uid))
	return cursor.fetchall()

def getUserFriendsId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 ='{0}'".format(uid))
	return cursor.fetchone()[0]

@app.route("/search_friend", methods=['GET', 'POST'])
@flask_login.login_required
def search_friends():
	if request.method == 'POST':
		email = request.form.get('email')
		cursor.execute("SELECT fname, lname from Users WHERE email = '{0}'".format(email))
		data = cursor.fetchall()
		return render_template("search_friend.html", searchs = data)
	else:
		return render_template("search_friend.html")

@app.route("/add_friend", methods=['POST'])
@flask_login.login_required
def add_friend():
	uid1 = getUserIdFromEmail(flask_login.current_user.id)
	friend_email = request.form.get('friend_email')
	uid2 = getUserIdFromEmail(friend_email)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) \
					VALUES (%s, %s)", (uid1, uid2))
	conn.commit()
	return flask.redirect(flask.url_for('protected'))

def friends_recommendation():
	uid1 = getUserIdFromEmail(flask_login.current_user.id)
	fid = getUserFriendsId(uid1)
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname, email FROM Users \
					WHERE user_id IN (SELECT user_id2 FROM Friends \
									  WHERE user_id1 = '{0}')".format(fid))
	return cursor.fetchall()
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
		aid = getAlbumIdFromUsers(uid)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE albums_id = '{0}'".format(aid))
		cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(aid))
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

@app.route('/show_photo/<tag_name>', methods=['GET', 'POST'])
@flask_login.login_required
def show_photo(tag_name):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	tid = getTagIdFromTagName(tag_name)
	cursor = conn.cursor()
	cursor.execute("SELECT data, caption FROM Photos WHERE  = '{0}'".format(uid))
	return 

@app.route("/delete_photo", methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = getPhotoIdFromPhotos(uid)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, 
								message='Photo Deleted!')
	else:
		return render_template('delete_photo.html')	


# helper func check if a tag already exists
def checkTagExist(word):
	cursor = conn.cursor()
	if cursor.execute("SELECT word FROM Tags WHERE word = '{0}'".format(word)):
		return True
	else:
		return False

@app.route("/create_tag", methods=['GET', 'POST'])
@flask_login.login_required
def create_tag():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		word = request.form.get('word')
		if checkTagExist(word):
			return render_template('hello.html', name=flask_login.current_user.id, 
									message='Tag Already Exists!')
		else:
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Tags (word) VALUES (%s)''',(word))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, 
        								message='Tag Created!')
	else:
  		return render_template('create_tag.html')

@app.route("/add_tag", methods=['GET', 'POST'])
@flask_login.login_required
def add_tag():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = getPhotoIdFromPhotos(uid)
		tag_name = request.form.get('tag_name')
		tid = getTagIdFromTagName(tag_name)
		if checkTagExist(tag_name):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES(%s, %s)",(pid, tid))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, 
									message='Tag Added!')
		else:
			return render_template("create_tag.html", message = "Tag not exist")
	else:
		return render_template('add_tag.html')	

def getAlbumIdFromUsers(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]
	
def getPhotoIdFromPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getTagIdFromTagName(tag_name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE word = '{0}'".format(tag_name))
	return cursor.fetchall()

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getPhotoTagsFromUID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tags WHERE tag_id = (SELECT tag_id \
														  FROM Tagged \
														  WHERE photo_id = \
														  (SELECT photo_id FROM Photos \
														   WHERE user_id ='{0}'))".format(uid))
	return cursor.fetchall()

def getTagsNameUsedByUser(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tags WHERE tag_id IN \
					(SELECT tag_id FROM Tagged WHERE photo_id IN \
					(SELECT photo_id FROM Photos WHERE user_id = '{0}'))".format(uid))
	return cursor.fetchall()

# function not in use #
def getAlbumNameFromAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def isOwnPhoto(pid, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT photo_id FROM Photos \
					   WHERE photo_id = '{0}' AND user_id = '{1}'".format(pid, uid)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def publicPhotosInfoFromPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id ,caption, user_id FROM Photos \
					ORDER BY photo_id ASC")
	data = cursor.fetchall()
	photo = [(i[0], i[1], i[2]) for i in data]
	return photo

def getLikes():
	likes = []
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos \
					ORDER BY photo_id ASC")
	data = cursor.fetchall()
	pid = [i[0] for i in data]
	for p in pid:
		cursor.execute("SELECT photo_id, COUNT(user_id) FROM Likes WHERE photo_id = '{0}'".format(p))
		like = cursor.fetchone()
		likes.append(like)
	num = [(i[0], i[1]) for i in likes]
	return num

def getComments():
	likes = []
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos \
					ORDER BY photo_id ASC")
	data = cursor.fetchall()
	pid = [i[0] for i in data]
	for p in pid:
		cursor.execute("SELECT photo_id, text FROM Comments WHERE photo_id = '{0}'".format(p))
		like = cursor.fetchone()
		likes.append(like)
	comment = [i for i in likes]
	return comment

@app.route("/public", methods=['GET'])
def public():
	return render_template('public.html', message='Welecome to Photoshare',
			photos=publicPhotosInfoFromPhotos(), base64=base64, likes=getLikes(), comments=getComments())

@app.route("/add_comment", methods=['POST'])
def add_comment():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		text = request.form.get('text')
		pid = request.form.get('pid')
		comment_date = request.form.get('comment_date')
		if isOwnPhoto(pid, uid):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (text, comment_date, user_id, photo_id) \
						    VALUES (%s, %s, %s, %s)", (text, comment_date, uid, pid ))
			conn.commit()
			return render_template("public.html", 
									message = "Comment Added!",
									photos = publicPhotos(), base64=base64)
		else:
			return render_template("public.html", 
									message = "You cannot comment on your own photo! Please choose another photo!",
									photos = publicPhotos(), base64=base64)

@app.route("/add_like", methods=['POST'])
@flask_login.login_required
def add_like():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.form.get('pid')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Likes (photo_id, user_id) \
						    VALUES (%s, %s)", (pid, uid))
		conn.commit()
		return render_template("public.html", 
									message = "Like Added!",
									photos = publicPhotos(), base64=base64)

def getUsersNameFromUID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname FROM Users \
					WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()


@app.route("/search_comment", methods=['GET', 'POST'])
@flask_login.login_required
def search_comment():
	if request.method == 'POST':
		text = request.form.get('text')
		cursor.execute("SELECT user_id, COUNT(*) AS counter FROM Comments\
						WHERE text LIKE '%{0}%' \
						GROUP BY user_id \
						ORDER BY counter DESC".format(text))
		data = cursor.fetchall() #(user_id, counter), (2,1)
		for i in data:
			name = getUsersNameFromUID(i[0])
		return render_template("search_comment.html", names = name)
	else:
		return render_template("search_comment.html")

def userActivity():
	cursor = conn.cursor()
	sql = "SELECT t1.fname, t1.lname, SUM(t1.sum) AS Total \
		   FROM ( \
		   SELECT Users.fname, Users.lname, COUNT(photo_id) AS sum FROM Photos, Users WHERE Photos.user_id = Users.user_id GROUP BY Users.user_id \
		   UNION ALL \
		   SELECT Users.fname, Users.lname, COUNT(comment_id) AS sum FROM Comments, Users WHERE Comments.user_id = Users.user_id GROUP BY Users.user_id \
		   )t1\
		   GROUP BY t1.fname, t1.lname \
		   ORDER BY Total DESC LIMIT 10"
	cursor.execute(sql)
	return cursor.fetchall()
#end photo uploading code


if __name__ == "__main__":
	#this is invoked when in the shell  you run	
	#$ python app.py
	app.run(port=5000, debug=True)

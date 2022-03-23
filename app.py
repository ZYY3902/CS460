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
							userActivitys = userActivity(), tags = getTagNameFromUID(uid), 
							pid_of_added_tag = None)

# Functions to get user data
def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersName(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

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

@app.route("/add_tag2/<int:pid>", methods=['GET', 'POST'])
@flask_login.login_required
def add_tag2(pid):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tag_name = request.form.get('tag_name')
		tid = getTagIdFromTagName(tag_name)
		if checkTagExist(tag_name):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES(%s, %s)",(pid, tid))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, 
									message='Tag Added!')#, pid_of_added_tag= pid)
		else:
			return render_template("create_tag.html", message = "Tag not exist")
	else:
		return render_template('add_tag.html', base64 = base64, photo_id = pid)	

@app.route("/add_tag", methods=['GET', 'POST'])
@flask_login.login_required
def add_tag():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.form.get('photo_id')
		tag_name = request.form.get('tag_name')
		tid = getTagIdFromTagName(tag_name)
		if checkTagExist(tag_name):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES(%s, %s)",(pid, tid))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, 
									message='Tag Added!')#, pid_of_added_tag= pid)
		else:
			return render_template("create_tag.html", message = "Tag not exist")
	else:
		return render_template('add_tag.html')	

@app.route("/show_photo_tags/<pid>", methods=['GET', 'POST'])
def displayPhotoTags(pid):
   if request.method == 'POST':
       uid = getUserIdFromEmail(flask_login.current_user.id)

       cursor = conn.cursor()
       cursor.execute('''SELECT word FROM Tags \
                           WHERE tag_id IN (SELECT tag_id FROM Tagged \
							   WHERE photo_id = (SELECT photo_id FROM Photos \
								   WHERE photo_id = {0}))'''.format(pid))
       conn.commit()
       return render_template(template_name_or_list)                
   else:
       return render_template('tag_album_all.html')


@app.route("/tag_album_all/<tag_name>", methods=['GET', 'POST'])
def all_tag_album(tag_name):
	if flask_login.current_user.id:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('tag_album_all.html', Name=flask_login.current_user.id, Tag=tag_name, 
												TagPhotos= displayTagAlbumAll(tag_name), base64=base64)

@app.route("/tag_album_user/<tag_name>")
def user_tag_album(tag_name):
		if flask_login.current_user.id:
			uid = getUserIdFromEmail(flask_login.current_user.id)

		return render_template('tag_album_user.html', Name=flask_login.current_user.id, Tag=tag_name, 
													TagPhotos= displayTagAlbumUser(uid, tag_name), base64=base64)	

def displayTagAlbumUser(uid, tag_name):
	tid = getTagIdFromTagName(tag_name)[0][0]
	#print(tid)
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE (user_id = '{1}' AND photo_id IN \
	   (SELECT photo_id FROM Tagged WHERE tag_id = '{0}') )".format(tid, uid))
	conn.commit()
	return cursor.fetchall()

def displayTagAlbumAll(tag_name):
	tid = getTagIdFromTagName(tag_name)[0][0]
	#print(tid)
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE (photo_id IN \
	   (SELECT photo_id FROM Tagged WHERE tag_id = '{0}') )".format(tid))
	conn.commit()
	return cursor.fetchall()

	########################

@app.route("/popular_tags", methods= ['GET', 'POST'])
def find_popular_tags():
	#uid = getUserIdFromEmail(flask_login.current_user.id)
	popular_tags = find_popular_t()
	tags = []
	for tag in popular_tags:
		tag = de_tuple(tag[0])
		tags.append(tag)

	return render_template('popular_tags.html', Popular_Tags= tags)

def find_popular_tid():
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM \
							(SELECT tag_id, COUNT(photo_id) FROM Tagged \
								GROUP BY tag_id \
									ORDER BY COUNT(photo_id) DESC \
										LIMIT 3 ) AS S")
	return cursor.fetchall()

def find_popular_t():
	popular_tag_ids = find_popular_tid()
	tags = []
	for id in popular_tag_ids:
		tags.append(
			getTagNameFromTageID(
				de_tuple(id)
			)
		)

	return tags

	########################

@app.route("/search_photos_with_tags", methods= ['GET', 'POST'])
def photo_search_w_tag():
	if request.method == 'POST':
		conjunctive_tags = request.form.get('conjunctive_tags')

		tags = breakIntoTagList(conjunctive_tags)

		first_tag = tags[0]
		rest_tag = tags[1:]
		#print(first_tag)
		#print(rest_tag)

		rawList = getAllPhotoIDFromTagName(first_tag)
		#print(rawList)
		AllList = []
		tempList = []
		for id in rawList:
			AllList.append(id[0])
		#print('first tag list of pid')
		#print(AllList)
		if len(rest_tag) != 0:
			for tag in rest_tag:
				restrawList = getAllPhotoIDFromTagName(first_tag)
				for rest_id in restrawList:
					tempList.append(rest_id[0])
				for n in tempList:
					if n not in AllList:
						tempList.remove(n)
				AllList = tempList
				#print('rest tag list of pid updates')
				#print(AllList)

		AllPhoto = []
		for i in AllList:
			AllPhoto.append(getPhotoFromPhotoID(i)[0])
			
		#print('now test if actual data is selected:')
		#print(AllPhoto)
		
		return render_template('show_photos_w_tags.html', Tags= conjunctive_tags, Photos= AllPhoto, base64= base64)
	else:
		return render_template('search_photos_w_tags.html')


def breakIntoTagList(tag_string):
	List = tag_string.split()
	return List

################################

@app.route("/getRecByTags", methods= ['GET', 'POST'])
@flask_login.login_required
def rec_by_most_used_tag():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	popular_tags = get5PopularTag(uid)
	print(popular_tags)

	PhotosTag1 = []; tag1 = popular_tags[0]
	PhotosTag2 = []; tag2 = popular_tags[1]
	PhotosTag3 = []; tag3 = popular_tags[2]
	PhotosTag4 = []; tag4 = popular_tags[3]
	PhotosTag5 = []; tag5 = popular_tags[4]

	if checkTagExist(tag1):
		photoid1 = getAllPhotoIDFromTagName(tag1)
		#PhotosTag1 = [getPhotoFromPhotoID(de_tuple(id) for item in photoid1


	return render_template('get_rec_by_tags.html', Photos1= PhotosTag1, Photos2= PhotosTag2, Photos3= PhotosTag3, 
											Photos4= PhotosTag4, Photos5= PhotosTag5, base64= base64)




def checkTagNotNull(tag_name):
	return (tag_name != "-1")

def get5PopularTagIDUser(uid):
	cursor = conn.cursor()
	cursor.execute("(SELECT DISTINCT tag_id FROM Tagged INNER JOIN \
						Photos WHERE user_id = '{0}' \
							GROUP BY tag_id \
								ORDER BY COUNT(Photos.photo_id) DESC \
									LIMIT 5) ".format(uid) )
	return cursor.fetchall()

def get5PopularTag(uid):
	Id_list = get5PopularTagIDUser(uid)
	Ids = []
	for i in Id_list:
		id = de_tuple(getTagNameFromTageID(i))
		Ids.append(id)

	if len(Ids) < 5:
		for num in range(1,(5-len(Ids)+1)):
			Ids.append("-1")

	print(Ids)

	return Ids





#############################
def de_tuple(tup):
	return tup[0]

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getAlbumIdFromUsers(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getAlbumNameFromAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getPhotoIdFromPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getAllPhotoIDFromUID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos WHERE user_id = '{0}' ".format(uid) )
	return cursor.fetchall()

def getAllPhotoIDFromTagName(tag_name):
	tid = getTagIdFromTagName(tag_name)[0][0]
	print(tid)
	allphoto = getAllPhotoIDFromTagID(tid)
	print('the length of the list of pid with same tid:')
	print(len(allphoto))
	return allphoto

def getAllPhotoIDFromTagID(tid):
	print(tid)
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos WHERE photo_id IN \
						(SELECT photo_id FROM Tagged WHERE tag_id = '{0}')".format(tid) )
	return cursor.fetchall()

def getPhotoFromPhotoID(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = '{0}'".format(pid) )
	return cursor.fetchall()



def getTagIdFromTagName(tag_name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE word = '{0}'".format(tag_name))
	return cursor.fetchall()#[0][0]

def getTagNameFromPhotoID(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tags WHERE tag_id IN (SELECT tag_id FROM Tagged WHERE photo_id ='{0}')".format(pid) )
	return cursor.fetchall()

def getTagIDFromPhotoID(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tagged WHERE photo_id = '{0}'".format(str(pid)))
	return cursor.fetchall()

def getTagNameFromUID(uid): # the version using for-loop is extremely inefficient !!!
	Pids = getAllPhotoIDFromUID(uid)

	AllTags = []
	#Pids.remove((None,""))
	for pid in Pids:
		#print (pid)
		tid = getTagNameFromPhotoID(de_tuple(pid))
		#print (tid)
		for tag_tuple in tid:
			tag = de_tuple(tag_tuple)
			if (tag not in AllTags):
				AllTags.append(tag)

	#print(AllTags)

	return AllTags

def getTagNameFromTageID(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tags WHERE tag_id = '{0}'".format(tag))
	return cursor.fetchall()


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
	num_likes = [(i[0], i[1]) for i in likes]
	return num_likes

def getLikesUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT Likes.photo_id, Users.fname, Users.lname \
						FROM Likes INNER JOIN Users on Likes.user_id = Users.user_id \
						ORDER BY Likes.photo_id ASC")
	users = cursor.fetchall()
	names_users = [(i[0], i[1], i[2]) for i in users]
	return names_users

def getComments():
	comments = []
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photos \
					ORDER BY photo_id ASC")
	data = cursor.fetchall()
	pid = [i[0] for i in data]
	for p in pid:
		cursor.execute("SELECT text FROM Comments WHERE photo_id = '{0}'".format(p))
		comment = cursor.fetchone()
		comments.append(comment)
	com = [i for i in comments]
	return com

@app.route("/public", methods=['GET'])
def public():
	cursor = conn.cursor()
	cursor.execute("SELECT Albums.aname, Users.fname, Users.lname FROM Albums, Users \
					WHERE Albums.user_id = Users.user_id\
					ORDER BY Users.user_id ASC")
	data = cursor.fetchall()
	albums = [(i[0], i[1], i[2]) for i in data]
	return render_template('public.html', message='Welecome to Photoshare',
			photos=publicPhotosInfoFromPhotos(), base64=base64, likes=getLikes(), comments=getComments(),
			albums=albums, users=getLikesUsers())

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
									photos=publicPhotosInfoFromPhotos(), base64=base64)
		else:
			return render_template("public.html", 
									message = "You cannot comment on your own photo! Please choose another photo!",
									photos=publicPhotosInfoFromPhotos(), base64=base64)

@app.route("/add_like", methods=['POST'])
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
									photos=publicPhotosInfoFromPhotos(), base64=base64)

def getUsersNameFromUID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname FROM Users \
					WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()


@app.route("/search_comment", methods=['GET', 'POST'])
@flask_login.login_required
def search_comment():
	names = []
	if request.method == 'POST':
		text = request.form.get('text')
		cursor.execute("SELECT user_id, COUNT(*) AS counter FROM Comments\
						WHERE text LIKE '%{0}%' \
						GROUP BY user_id \
						ORDER BY counter DESC".format(text))
		data = cursor.fetchall() #(user_id, counter), (2,1)
		for i in data:
			name = getUsersNameFromUID(i[0])
			names.append(name)
		return render_template("search_comment.html", names = names)
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

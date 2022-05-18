from builtins import classmethod, len, print
import flask
from flask import Flask, redirect, render_template, abort, request, request_started, url_for, send_from_directory 
from flask_login import LoginManager, current_user, login_user, login_required, logout_user 
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, IntegerField,TextAreaField 
# from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename 
from werkzeug.exceptions import RequestEntityTooLarge
from urllib.parse import urlparse, urljoin
import database
import json
import os  
import PIL.Image as Image



app = Flask(__name__, template_folder='templates', static_url_path = '/static')
app.config['UPLOAD_DIRECTORY'] = 'static/upload/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16mb
app.config['ALLOWED_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
login_manager = LoginManager()
# auth = HTTPBasicAuth()
login_manager.init_app(app)
db = database.SqliteDBnexDatabase()
# users = {
#    "lamar": generate_password_hash("lamar"),
#    "shanks": generate_password_hash("shanks")
# }
 
app.secret_key = b'jkrg,fjfvklsvsjkhvbjknvjknvhjbsfbshvbhjv09886-3'


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

class User():

    def __init__(self, id):
        self.id = id

    def is_authenticated(self):
        return True

    def is_active():
        return True

    def is_anonymous():
        return False

    def get_id(self):
        return self.id

    @classmethod 
    def get(cls,id):
       return User(id)

class LoginForm(FlaskForm):
 username = StringField('Username')
 password = PasswordField('Password')
 submit = SubmitField('Submit')

class signUpForm(FlaskForm):
 username = StringField('Username')
 name = StringField('Name')
 bio = TextAreaField('Bio')
 age = IntegerField('Age')
 password = PasswordField('Password')
 submit = SubmitField('Submit')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http','https') and \
           ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        username = form.username.data
        password = form.password.data
        bird = db.get_id_by_user(username)[0] 
        if bird and  check_password_hash(bird['PasswordHash'], password):

            user = User(bird['BirdId'])

            login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('feed'))
    return flask.render_template('login.html', form=form)


@app.route('/test')
@login_required
def test():
    return render_template('test.html')







@app.route("/feed")
@login_required
def feed():
   
    files = os.listdir(app.config['UPLOAD_DIRECTORY'])
    images = []

    for file in files:
        extension = os.path.split(file)[1].lower()
        if extension in app.config['ALLOWED_EXTENSIONS']:
            images.append(file)
    
    
   # posts = db.get_posts_by_Id(current_user.id)
    posts = db.get_all_posts() 
  
    user = db.get_user_by_Id(current_user.id)[0] 
    
    for post in posts:
        post['Likescount'] = db.like_count(post['PostId'])
        if db.already_liked(current_user.id, post['PostId']):
            post['CurrentBirdLike'] = True
   
    if (posts == None):
        posts = []
    return render_template('feed.html', images=images, posts=posts, titile="My feed",  BirdId=current_user, user=user)

@app.route('/upload', methods=['POST'])
def upload():
    try:
      file = request.files['file']
      extension = os.path.split(file)[1].lower()
      if file:

         if extension not in app.config['ALLOWED_EXENSIONS']: 
             return 'File is not an image.'

         file.save(os.path.join(
            app.config['UPLOAD_DIRECTORY'],
            secure_filename(file.filename)
        ))
    except RequestEntityTooLarge:

        return 'file is larger than 16MB limit.'
    return redirect(url_for('feed'))
    

@app.route("/serve-image/<filename>", methods=['GET'])
def serve_image(filename): 
    return send_from_directory(app.config['UPLOAD_DIRECORTORY'], filename)  

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[-1].lower() in ['jpg','jpeg','gif','png']
 
@app.route("/birds/<string:user>", methods=['GET', 'POST'])
def profile(user):
    if request.method == 'POST':
            # process the image upload

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_DIRECTORY'], filename)
            file.save(file_path)
            original = Image.open(file_path)
            new_file_path = os.path.join(app.config['UPLOAD_DIRECTORY'], "%s.png" % user)
            original.save(new_file_path, format="png")
    bird_data = db.get_id_by_user(user)
    if (len(bird_data) > 0):
        bird = bird_data[0] 
        posts = db.get_posts_by_Id(current_user.id)
        if (posts == None):
            posts = []
        return render_template('profile.html', title=bird['Name'], bird=bird, posts=posts, user=current_user )
    else:
        return "bird does not exist"
# @app.route("/comments/<int:posts>")
# @login_required
# def comments(posts):
#    post = db.get_all_posts[posts]
#    return render_template('comments.html', title="Comments", posts=posts) 

@app.route("/create", methods=['POST'])  
def create():
    post_content = request.form['post-content']
    db.insert_post(current_user.id, post_content) 
    return redirect(url_for('feed'))


@app.route("/likes/<int:post_id>")
@login_required
def like(post_id):
    username = current_user.id
    like_result = db.toggle_like(username, post_id)
   #   lc = db.like_count(post_id)
    ('like count came back as:', like_result)
    return json.dumps(like_result)

@app.route("/api/comments/<int:post_id>")
@login_required
def comments_api(post_id):
 c = db.get_comment_by_Id(post_id)
 return  json.dumps(c)  

# @app.route("/unlikes/<int:post_id>")
# @login_required
# def unlike(post_id):
#    username = current_user.id
#    db.unlike_post(username, post_id)
#    return redirect(url_for('feed')) 


@app.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):
   # post_id = request.args.get('post_id')
    db.delete_post(post_id,current_user.id)
    return redirect(url_for('feed'))
##
@app.route('/cancel_friend_request/<int:sender_id>')
@login_required
def cancel_friend_request(sender_id):
    db.cancel_friend_request(sender_id,current_user.id)
    return redirect(url_for('request'))

@app.route('/cancel_a_friend_requestt/<int:receiver_id>')
@login_required
def cancel_a_friend_request(receiver_id):
    db.cancel_a_friend_request(receiver_id,current_user.id)
    return redirect(url_for('profile'))
#
@app.route('/add_a_friend/<int:friend_id>')
@login_required
def add_a_friend(friend_id):
    db.add_a_friend(friend_id,current_user.id)
    return redirect(url_for('request'))

@app.route('/friend_request/<int:receiver_id>')
@login_required
def add_friend_request(receiver_id):
    db.add_friend_request(receiver_id,current_user.id)
    return redirect(url_for('profile'))

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/messages')
@login_required
def message_chat():
    messages = db.get_all_messages() 
    user = db.get_user_by_Id(current_user.id)[0] 
    return render_template('message.html', user=user , messages=messages)


@app.route('/create_message', methods=['GET', 'POST'])
@login_required
def create_message(): 
    message_content = request.form['message_content'] 
    db.insert_into_message(current_user.id, message_content)
    return redirect(url_for('message'))

@app.route('/request')
@login_required
def friend_request():
    friend_requests = db.friend_request(current_user.id)
    
    user = db.get_user_by_Id(current_user.id)[0] 
    return render_template('request.html', user=user , friend_requests=friend_requests)

@app.route('/search_users', methods=['GET', 'POST'])
@login_required
def search_users():
    search_input = request.form['search_input']
    db.search_user(current_user.id, search_input)
    return redirect(url_for('users'))

 

@app.route('/users')
@login_required
def users():
    users = db.get_all_users() 
    user = db.get_user_by_Id(current_user.id)[0] 
    return render_template('user.html', user=user , users=users)    

@app.route('/accept_friend')
@login_required
def accept_friend():
    
    friends = db.accept_friend_request(current_user.id)
    user = db.get_user_by_Id(current_user.id)[0] 
    return render_template('friends.html',user=user, friends=friends)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = signUpForm()
    if  form.validate_on_submit():
        username = form.username.data
        password_hash = generate_password_hash(form.password.data)
        name = form.name.data
        bio = form.bio.data
        age = form.age.data
        # if request.method =='POST':
        
        #     username = request.method['Username']
        #     name = request.method['Name']
        #     bio = request.method['Bio']
        #     age = request.method['Age']
        #     password_hash = generate_password_hash(request.method['Password'])


        db.create_user(username, name, bio, age, password_hash)
        
        bird_ids = db.get_id_by_user(username)
        print(bird_ids)
        bird_id = db.get_id_by_user(username)[0]
        print(bird_id['BirdId'])
        user = User(bird_id['BirdId'])

        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)
        return flask.redirect(next or flask.url_for('feed'))
    
    return render_template('signup.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('splash'))

if __name__ == '__main__':
    app.run(debug=True)
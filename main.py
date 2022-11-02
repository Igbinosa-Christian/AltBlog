from flask import Flask,render_template,request,redirect,flash,url_for
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,login_user,logout_user,login_required,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime



# Defining base dir. of main.py
base_dir=os.path.dirname(os.path.realpath(__file__))

# Create an instance of sqlalchemy
db=SQLAlchemy()


# Create a flask instance
app=Flask(__name__)


# Database Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY']='d264032a74d1555a05942698'

# Initialize the app database
db.init_app(app)


# User Model
class User(db.Model,UserMixin):
    id=db.Column(db.Integer(),primary_key=True)
    first_name=db.Column(db.String(200),nullable=False)
    last_name=db.Column(db.String(200),nullable=False)
    username=db.Column(db.String(150),unique=True,nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password_hash=db.Column(db.Text(),nullable=False)

    def __repr__(self):
        return f"User {self.username}"


# Blog Post Model
class Post(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    author = db.Column(db.String(150),nullable=False)
    title = db.Column(db.String(255),nullable=False)
    content = db.Column(db.String(),nullable=False)
    date = db.Column(db.DateTime(), nullable=False, default = datetime.now())

    def __repr__(self):
        return f"Post {self.author}"



# Contact(Message) Us Model
class Message(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(150),nullable=False)
    email = db.Column(db.String(255),nullable=False)
    feedback = db.Column(db.String(),nullable=False)
    date = db.Column(db.DateTime(), nullable=False, default = datetime.now())

    def __repr__(self):
        return f"Post {self.name}"



#LoginManager Instance
login_manager=LoginManager(app) 
login_manager.login_view='login'



# Create user loader to get users from database
@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))



# Home page route
@app.route('/')
def index():
    posts = Post.query.all()
    
    return render_template('index.html', posts=posts)


# About Route
@app.route('/about')
def about():
    return render_template('about.html')


# Contact Route
@app.route('/contact_us', methods=['GET','POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        feedback = request.form.get('feedback')

        
        new_message = Message(name=name, email=email, feedback=feedback)

        db.session.add(new_message)
        db.session.commit()

        flash("Feedback Sent", category='success')
        return redirect(url_for('index'))

    return render_template('contact_us.html')




# Signup Route
@app.route('/signup', methods=['GET','POST'])
def signup():
    
    if request.method == 'POST':
        first_name=request.form.get('first_name')
        last_name=request.form.get('last_name')
        username=request.form.get('username')
        email=request.form.get('email')
        password=request.form.get('password')
        con_Password=request.form.get('con_password')
        

        # To validate if a user already exists by username
        user_exists=User.query.filter_by(username=username).first()

        if user_exists:
            flash(f"User with Username {username} exists.", category='error')
            return redirect(url_for('signup'))

        # To validate if a user already exists by email
        email_exists=User.query.filter_by(email=email).first()

        if email_exists:
            flash(f"User with email {email} exists", category='error')
            return redirect(url_for('signup'))   

        # To confirm if passwords match 
        if password != con_Password:
            flash(f'Passwords do not match', category='error')
            return redirect(url_for('signup')) 
        else:
            password_hash=generate_password_hash(password) # To hide password in hash in database
            new_user=User(
                first_name=first_name, last_name=last_name,username=username,
                email=email,password_hash=password_hash
            )   

            db.session.add(new_user)
            db.session.commit()

            flash("User Account Created", category='success') 
            return redirect(url_for('login'))
         

    return render_template('signup.html')



# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username=request.form.get('username')
        password=request.form.get('password')
    

        user=User.query.filter_by(username=username).first()

        if not user:
            flash(f'User does not exist', category='error')
            return redirect(url_for('login'))

        if user and not check_password_hash(user.password_hash,password) :
            flash(f'Incorrect Password', category='error')
            return redirect(url_for('login'))


        if user and check_password_hash(user.password_hash,password):
            login_user(user)
            

            return redirect(url_for('index'))

    return render_template('login.html')



# Route to add post
@app.route('/add_post/<string:author>', methods=['GET','POST'])
@login_required
def add_post(author):
    if request.method == 'POST':
        author = current_user.username
        title = request.form.get('title')
        content = request.form.get('content')

        if author:
            new_post = Post(author=author, title=title, content=content)

            db.session.add(new_post)
            db.session.commit()

            flash("Post Created", category='success')
            return redirect(url_for('index'))

    return render_template('add_post.html')



# Route to view all your(user) posts
@app.route('/my_posts/<string:author>')
@login_required
def my_posts(author):
    author = current_user.username
    posts = Post.query.filter_by(author=author).all()

    return render_template('my_posts.html', posts=posts)



# Route to read complete post
@app.route('/read/<int:id>/', methods=['GET'])
def read(id):
    post = Post.query.get_or_404(id)

    return render_template('read.html', post=post)



# Route to search by author 
@app.route('/results', methods=(['GET', 'POST']))
def results():
    if request.method == 'POST':
        author = request.form.get('search')
        posts = Post.query.filter_by(author=author).all()

        if not author:
            flash("Author does not exist", category='error')
            return redirect(url_for('index'))

        if author:
            return render_template('results.html', posts=posts, author=author)



# Route to update post
@login_required
@app.route('/update/<int:id>/', methods=['GET', 'POST'])
def update(id):
    post_to_update=Post.query.get_or_404(id)

    if request.method == 'POST':
        post_to_update.author=current_user.username
        post_to_update.title=request.form.get('title')
        post_to_update.content=request.form.get('content')

        # To confirm that current user owns the post before editing
        if current_user.username == post_to_update.author:

            db.session.commit()

            flash("Update Successful", category='success')
            return redirect(url_for('index'))

        else:
           flash("CANNOT UPDATE ANOTHER AUTHOR'S POST", category='error') 
           return redirect(url_for('index'))

    return render_template('update.html', post=post_to_update)



# Route to delete post
@login_required
@app.route('/delete/<int:id>/', methods=['GET'])
def delete(id):
    post_to_delete=Post.query.get_or_404(id)
    
    # To confirm that current user owns the post before deleting
    if current_user.username == post_to_delete.author:

        db.session.delete(post_to_delete)
        db.session.commit()    

        flash("POST DELETED", category='error')
        return redirect(url_for('index'))

    else:
        flash("CANNOT DELETE ANOTHER AUTHOR'S POST", category='error') 
        return redirect(url_for('index'))



# Route to logout
@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(debug=True)
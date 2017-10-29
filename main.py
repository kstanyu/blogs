
from flask import Flask, redirect, render_template, request, url_for, session, flash
#info_check is a design python file with custom parameter check functions

from info_checks import *
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://blogz:LC101Blogz@localhost:8889/blogz"

app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
app.secret_key ="\xbd\xcf\xa7\x1b\xf2\xaaC\xc7\xba\xdf#/\x19.\xa0\x81\xd1\xad#\xbb\xa1\xd5\xee\x10"

#check validity of a user dat field
def field_checker(user_info):
    validity = False
    if not is_empty(user_info) and not contains_a_space(user_info) and is_length_ok(user_info):
        validity = True
    return validity

#verify if the passwords are the same
def double_field_checker(usr_pword, usr_vpword):
    double_validity = False
    if not field_checker(usr_pword) and not field_checker(usr_vpword):
        return double_validity
    else:
        if is_a_match(usr_pword, usr_vpword):
            double_validity = True
    return double_validity

class User(db.Model):
    """blogz user class"""
    
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True )
    password = db.Column(db.String(120))
    blogs = db.relationship("Blog", backref = "author")
   
    def __init__(self, username, password):
        self.username = username
        self.password = password
    

class Blog(db.Model):
    """blog class thats owned by a user"""
    
    id = db.Column(db.Integer, primary_key = True)
    blog_title = db.Column(db.String(120))
    blog_post = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, blog_title, blog_post, author, pub_date=None):
        self.blog_title = blog_title
        self.blog_post = blog_post	
        self.author = author
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

@app.before_request
def require_login():
    allowed_routes = ['login','blog', 'index', 'signup']
    if request.endpoint not in allowed_routes and 'username'  not in session:
        return redirect(url_for("login")) 

@app.route("/", methods = ["POST", "GET"])
def index():
    users = User.query.all()
    
    return render_template("index.html", users = users)
 
@app.route("/signup", methods = ["POST","GET"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        verify_password = request.form["verify"]
        
        """verify new user data before account creation"""
        username_error = ""
        password_error = ""
        verify_password_error = ""

        if not field_checker(username):
            username = ""
            username_error = "That\'s not a valid Username"
        
        if not double_field_checker(password, verify_password):
            password = ""
            password_error = "That\s not a valid password"
            verify_password = ""
            verify_password_error = "Passwords don\'t match"

        if not username_error and not password_error and not verify_password_error:
            existing_user = User.query.filter_by(username = username).first()
            if not existing_user:
                new_user = User(username,password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect(url_for("newpost"))
            else:
                flash("User Already exist","error_message")
        else:
            return render_template("signup.html", username_error = username_error, password_error = password_error, verify_password_error = verify_password_error, username = username)
    return render_template("signup.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        username =  request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()

        """checks if username and/or password are in database"""
        if user is None:
            flash("Invalid User", "error_message")
            return redirect(url_for("login"))
        else:
            if user.password == password:
                session['username'] = username     
                return redirect(url_for("newpost"))
            elif user.password != password:
                flash("Incorrect Password")
                return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/blog", methods = ["POST", "GET"])
def blog():
    authors = User.query.all()
    blog_posts = Blog.query.all()
    users_blog_entries = []

    if "id" in request.args:
        blog_id = request.args.get('id')
        blog_entry = Blog.query.get(blog_id)
        return render_template("blog-post.html", blog_title = blog_entry.blog_title, blog_content = blog_entry.blog_post, username = blog_entry.author.username)
    elif "user" in request.args:
        blog_user = request.args.get("user")
        for author in authors:
            if author.username == blog_user:
                users_blog_entries = Blog.query.filter_by(author = author).all()
        return render_template("single_user.html", user_entries = users_blog_entries)
    else:
        return render_template("blogs.html", title = "BLOG POSTS!", blogposts = blog_posts)


@app.route("/newpost", methods = ["POST", "GET"])
def newpost(): 
    
    author = User.query.filter_by(username = session["username"]).first()

    if request.method == "POST":
        blog_title_error = ""
        blog_post_error = ""
        blg_title = ""
        blg_post = ""
        if is_empty(request.form["blog_title"]) or is_empty(request.form["blog_post"]):
            if is_empty(request.form["blog_title"]):
                blog_title_error = "Please fill in the title."
            else:
                blg_title = request.form["blog_title"]
            if is_empty(request.form["blog_post"]):
                blog_post_error = "Please fill in the Body."
            else:
                blg_post = request.form["blog_post"]

        #if (request.form["blog_title"] == "") or (request.form["blog_post"] == ""):
        if blog_title_error or blog_post_error: 
            return render_template("newpost.html", blg_title = blg_title, blg_post = blg_post,  blog_title_error = blog_title_error, body_error = blog_post_error)
        else:
            blog_title = request.form["blog_title"]
            new_post = request.form["blog_post"]
            new_blog = Blog(blog_title, new_post, author)
            db.session.add(new_blog)
            db.session.commit()
        
            return redirect(url_for("blog", id = [new_blog.id]))
    
    return render_template("newpost.html")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect(url_for("blog"))
    
if __name__ == "__main__":
    app.run()

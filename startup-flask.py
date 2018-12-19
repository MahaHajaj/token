from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from startup_setup import Base, Startup, Founder, User
from sqlalchemy.pool import SingletonThreadPool
from flask import session as login_session
import random, string
import json
from flask import request, g
from flask import make_response
from flask import jsonify
import requests

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()



# Instance, every time it runs create instance name
app = Flask(__name__)
APPLICATION_NAME = "Startups"

# Connect to Database and create database session
engine = create_engine('sqlite:///startupwithusers.db?check_same_thread=False', poolclass=SingletonThreadPool)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()




@auth.verify_password
def verify_password(username_or_token, password):
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})    

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username is None or password is None:
            print "missing arguments"
            abort(400)

        if session.query(User).filter_by(username = username).first() is not None:
            login_session['username'] = username
            user = session.query(User).filter_by(username=username).first()
            return redirect(url_for('showAllStartup'))

        user = User(username = username)
        user.hash_password(password)
        login_session['username'] = username
        session.add(user)
        session.commit()
        return redirect(url_for('showAllStartup'))
    else:
         return render_template('login.html')

@app.route('/logout', methods = ['GET'])
def logout():
    if login_session['username']:
        login_session['username'] = ''
        flash("You have successfully been logged out.")
        return redirect(url_for('showAllStartup'))
    else:
        flash("You are already logged out.")

# Startup details page
@app.route('/Startup/<int:startup_id>',methods=['GET', 'POST'])
@auth.login_required
def showStartup(startup_id):
    startup = session.query(Startup).filter_by(id=startup_id).one()
    founder = session.query(Founder).filter_by(startup_id=startup_id).all()
    owner = getUserInfo(startup.username)
    if request.method == 'POST':
    	newFounder = Founder(name = request.form['name'], bio = request.form['bio'],startup_id=startup_id)
    	session.add(newFounder)
    	session.commit()
    	flash("New founder has been added")
    	return redirect(url_for('showStartup', startup_id=startup_id))
    else:
        if 'username' not in login_session or owner.username != login_session['username']:
            return render_template('startup.html', startup = startup, founder = founder, owner = owner, isOwner = False)
        else:
            return render_template('startup.html', startup = startup, founder = founder, owner = owner, isOwner = True)


# Main Route Has All Startups
@app.route('/', methods=['GET', 'POST'])
@app.route('/startups', methods=['GET', 'POST'])
def showAllStartup():
    if request.method == 'POST':
    	newStartup = Startup(name = request.form['name'], username=login_session['username'])
    	session.add(newStartup)
    	session.commit()
    	flash("New startup has been added")
    	return redirect(url_for('showAllStartup'))
    else:
        list = session.query(Startup).all()
        return render_template('allList.html', list=list)

# Founder Edit Page
@app.route('/Startup/<int:startup_id>/<int:founder_id>/edit',methods=['GET', 'POST'])
@auth.login_required
def editFounder(startup_id,founder_id):
    startup = session.query(Startup).filter_by(id=startup_id).one()
    editFounder = session.query(Founder).filter_by(id=founder_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if startup.username != login_session['username']:
        return "<script>function myFunction() {alert('You are not authorized to edit the founder!');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
    	if request.form['name']:
            editFounder.name = request.form['name']
        if request.form['bio']:
            editFounder.bio = request.form['bio']
        session.add(editFounder)
        session.commit()
    	flash("Founder info have been updated")
    	return redirect(url_for('showStartup', startup_id=startup_id))
    else:
    	return render_template('startup.html', startup=startup, founder=founder)


# Founder Delete Page
@app.route('/Startup/<int:startup_id>/<int:founder_id>/delete',methods=['GET', 'POST'])
@auth.login_required
def deleteFounder(startup_id,founder_id):
    startup = session.query(Startup).filter_by(id=startup_id).one()
    founderToBeDeleted = session.query(Founder).filter_by(id=founder_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if startup.username != login_session['username']:
        return "<script>function myFunction() {alert('You are not authorized to delete the founder!');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(founderToBeDeleted)
        session.commit()
    	flash("Founder has been deleted")
    	return redirect(url_for('showStartup', startup_id=startup_id))
    else:
    	return render_template('startup.html', startup=startup, founder=founder)


def getUserInfo(username):
    user = session.query(User).filter_by(username=username).one()
    return user


# Main part runs if there is no exceptions, from python interpretur
if __name__ == '__main__':
    app.secret_key = 'super_secure'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

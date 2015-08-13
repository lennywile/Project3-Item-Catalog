from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """User selects logon button, show login.html"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google logon"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    """Add user to database"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# gdisconnect - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    """User logoff"""
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect - allow for future providers
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("Logoff successful")
        return redirect(url_for('showCatalog'))
    else:
        flash("Login successful")
        return redirect(url_for('showCatalog'))


# get the user from the database if they exist
def getUserID(email):
    """get the userid from the database"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON APIs to view Catalog Information
@app.route('/json')
def catalogjson():
    """List all items via JSON api"""
    list = []
    items = session.query(Item).all()
    for item in items:
        list.append({"name": item.name,
                     "id": item.id,
                     "description": item.description,
                     "category": item.category.name,
                     "owner": item.owner.name
                     })
    return jsonify({"items": list})


# display the entire catalog - no category selected
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """Display entire catalog"""
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(desc(Item.created))
    if 'username' in login_session:
        return render_template('catalog.html', categories=categories,
                               items=items, user=login_session['username'])
    else:
        return render_template('catalog.html',
                               categories=categories, items=items)


# display the items by category
@app.route('/catalog/<string:category_name>/')
def showCategory(category_name):
    """Display items by catageory"""
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=category).all()
    if 'username' in login_session:
        return render_template('catalog.html', categories=categories,
                               items=items,
                               category=category,
                               user=login_session['username'])
    else:
        return render_template('catalog.html', categories=categories,
                               items=items, category=category)


# display a specific item
@app.route('/item/<int:item_id>/')
def showItem(item_id):
    """Display a specific item"""
    item = session.query(Item).filter_by(id=item_id).one()
    if 'username' in login_session:
        return render_template('item.html', item=item,
                               user=login_session['username'])
    else:
        return render_template('item.html', item=item)


# add an item to the database
@app.route('/catalog/<string:category_name>/add/', methods=['GET', 'POST'])
def addItem(category_name):
    """Add item to database"""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    user = login_session['username']
    if user is not None:
        if request.method == 'POST':
            if request.form['name'] != "":
                myuser = session.query(User).filter_by(name=user).one()
                mycategory = session.query(Category).filter_by(name=request.form['category']).one()
                item = Item(name=request.form['name'],
                            description=request.form['description'],
                            category=mycategory,
                            owner=myuser)
                session.add(item)
                session.commit()
                flash("Item " + item.name + " added to " + item.category.name)
                return redirect(url_for('showCategory',
                                        category_name=mycategory.name))
            else:
                flash("Please provide an item name")
                return redirect(url_for('addItem',
                                category_name=category_name))
        else:
            return render_template('additem.html', category=category,
                                   categories=categories, user=user)
    else:
        flash("You are not logged on, please logon")
        return redirect(url_for('showCatalog'))


# edit an item in the database
@app.route('/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    """Edit an item"""
    item = session.query(Item).filter_by(id=item_id).one()
    user = login_session['username']
    if user == item.owner.name:
        if request.method == 'POST':
            if request.form['name'] != "":
                item.name = request.form['name']
                item.description = request.form['description']
                if request.form['category']:
                    category = session.query(Category).filter_by(name=request.form['category']).one()
                    item.category = category
                session.add(item)
                session.commit()
                flash("Item " + item.name + " successfully updated")
                return redirect(url_for('showItem', item_id=item.id))
            else:
                flash("Please provide an item name")
                return redirect(url_for('editItem', item_id=item.id))
        else:
            categories = session.query(Category).all()
            return render_template('edititem.html', item=item,
                                   categories=categories, user=user)
    else:
        flash("You are not the owner of this item")
        return redirect(url_for('showCatalog'))


# delete an item from the database
@app.route('/item/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    """Delete an item from database"""
    item = session.query(Item).filter_by(id=item_id).one()
    category = item.category
    user = login_session['username']
    if user == item.owner.name:
        if request.method == 'POST':
            flash("Item " + item.name + " successfully deleted")
            session.delete(item)
            session.commit()
            return redirect(url_for('showCategory',
                                    category_name=category.name))
        else:
            return render_template('deleteitem.html', item=item,
                                   user=login_session['username'])
    else:
        flash("You are not the owner of this item")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

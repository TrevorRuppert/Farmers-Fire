from flask import Flask, flash, render_template, make_response, request, redirect, abort, g, url_for, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.debug import DebuggedApplication
from flask_admin.model import typefmt
from sqlalchemy import or_
from collections import OrderedDict
import os
import pdfkit

uri = os.environ.get('URI')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.secret_key = 'supersecretkeydevtest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

admin = Admin(app)


class User(db.Model):
    __tablename__ = 'User'
    can_create = False
    id = db.Column('id', db.Integer, primary_key=True)
    first = db.Column('first', db.String(15), nullable=False)
    last = db.Column('last', db.String(25), nullable=False)
    username = db.Column('username', db.String(80), unique=True, nullable=False)
    password = db.Column('password', db.String(80), nullable=False)
    phonenumber = db.Column('phonenumber', db.String(45), nullable=False)
    dob = db.Column('dob', db.DateTime, nullable=False)
    admin = db.Column('isadmin', db.Boolean, default=False, nullable=False)

    def __init__(self, first=None, last=None, username=None, password=None, phonenumber=None, dob=None):
        self.first = first
        self.last = last
        self.username = username
        self.password = password
        self.phonenumber = phonenumber
        self.dob = dob

    def type_formatter(view, value):
        pass

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return self.username


class JSONMixin(object):

    def _asdict(self):
        result = OrderedDict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)
        return result


class Contact(JSONMixin, db.Model):
    __tablename__ = 'Contact'
    id = db.Column('id', db.Integer, primary_key=True)
    first = db.Column('first', db.String(15), nullable=False)
    last = db.Column('last', db.String(25), nullable=False)
    street = db.Column('street', db.String(80), nullable=False)
    city = db.Column('city', db.String(80), nullable=False)
    state = db.Column('state', db.String(80), nullable=False)
    zipcode = db.Column('zipcode', db.String(80), nullable=False)
    phonenumber = db.Column('phonenumber', db.String(45), nullable=False)

    def __repr__(self):
        return self.first


class Policy(JSONMixin, db.Model):
    __tablename__ = 'Policy'
    id = db.Column('id', db.Integer, primary_key=True)
    policy_number = db.Column('policy_number', db.Integer)
    policy_type = db.Column('policy_type', db.String(25))
    contact_id = db.Column(db.Integer, db.ForeignKey('Contact.id'))
    contact = db.relationship('Contact', backref='policies')

    def __repr__(self):
        return str(self.id)


class Letter(db.Model):
    __tablename__ = 'Letter'
    id = db.Column('id', db.Integer, primary_key=True)
    title = db.Column('title', db.String(25))
    description = db.Column('description', db.String(80))
    template = db.Column('template', db.Text)

    def __repr__(self):
        return self.id


class ContactView(ModelView):
    form_excluded_columns = ('policies')


admin.add_view(ModelView(User, db.session))
admin.add_view(ContactView(Contact, db.session))
admin.add_view(ModelView(Policy, db.session))
admin.add_view(ModelView(Letter, db.session))


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/reports', methods=['GET','POST'])
@login_required
def reports():
    if request.method == "GET":
        return render_template('reports.html')


@app.route('/process', methods=['GET', 'POST'])
def process():
    first = request.form['searchFirst']
    last = request.form['searchLast']
    phone = request.form['searchPhone']
    contacts = Contact.query.filter(Contact.first.contains(first), Contact.last.contains(last), Contact.phonenumber.contains(phone)).all()
    return jsonify(contacts=contacts)


@app.route('/results', methods=['GET','POST'])
@login_required
def results():
    return render_template('results.html')


@app.route('/management', methods=['GET', 'POST'])
@login_required
def management():
    return render_template('management.html')


@app.route('/history')
@login_required
def history():
    return render_template('history.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/test')
def test():
    return render_template('knockouttest.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['inputEmail']
    password = request.form['inputPassword']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username, password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid', 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember=remember_me)
    flash('Logged in Successfully')
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    user = User(request.form['inputFirst'], request.form['inputLast'], request.form['inputEmail'], request.form['dob'], request.form['inputPassword', request.form['inputStreet'],request.form['inputState'],request.form['inputCity'],request.form['inputZip'],request.form['inputPhone']])
    db.session.add(user)
    db.session.commit()
    flash('User successfully created!')
    return redirect(url_for('login'))


@app.route('/profile/<name>')
@login_required
def profile():
    return render_template('profile.html', name=name)


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')


@app.route('/genreport')
def pdf_template():
    lid = request.args.get('lid')
    pid = request.args.get('policyId')
    policy = Policy.query.get(pid)
    letter = Letter.query.get(lid)
    rendered = render_template_string(letter.template, policy=policy)
    pdf = pdfkit.from_string(rendered, False)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

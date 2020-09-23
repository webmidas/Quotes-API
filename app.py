from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
from datetime import datetime


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quotes.db')
app.config['JWT_SECRET_KEY'] = 'Bc4HOUCKCbDLyAZ8XaY3M3VpisP6JhLs'  # change this IRL
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = 'yt'

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    first = Quote(quote='Whatever mind can conceive and believe , mind can achieve it',
                     author='John')

    second = Quote(quote='I am the DON',
                     author='Ashish')

    third = Quote(quote='If you can dream it, you can do it',
                     author='Neilson')

    db.session.add(first)
    db.session.add(second)
    db.session.add(third)

    test_user = User(first_name='Mark',
                     last_name='Swan',
                     email='reply@reply.com',
                     password='test123')

    db.session.add(test_user)
    db.session.commit()
    print('Database seeded!')


@app.route('/')
def home():
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )


@app.route('/quotes', methods=['GET'])
def Quotes():
    quote_list = Quote.query.all()
    result = quotes_schema.dump(quote_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists.'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded!", access_token=access_token)
    else:
        return jsonify(message="Bad email or password"), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your quotes API password is " + user.password,
                      sender="admin@test.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="That email doesn't exist"), 401


@app.route('/quote_details/<int:quote_id>', methods=["GET"])
def quote_details(quote_id: int):
    quote = Quote.query.filter_by(quote_id=quote_id).first()
    if quote:
        result = quote_schema.dump(quote)
        return jsonify(result)
    else:
        return jsonify(message="That quote does not exist"), 404


@app.route('/add_quote', methods=['POST'])
@jwt_required
def add_quote():
    quote = request.form['quote']
    test = Quote.query.filter_by(quote=quote).first()
    if test:
        return jsonify("There is already a quote by that name"), 409
    else:
        author = request.form['author']

        new_quote = Quote(quote=quote,
                            author=author)

        db.session.add(new_quote)
        db.session.commit()
        return jsonify(message="You added a quote"), 201


@app.route('/update_quote', methods=['PUT'])
@jwt_required
def update_quote():
    quote_id = int(request.form['quote_id'])
    quote = Quote.query.filter_by(quote_id=quote_id).first()
    if quote:
        quote.quote = request.form['quote']
        quote.author = request.form['author']
        db.session.commit()
        return jsonify(message="You updated a quote"), 202
    else:
        return jsonify(message="That quote does not exist"), 404


@app.route('/remove_quote/<int:quote_id>', methods=['DELETE'])
@jwt_required
def remove_quote(quote_id: int):
    quote = Quote.query.filter_by(quote_id=quote_id).first()
    if quote:
        db.session.delete(quote)
        db.session.commit()
        return jsonify(message="You deleted a quote"), 202
    else:
        return jsonify(message="That quote does not exist"), 404


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Quote(db.Model):
    __tablename__ = 'quotes'
    quote_id = Column(Integer, primary_key=True)
    quote = Column(String)
    author = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class QuoteSchema(ma.Schema):
    class Meta:
        fields = ('quote_id', 'quote', 'author')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

quote_schema = QuoteSchema()
quotes_schema = QuoteSchema(many=True)


if __name__ == '__main__':
    app.run()

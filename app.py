from os import path, environ
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = path.abspath(path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path.join(basedir, 'planet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# TODO change this
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER']= environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = environ.get('MAIL_PORT')
app.config['MAIL_USERNAME'] = environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database Created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database Dropped!!!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(
        name='Mercury',
        category='Class D',
        home_star='Sol',
        mass=3.258e23,
        radius=1516,
        distance=35.98e6
    )
    venus = Planet(
        name='Venus',
        category='Class K',
        home_star='Sol',
        mass=4.867e24,
        radius=3760,
        distance=67.24e6
    )
    earth = Planet(
        name='Earth',
        category='Class M',
        home_star='Sol',
        mass=5.972e24,
        radius=3959,
        distance=92.96e6
    )

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        first_name='Wiliam',
        last_name='Herschel',
        email='test@test.com',
        password='P@ssw0rd'
    )

    db.session.add(test_user)

    db.session.commit()
    print('Database Seeded!')


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='The Email already exists !!'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return jsonify(message='User created successfully'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password= request.form['password']

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded', access_token=access_token), 200
    else:
        return jsonify(message='Bad email or password'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message(
            "Your planetary API password is " + user.password,
            sender="admin@planetary.edu",
            recipients=[email]
        )
        mail.send(msg)
        return jsonify(message="Password is sent to " + email)
    else:
        return jsonify(message=email + " does not exist"), 404


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message="The planet does not exist"), 404


@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    name = request.form['name']
    planet = Planet.query.filter_by(name=name).first()
    if planet:
        return jsonify(message="There is already a planet by that name"), 409
    else:
        category = request.form['category']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planet(
            name=name,
            category=category,
            home_star=home_star,
            mass=mass,
            radius=radius,
            distance=distance
        )
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You add a planet"), 201


# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'password'
        )


class Planet(db.Model):
    __tablename__ = 'planets'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class PlanetSchema(ma.Schema):
    class Meta:
        fields = (
            'id',
            'name',
            'category',
            'home_star',
            'mass',
            'radius',
            'distance'
        )


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == "__main__":
    app.run()

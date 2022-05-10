from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./movies_collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'YOUR APP CONFIG SECRET KEY'
SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
API_KEY = 'YOUR API KEY FROM TMDB'
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(500), unique=True, nullable=False)
    rating = db.Column(db.Float, unique=False, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String(120), unique=False, nullable=True)
    img_url = db.Column(db.String(300), unique=True, nullable=False)

db.create_all()

class EditForm(FlaskForm):
    rating_form = FloatField('Rating', validators=[DataRequired()])
    review_form = StringField('Edit your review', validators=[DataRequired()])
    submit_form = SubmitField('Apply Changes')

class AddForm(FlaskForm):
    add_form = StringField('Movie Title', validators=[DataRequired()])
    add_button = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    film_q = len(all_movies)
    for movie in all_movies:
        movie.ranking = film_q
        film_q -= 1
    return render_template("index.html", movies=all_movies)

@app.route('/edit', methods=['POST', 'GET'])
def edit():
    form = EditForm()
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    if request.method == 'POST' and form.validate_on_submit():
        movie.rating = request.form['rating_form']
        movie.review = request.form['review_form']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie)

@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    delete_movie = Movie.query.get(movie_id)
    db.session.delete(delete_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddForm()
    if request.method == 'POST' and form.validate_on_submit():
        movie_title = form.add_form.data
        params = {
            'api_key': API_KEY,
            'query': movie_title
        }
        response = requests.get(url=SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
        lenght_data = len(data['results'])
        return render_template('select.html', films=data, quantity=lenght_data)
    return render_template('add.html', form=form)

@app.route("/add_movie")
def movie_details():
    ide = request.args.get('id')
    params = {
        'api_key': API_KEY
    }
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{ide}', params=params)
    response.raise_for_status()
    movie_data = response.json()
    film = Movie(title=movie_data['original_title'],
                 year=movie_data['release_date'],
                 description= movie_data['overview'],
                 img_url=f"https://image.tmdb.org/t/p/original/{movie_data['poster_path']}")
    db.session.add(film)
    db.session.commit()
    film = Movie.query.filter_by(title=film.title).first()
    film_id = film.id
    return redirect(url_for('edit', id=film_id))

if __name__ == '__main__':
    app.run(debug=True)


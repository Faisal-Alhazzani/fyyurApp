# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import (Flask, render_template, request, flash, redirect, url_for)
import logging
from logging import Formatter, FileHandler
from sqlalchemy import func
from flask_wtf import Form
from forms import *
from flask_moment import Moment
from flask_migrate import Migrate
from models import db, Venue, Artist, Show
from flask_wtf.csrf import CSRFProtect



# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)


# Completed: connect to a local postgresql database


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # Completed : replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    # initiate regions list to populate it with venues per state, city
    regions = []
    # get all venues
    venues = Venue.query.all()
    # get all venues that has distinct city, state
    places = Venue.query.distinct(Venue.city, Venue.state).all()
    # Nested loop: 1- append distinct city, state
    #              2- take that distinct city, state and grab their venues from venues query
    for place in places:
        regions.append({
            'city': place.city,
            'state': place.state,
            'venues': [{
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
            } for venue in venues if
                venue.city == place.city and venue.state == place.state]
        })
    return render_template('pages/venues.html', areas=regions)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # Completed: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    venues_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
    data = []

    for venue in venues_result:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows":db.session.query(db.func.count(Show.venue_id == venue.id)).filter(
                        Show.start_time > datetime.now()).all(),
      })

    response = {
      "count": len(venues_result),
      "data": data
    }
    #response = {
    #   "count": 1,
    #    "data": [{
    #        "id": 2,
    #        "name": "The Dueling Pianos Bar",
    #        "num_upcoming_shows": 0,
    #    }]
    #}
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # Completed: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)

    if not venue:
      return render_template('errors/404.html')

    else:
      upcoming_shows_query = db.session.query(Show).join(Artist).filter( Artist.id == Show.artist_id).filter(
        Show.start_time > datetime.now()).all()
      upcoming_shows = []

      past_shows_query = db.session.query(Show).join(Artist).filter(Artist.id == Show.artist_id).filter(
        Show.start_time < datetime.now()).all()
      past_shows = []

      for show in past_shows_query:
        past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

      for show in upcoming_shows_query:
        upcoming_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

      data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
      }
      return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm(csrf_enabled=False)
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Completed: insert form data as a new Venue record in the db, instead
    # Completed: modify data to be the data object returned from db insertion
    form = VenueForm(request.form, csrf_enabled=False)
    error = False
    if form.validate():
        try:
          name = form.name.data
          city = form.city.data
          state = form.state.data
          address = form.address.data
          phone = form.phone.data
          image_link = form.image_link.data
          genres = form.genres.data
          facebook_link = form.facebook_link.data
          website = form.website.data
          if form.seeking_talent.data:
              seeking_talent = True
          else:
              seeking_talent = False
          seeking_description = form.seeking_description.data

          venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,
                        facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent,
                        seeking_description=seeking_description)
          db.session.add(venue)
          db.session.commit()
        except:
          error = True
          db.session.rollback()
          print(sys.exc_info())
        finally:
          db.session.close()
        if error:
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        if not error:
          flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return render_template('pages/home.html')
    # on successful db insert, flash success
    # Completed: on unsuccessful db insert, flash an error instead.


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Completed: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash(f'An error occurred. Venue {venue_id} could not be deleted.')
    if not error:
        flash(f'Venue {venue_id} was successfully deleted.')
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # Completed: replace with real data returned from querying the database
    data = db.session.query(Artist).all()

    return render_template('pages/artists.html', artists=data)


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm(csrf_enabled=False)
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # Completed: insert form data as a new Venue record in the db, instead
    # Completed: modify data to be the data object returned from db insertion
    error = False
    form = ArtistForm(request.form, csrf_enabled=False)
    if form.validate():
        try:
            name = form.name.data
            city = form.city.data
            state = form.state.data
            phone = form.phone.data
            genres = form.genres.data
            facebook_link = form.facebook_link.data
            image_link =form.image_link.data
            website = form.website.data
            if form.seeking_venue.data:
                seeking_venue = True
            else:
                seeking_venue = False
            seeking_description = form.seeking_description.data

            artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link,
                            image_link=image_link, website=website, seeking_venue=seeking_venue,
                            seeking_description=seeking_description)
            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
        # Completed: on unsuccessful db insert, flash an error instead.
         # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        if error:
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
            print((sys.exc_info()))
        # on successful db insert, flash success
        if not error:
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return render_template('pages/home.html')



@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Completed: implement search on artists with partial string search. Ensure it is case-insensitive.
    search_term = request.form.get('search_term', '')
    artist_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
    data = []

    for artist in artist_result:
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == artist.id).filter(
                Show.start_time > datetime.now()).all()),
        })

    response = {
        "count": len(artist_result),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # Completed: replace with real venue data from the venues table, using venue_id
    artist = db.session.query(Artist).get(artist_id)

    if not artist:
        return render_template('errors/404.html')

    past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()
    past_shows = []
    # populating past shows list
    for show in past_shows_query:
        past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()
    upcoming_shows = []
    # populating upcoming shows list
    for show in upcoming_shows_query:
        upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link":artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if artist:
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres
        form.facebook_link.data = artist.facebook_link
        form.image_link.data = artist.image_link
        form.website.data = artist.website
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description

    # Completed: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # Completed: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    def edit_artist_submission(artist_id):
        error = False
        artist = Artist.query.get(artist_id)

        try:
            artist.name = request.form['name']
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.genres = request.form.getlist('genres')
            artist.image_link = request.form['image_link']
            artist.facebook_link = request.form['facebook_link']
            artist.website = request.form['website']
            if request.form['seeking_venue']:
                artist.seeking_venue = True
            else:
                artist.seeking_venue = False
            artist.seeking_description = request.form['seeking_description']

            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
        if error:
            flash('An error occurred. Artist could not be changed.')
        if not error:
            flash('Artist was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    if venue:
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.address.data = venue.address
        form.genres.data = venue.genres
        form.facebook_link.data = venue.facebook_link
        form.image_link.data = venue.image_link
        form.website.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description

    # Completed: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # Completed: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website = request.form['website']
        if request.form['seeking_talent']:
            venue.seeking_talent = True
        else:
            venue.seeking_talent = False
        venue.seeking_description = request.form['seeking_description']

        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash(f'An error occurred. Venue could not be changed.')
    if not error:
        flash(f'Venue was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # Completed: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    shows_data = db.session.query(Show).join(Artist).join(Venue).all()

    data = []
    for show in shows_data:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch. ok!
    form = ShowForm(csrf_enabled=False)
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # Completed: insert form data as a new Show record in the db, instead
    error = False
    form = ShowForm(request.form, csrf_enabled=False)
    if form.validate():
        try:
            artist_id = form.artist_id.data
            venue_id = form.venue_id.data
            start_time = form.start_time.data

            show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
            db.session.add(show)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
        # on successful db insert, flash success
        if not error:
            flash('Show was successfully listed!')
        # Completed: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        if error:
            flash('An error occurred. Show could not be listed.')
        return render_template('pages/home.html')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

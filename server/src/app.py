import os
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from datetime import datetime, timedelta
from firebase_admin import db as fb_db
import firebase_admin
from firebase_admin import credentials
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NoneOf


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'magicarts123'


app = Flask(__name__)
app.config.from_object(Config)

# Put path to service key here.
cred = credentials.Certificate('service_key.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL': 'https://fire-apex-data.firebaseio.com/'})


# Consider adding a validator for time argument to accept datetime formats only
def list_to_choices(alist):
    """
    SelectField() choices parameter requires a tuple. tuple[0] is what shows
    up in the dropdown menu, and tuple[1] is what gets passed to the backend
    as data.

    In this case, what gets passed into the backend is the same as the choice
    that shows up in the dropdown menu.

    If the list is required to be in alphabetical order, add sorted(list) to
    choices parameter of SelectField.
    """
    choices = []

    for item in alist:
        choices.append((item, item))

    return choices


class GameDataForm(FlaskForm):
    map_list = list_to_choices(["--SELECT--", "King's Canyon S1",
                                "King's Canyon S2", "King's Canyon S5",
                                "King's Canyon PM", "World's Edge S3",
                                "World's Edge S4"])
    modes_list = list_to_choices(['Trios', 'Duos', 'Ranked'])

    placement = StringField('Placement', validators=[DataRequired()])
    squad_kills = StringField('Squad Kills')
    map = SelectField('Map', choices=map_list, validators=[NoneOf('--SELECT--', 'Select map')])
    mode = SelectField('Mode', choices=modes_list)
    submit = SubmitField('Submit')

    def listings(self):
        return [self.placement, self.squad_kills, self.map, self.mode]


class PlayerDataForm(FlaskForm):
    """
    Design choice; some fields can be left blank when submitting. If blank,
    then entered into db as zero (0).
    """
    weapons_list = list_to_choices(['R-301', 'Hemlok', 'Flatline',
                                    'R-99', 'Alternator', 'Prowler',
                                    'Spitfire', 'Devotion', 'Mozambique',
                                    'RE-45', 'P2020', 'Wingman', 'G7 Scout',
                                    'Longbow', 'Triple Take', 'Kraber',
                                    'Charge Rifle', 'Havoc', 'L-Star',
                                    'Peacekeeper', 'EVA-8', 'Mastiff',
                                    'Sentinel', '--SELECT--', 'Fists'])

    legends_list = list_to_choices(['Bloodhound', 'Gibraltar', 'Lifeline',
                                    'Pathfinder', 'Wraith', 'Bangalore',
                                    'Caustic', 'Mirage', 'Octane', 'Wattson',
                                    'Crypto', 'Revenant', '--SELECT--'])

    username = StringField('Username', validators=[DataRequired()])
    legend = SelectField('Legend', choices=sorted(legends_list), validators=[NoneOf('--SELECT--', 'Select a legend')])
    kills = StringField('Kills')
    damage = StringField('Damage Done')

    # Can't set time as a list of a a minutes StringField and a seconds
    # StringField. Instead set as a placeholder, and when jinja iterates over
    # it, insert minutes and seconds StringFields instead.
    # Don't add minutes and seconds StringFields in listings because it's not
    # part of normal player-data for loop. Want to include down side by side
    # instead of having a page break after minutes.
    time = None  # Placeholder variable to be called by html
    minutes = StringField('min', validators=[DataRequired(), Length(1, 2, 'Invalid Entry: minutes')])
    seconds = StringField('sec', validators=[DataRequired(), Length(1, 2, 'Invalid Entry: seconds')])

    revives = StringField('Players Revived')
    respawns = StringField('Players Respawned')

    weapon1 = SelectField('Weapon', choices=sorted(weapons_list))
    weapon2 = SelectField('Weapon (Optional)', choices=sorted(weapons_list))

    submit = SubmitField('Submit')

    def listings(self):
        return [self.username, self.legend, self.kills, self.damage, self.time,
                self.revives, self.respawns, self.weapon1, self.weapon2]


# Have to add methods on both directories o.w. 405 Error.
@app.route('/', methods=['GET', 'POST'])
@app.route('/player-data', methods=['GET', 'POST'])
def playerData():
    # Push wep_data first to get access to weapons_id for use in player_data
    form = PlayerDataForm()

    if form.validate_on_submit():
        wep_ref = fb_db.reference('/weapons/')
        ply_ref = fb_db.reference('/player_stats/')
        game_ref = fb_db.reference('/game_stats/')

        # Query returns an OrderedDict() object.
        # Can access indices by turning into a list.
        last_timestamp = list(game_ref.order_by_key().limit_to_last(1).get().items())[0][1]['timestamp']
        if datetime.utcnow() <= datetime.fromisoformat(last_timestamp) + timedelta(seconds=150):
            game_id = list(game_ref.order_by_key().limit_to_last(1).get().items())[0][0]
        else:
            game_id = None

        wep_data = {
            'game_id': game_id,
            'username': form.username.data,
            'weapon1': form.weapon1.data if form.weapon1.data != '--SELECT--' else None,
            'weapon2': form.weapon2.data if form.weapon2.data != '--SELECT--' else None,
        }

        wep_ref.push(wep_data)

        # Query returns an OrderedDict() object.
        # Can access indices by turning into a list.
        wep_id = list(wep_ref.order_by_key().limit_to_last(1).get().items())[0][0]

        ply_data = {
            'damage': int(form.damage.data) if form.damage.data else 0,
            'game_id': game_id,
            'kills': int(form.kills.data) if form.kills.data else 0,
            'legend': form.legend.data,
            'respawns': int(form.respawns.data) if form.respawns.data else 0,
            'revives': int(form.revives.data) if form.revives.data else 0,
            'survival_time': f'{form.minutes.data}:{form.seconds.data}',
            'timestamp': datetime.utcnow().isoformat()[:-7],  # Drop microsecs
            'username': form.username.data,
            'weapons_id': wep_id
        }

        ply_ref.push(ply_data)

        flash(f'Data submitted for {form.username.data}')
        return redirect(url_for('playerData'))

    return render_template('player-data.html', title='Player Data', form=form)


@app.route('/game-data', methods=['GET', 'POST'])
def gameData():
    form = GameDataForm()

    if form.validate_on_submit():
        ref = fb_db.reference('/game_stats/')

        data = {
            'created_by': None,
            'map': form.map.data,
            'mode': form.mode.data,
            'placement': form.placement.data,
            'squad_kills': form.squad_kills.data,
            'timestamp': datetime.utcnow().isoformat()[:-7]  # Drop microsecs
        }

        ref.push(data)

        flash(f'Last game submitted at {str(datetime.now())[:-7]}')
        return redirect(url_for('playerData'))

    return render_template('game-data.html', title='Game Data', form=form)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

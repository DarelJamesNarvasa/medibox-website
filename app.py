from flask import Flask, render_template, request, redirect
from flask_mqtt import Mqtt
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'broker.emqx.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_BROKER_USERNAME'] = 'medicine'
app.config['MQTT_BROKER_PASSWORD'] = '1234'
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

topic = 'medicine/reminder'
mqtt = Mqtt(app)

class Database(Base):
    __tablename__ = "drifter_one"
    id = Column(Integer, primary_key=True)

    time = Column(String)
    amount = Column(Integer)
    pills = Column(String)

    def __init__(self, time, amount, pills):
        self.time = time
        self.amount = amount
        self.pills = pills

    def __repr__(self):
        return (f"({self.id}, {self.time}, {self.amount}, {self.pills})")

database_engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(database_engine)

Database_session = sessionmaker(bind=database_engine)
database_session = Database_session()

mqtt.publish(topic, 'website MEDBOX')

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(topic)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    try:
        json_data = json.loads(data['payload'])
    except json.JSONDecodeError:
        print(f"failed to parse JSON")
        return



    time = json_data.get('time', None)
    amount = json_data.get('amount', None)
    pills = json_data.get('pills', None)

    if time is not None and amount is not None and pills is not None:
        new_data = Database(time, amount, pills)
        database_session.add(new_data)
        database_session.commit()

    print(f"time: {time}, amount: {amount}, pills: {pills}")



@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/pillsinfo')
def pillsinfo():
    database_results = database_session.query(Database).all()
    return render_template('pillsinfo.html', data = database_results)

@app.route('/medibox')
def medibox():
    return render_template('medibox.html')

# Route to handle form submission
@app.route('/process_time', methods=['POST'])
def process_time():
    if request.method == 'POST':
        selected_time = request.form['set-time']
        # Split the time string into hour, minute, and AM/PM components
        time_components = selected_time.split(":")
        hour = int(time_components[0])
        minute = int(time_components[1])

        if "PM" in selected_time.upper():
            hour += 12

        print(f"Selected time: {selected_time}")
        print(f"Parsed hour: {hour}, Parsed minute: {minute}")
        mqtt.publish(topic, json.dumps({"hour": hour, "minute": minute}))

        return render_template('medibox.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run()

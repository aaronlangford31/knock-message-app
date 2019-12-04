# Infrastructure test page.
import os
from flask import Flask
from flask import Markup
from flask import render_template
from flask import jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import and_
import time

app = Flask(__name__)

# Configure MySQL connection.
db = SQLAlchemy()
db_uri = 'mysql://root:supersecure@db/messaging'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route("/")
def test():
    mysql_result = False
    query_string = text("SELECT 1")
    # TODO REMOVE FOLLOWING LINE AFTER TESTING COMPLETE.
    db.session.query("1").from_statement(query_string).all()
    try:
        if db.session.query("1").from_statement(query_string).all():
            mysql_result = True
    except:
        pass

    if mysql_result:
        result = Markup('<span style="color: green;">PASS</span>')
    else:
        result = Markup('<span style="color: red;">FAIL</span>')

    # Return the page with the result.
    return render_template('index.html', result=result)

@app.route("/thread", methods=['POST'])
def create_thread():
    data = request.json

    mysql_result = False

    thread = Thread()
    
    for u in data['users']:
        thread.participants.append(ThreadParticipant(user_id=u))

    try:
        db.session.add(thread)
        db.session.commit()

        mysql_result = True
    except Exception as e:
        ## TODO: wire up some actual logger implemention
        print(e)
        db.session.rollback()
        db.session.flush()
        pass

    if mysql_result:
        result = jsonify({
            'threadId': thread.id
        })
        result.status_code = 201
    else:
        result = jsonify({
            'status': '501',
            'message': 'Sorry, I\'m not yet smart enough to explain why I failed'
        })
        result.status_code = 501

    return result

@app.route("/thread/<int:thread_id>/<user_id>", methods=['POST'])
def create_message(thread_id, user_id):
    message = request.json['message']

    mysql_result = False

    ## This is unchecked. Thread could not exist
    participant = ThreadParticipant.query.filter(
        and_(ThreadParticipant.thread_id == thread_id, ThreadParticipant.user_id == user_id)
    ).one()

    participant.messages.append(ThreadMessage(thread_id=thread_id,content=message))

    try:
        db.session.commit()

        mysql_result = True
    except Exception as e:
        ## TODO: wire up some actual logger implemention
        print(e)
        db.session.rollback()
        db.session.flush()
        pass

    if mysql_result:
        result = '', 204
    else:
        result = jsonify({
            'status': '501',
            'message': 'Sorry, I\'m not yet smart enough to explain why I failed'
        })
        result.status_code = 501

    return result

@app.route("/thread/<int:thread_id>", methods=['GET'])
def get_thread(thread_id):
    ## This is unchecked. Thread could not exist
    thread = Thread.query.get(thread_id)
    
    data = {
        'messages': list(map(lambda m: {'username': m.user_id, 'message': m.content}, thread.messages))
    }

    return jsonify(data)

class Thread(db.Model):
    ## Would look into this being a BigInt...
    id = db.Column(db.Integer, primary_key=True)
    participants = db.relationship('ThreadParticipant', backref='thread', lazy=True)
    messages = db.relationship('ThreadMessage', backref='thread', lazy=True)


class ThreadParticipant(db.Model):
    user_id = db.Column(db.String(255), nullable=False, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), primary_key=True)
    messages = db.relationship('ThreadMessage', backref='participant', lazy=True)

class ThreadMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'))
    user_id = db.Column(db.String(255), db.ForeignKey(ThreadParticipant.__tablename__ + '.user_id'))
    content = db.Column(db.Text, nullable=False)

if __name__ == "__main__":
    with app.app_context():
        ## hack to make web app wait for mysql to be ready
        time.sleep(30)
        db.create_all()

    app.run(host="0.0.0.0", port=80)
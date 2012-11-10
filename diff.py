from __future__ import with_statement
import difflib
import logging
import os
import sched
import shutil
import sqlite3
from contextlib import closing
from urllib import urlopen
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from twilio.rest import TwilioRestClient
from apscheduler.scheduler import Scheduler

sched = Scheduler()
sched.start()
logging.basicConfig()

# temporary
DATABASE = '/tmp/diff.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

def init_twilio(filename):
    curpath = os.path.abspath(os.curdir)
    with open(os.path.join(curpath, filename)) as f:
        lines = f.readlines() # temporary method
        num = lines[0].strip()
        sid = lines[1].strip()
        token = lines[2].strip()
    return [num, TwilioRestClient(sid, token)]

twilio = init_twilio('twilio-info')
twilio_num = twilio[0]
twilio_client = twilio[1]

diff = Flask(__name__)
diff.config.from_object(__name__)

# from flask docs
def connect_db():
    return sqlite3.connect(diff.config['DATABASE'])

# from flask docs
def init_db():
    with closing(connect_db()) as db:
        with diff.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

# from flask docs
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

# from flask docs
@diff.before_request
def before_request():
    g.db = connect_db()

# from flask docs
@diff.teardown_request
def teardown_request(exception):
    g.db.close()

@diff.route('/')
def index_page():
    return render_template('index.html')

@diff.route('/confirm', methods=['POST'])
def confirm_page():
    args = request.form
    phone = args['phone']
    url = args['url']
    enter_data(phone, url)
    return render_template('confirm.html', phone=phone, url=url)

def enter_data(phone, url):
    contents = urlopen(url)
    curpath = os.path.abspath(os.curdir)
    last = url.split('/')[-1]
    fname = "contents/%s-%s" % (phone, last)
    with open(os.path.join(curpath, fname), 'w') as f:
        shutil.copyfileobj(contents, f)
    uid = get_id(phone)
    if uid is None:
        query_db("insert into users (phone) values (?)", [phone])
        uid = get_id(phone)
    query_db("insert into requests (uid, url) values (?, ?)", [uid, url])
    msg = "You will receive updates for %s! Love, Diff Checker." % url
    sched.add_interval_job(update, seconds=10, args=[uid])
    return send_text(phone, msg)

def update(uid):
    with diff.test_request_context():
        diff.preprocess_request()
        user = g.db.execute("select phone from users where id = ?", [uid])
        phone = '+' + str([row[0] for row in user.fetchall()][0])
        reqs = g.db.execute("select url from requests where uid = ?", [uid])
        urls = [row[0] for row in reqs.fetchall()]
        for url in urls:
            check_and_send(phone, url)

def check_and_send(phone, url):
    contents = urlopen(url).read()
    curpath = os.path.abspath(os.curdir)
    last = url.split('/')[-1]
    fname = "contents/%s-%s" % (phone, last)
    with open(os.path.join(curpath, fname), 'r') as f:
        match = difflib.SequenceMatcher(None, f.read(), contents)
        matchratio = match.ratio()
        if matchratio != 1:
            print "Difference detected -- sending text to %s" % phone
            msg = "%s has changed! Love, Diff Checker." % url
            send_text(phone, msg)
            with open(os.path.join(curpath, fname), 'w+') as f2:
                f2.write(contents)

def send_text(phone, content):
    msg = twilio_client.sms.messages.create(to=phone, from_=twilio_num,
                                            body=content)
    return msg

# adapted from flask docs
def get_id(phone):
    user = query_db("select * from users where phone = ?", [phone],
                    one=True)
    if user is None:
        return None
    else:
        return user['id']

if __name__ == '__main__':
    diff.run()

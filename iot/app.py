import os
from StringIO import StringIO
from datetime import timedelta
from functools import wraps, partial

import pyotp
import qrcode
from bson.objectid import ObjectId
from fabric.context_managers import settings
from fabric.operations import run, sudo
from fabric.state import env
from flask import Flask, render_template, jsonify, json, request, redirect, session, url_for, send_file, flash
from pymongo import MongoClient

# TODO add flask_ipblock
# from flask_ipblock import IPBlock
# from flask_ipblock.documents import IPNetwork

app = Flask(__name__, template_folder='templates')
app.permanent_session_lifetime = timedelta(minutes=3)

app.config.update(
    DEBUG=True,
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(64))
)

client = MongoClient(os.environ.get('MONGODB_URI', None))
db = client.get_default_database()

device_detail = {
    'device': None,
    'ip': None,
    'username': None,
    'password': None,
    'port': None,
    'id': None

}


def authenticate(otp, u):
    try:
        p = int(otp)
        t = pyotp.TOTP(u)
    except ValueError:
        return False
    return t.verify(str(p))


def check_token(u):
    @wraps(u)
    def totp(*args, **kwargs):
        otp = request.json['info']['token']
        key = session['key']
        otp_auth = authenticate(otp, key) if otp and key else None
        if otp_auth:
            flash('Error')
            return redirect(url_for('update_device', next=request.url))
        return u(*args, **kwargs)

    return totp


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session:
            return redirect(url_for('index', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    if session:
        return render_template('manager.html')
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    user = db.users.find_one({'email': request.form['email']})
    u = partial(type, "user", ())(user or {'invalid': True})
    if hasattr(u, 'invalid'):
        flash('Invalid email address.', 'danger')
    else:
        token = request.form['token']
        if authenticate(token, u.key):
            session.permanent = True
            session[u.email] = True
            session['email'] = u.email
            session['key'] = u.key
            return redirect(url_for('index'))
        else:
            flash('Invalid one-time password!', 'danger')

    return render_template('login.html')


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
@logout_required
def register():
    if request.method == 'POST':

        existing_user = db.users.find_one({'email': request.form['email']})

        if existing_user is None:

            if db.users.insert({'email': request.form['email'], 'key': pyotp.random_base32()}):
                user = partial(type, "user", ())(db.users.find_one({'email': request.form['email']}))

                session.permanent = True
                session[user.email] = True
                session['email'] = user.email
                session['key'] = user.key

                return render_template('qrcode.html', user=user)

        flash('Invalid email or user already exists.', 'danger')

    return render_template('register.html')


@app.route("/addDevice", methods=['POST'])
@login_required
@check_token
def add_device():
    try:
        json_data = request.json['info']
        device_name = json_data['device']
        ip_address = json_data['ip']
        user_name = json_data['username']
        password = json_data['password']
        port_number = json_data['port']

        db.Devices.insert_one({
            'device': device_name, 'ip': ip_address, 'username': user_name, 'password': password, 'port': port_number
        })
        return jsonify(status='OK', message='inserted successfully')

    except Exception as e:
        return jsonify(status='ERROR', message=str(e))


@app.route('/getDevice', methods=['POST'])
@login_required
def get_device():
    try:
        device_id = request.json['id']
        device = db.Devices.find_one({'_id': ObjectId(device_id)})
        device_detail['device'] = device['device']
        device_detail['ip'] = device['ip']
        device_detail['username'] = device['username']
        device_detail['password'] = device['password']
        device_detail['port'] = device['port']
        device_detail['id'] = str(device['_id'])
        return json.dumps(device_detail)
    except Exception as e:
        return str(e)


@app.route('/updateDevice', methods=['POST'])
@login_required
@check_token
def update_device():
    try:
        device_info = request.json['info']
        device_id = device_info['id']
        device = device_info['device']
        ip = device_info['ip']
        username = device_info['username']
        password = device_info['password']
        port = device_info['port']

        db.Devices.update_one({'_id': ObjectId(device_id)}, {
            '$set': {'device': device, 'ip': ip, 'username': username, 'password': password, 'port': port}})
        return jsonify(status='OK', message='updated successfully')
    except Exception as e:
        return jsonify(status='ERROR', message=str(e))


@app.route("/deleteDevice", methods=['POST'])
@login_required
@check_token
def delete_device():
    try:
        device_id = request.json['id']
        db.Devices.remove({'_id': ObjectId(device_id)})
        return jsonify(status='OK', message='deletion successful')
    except Exception as e:
        return jsonify(status='ERROR', message=str(e))


@app.route("/getDeviceList", methods=['POST'])
@login_required
def get_device_list():
    try:
        devices = db.Devices.find()
        device_list = []
        for device in devices:
            device_detail['device'] = device['device']
            device_detail['ip'] = device['ip']
            device_detail['username'] = device['username']
            device_detail['password'] = device['password']
            device_detail['port'] = device['port']
            device_detail['id'] = str(device['_id'])
            device_list.append(device_detail)
    except Exception as e:
        return str(e)
    return json.dumps(device_list)


@app.route("/execute", methods=['POST'])
@login_required
def execute():
    try:
        device_info = request.json['info']
        ip = device_info['ip']
        username = device_info['username']
        password = device_info['password']
        command = device_info['command']
        is_root = device_info['isRoot']

        env.host_string = username + '@' + ip
        env.password = password

        with settings(warn_only=True):
            if is_root:
                resp = sudo(command)
            else:
                resp = run(command)

        return jsonify(status='OK', message=resp)
    except Exception as e:
        print('Error is {}'.format(str(e)))
        return jsonify(status='ERROR', message=str(e))


@app.route('/qr/<email>')
def qr(email):
    """
    Return a QR code for the secret key associated with the given email
    address. The QR code is returned as file with MIME type image/png.
    """
    user = db.users.find_one({'email': email})
    u = partial(type, "user", ())(user)

    if u is None:
        return ''

    t = pyotp.TOTP(u.key)
    q = qrcode.make(t.provisioning_uri(u.email))

    img = StringIO()
    q.save(img)
    img.seek(0)

    return send_file(img, mimetype="image/png")


@app.errorhandler(400)
def page_not_found(e):
    app.logger.erro(e)
    return render_template('400.html'), 400


@app.errorhandler(404)
def page_not_found(e):
    app.logger.erro(e)
    return render_template('404.html'), 404


@app.errorhandler(405)
def page_not_found(e):
    app.logger.erro(e)
    return render_template('405.html'), 405


if __name__ == "__main__":
    app.run(host='0.0.0.0')

import os

from flask import Flask, jsonify, request, render_template, send_from_directory

import db

app = Flask(__name__)
db.init_db()

DEMO_MODE = os.environ.get('DEMO_MODE') == '1'


@app.route('/')
def index():
    return render_template('index.html', demo_mode=DEMO_MODE)


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(db.get_all())


@app.route('/api/state/<key>', methods=['PUT'])
def put_state(key):
    body = request.get_json(force=True)
    db.set_kv(key, body['value'])
    return jsonify({'ok': True})


@app.route('/api/state/<key>', methods=['DELETE'])
def delete_state(key):
    db.delete_kv(key)
    return jsonify({'ok': True})


@app.route('/api/export', methods=['GET'])
def export_data():
    return jsonify(db.export_all())


@app.route('/api/import', methods=['POST'])
def import_data():
    body = request.get_json(force=True)
    if not body:
        return jsonify({'error': 'empty payload'}), 400
    db.import_all(body)
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

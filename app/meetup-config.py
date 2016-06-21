from flask import Flask, render_template, request, redirect
from flaskext.mysql import MySQL
import os
import hvac

app = Flask(__name__)

mysql = MySQL()

vault_token = os.environ.get('VAULT_TOKEN')
client = hvac.Client(url='http://vault:9000', token=vault_token)
mysql_credentials = client.read('mysql/creds/all')

credentials = mysql_credentials['data']

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = credentials['username']
app.config['MYSQL_DATABASE_PASSWORD'] = credentials['password']
app.config['MYSQL_DATABASE_DB'] = 'sydney'
app.config['MYSQL_DATABASE_HOST'] = 'mysql'
mysql.init_app(app)



@app.route('/', methods=['GET'])
def list_messages():
    messages = []
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * from sydney.messages")
        rows = cursor.fetchall()
        for id,value in rows:
            messages.append(value)
        return render_template('index.html', messages=messages)

    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()
        

@app.route('/messages', methods=['POST'])
def add_message():
    
    _msg = request.form['message']
    app.logger.debug(_msg)
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sydney.messages (message) VALUES (%s)", [_msg])
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        app.logger.debug(e)
        return render_template('error.html',error = str(e))
    
    return redirect("/")


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True)
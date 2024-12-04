from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from engineio.payload import Payload
from dotenv import load_dotenv
from flask_cors import CORS
import pymysql
from urllib.parse import urlparse
import os

load_dotenv()

app = Flask(__name__)


app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

Payload.max_decode_packets = 500
mysql = MySQL(app)
mail = Mail(app)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

def get_db_connection():
    db_url = os.getenv("DB_URL")
    url = urlparse(db_url)

    connection = pymysql.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        db=os.getenv("DB_NAME"),
        port=url.port,
        ssl={'ssl': {'ssl-mode': os.getenv('DB_SSL_MODE', 'REQUIRED')}}
    )
    return connection
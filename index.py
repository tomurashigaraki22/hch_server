import hashlib
import jwt
import datetime
from flask import Flask, request, jsonify, json
import os
from dotenv import load_dotenv
from extensions.extensions import get_db_connection, app, mail
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()


# Secret key for JWT encoding and decoding
SECRET_KEY = os.getenv("SECRET_KEY")

@app.route("/show", methods=["GET"])
def show_users():
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to fetch all users
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        # Define column names for better readability
        column_names = ["id", "email", "password", "balance"]

        # Format the data as a list of dictionaries
        user_list = [dict(zip(column_names, user)) for user in users]

        # Close the cursor and connection
        cur.close()
        conn.close()

        return jsonify({
            'status': 200,
            'message': 'Users retrieved successfully',
            'data': user_list
        }), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 400}), 400



@app.route("/signup", methods=["POST", "GET"])
def userSignup():
    try:
        # Get data from the request
        data = request.get_json()

        email = data['email']
        password = data['password']
        
        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Create a new user with a balance of 0.00
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert user into the database
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        balance DECIMAL DEFAULT 0.00
                      )''')

        # Insert the user into the users table
        cur.execute("INSERT INTO users (email, password, balance) VALUES (%s, %s, %s)", 
                    (email, hashed_password, 0.00))

        conn.commit()
        conn.close()

        # Create JWT token with user details (excluding the password)
        payload = {
            'id': cur.lastrowid,
            'email': email,
            'balance': 0.00,
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return json.jsonify({
            'message': 'Account created successfully',
            'token': token,
            'status': 200
        }), 200

    except Exception as e:
        return json.jsonify({'error': str(e)}), 400


@app.route("/login", methods=["POST"])
def userLogin():
    try:
        # Get login data
        data = request.get_json()
        email = data['email'].strip()
        password = data['password'].strip()
        print(f"Login email and pass: {email} {password}")

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    balance DECIMAL DEFAULT 0.00
                    )''')


        # Retrieve user by email
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user or not check_password_hash(user[2], password):
            return json.jsonify({'message': 'Invalid credentials', 'status': 401}), 401

        # Create JWT token for the user
        payload = {
            'id': user[0],  # user[0] is the user ID
            'email': user[1],  # user[1] is the user email
            'balance': float(user[3]),  # user[3] is the user balance
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return json.jsonify({
            'message': 'Login successful',
            'token': token,
            'status': 200
        }), 200

    except Exception as e:
        return json.jsonify({'error': str(e), 'status': 400}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234, use_reloader=True, debug=True)

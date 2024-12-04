import hashlib
import jwt
import datetime
from flask import Flask, request, jsonify, json
import os
import pymysql
from flask_mail import Message, Mail
from dotenv import load_dotenv
from extensions.extensions import get_db_connection, app, mail
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()


# Secret key for JWT encoding and decoding
SECRET_KEY = os.getenv("SECRET_KEY")

@app.route("/welcome", methods=["GET"])
def welcome():
    try:
        data = request.get_json()
        email = data['email']
        subject = "Registration Successful"
        body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    background-color: #ffffff;
                    width: 600px;
                    margin: 20px auto;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                h2 {{
                    color: #4CAF50;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                p {{
                    font-size: 16px;
                    color: #555;
                    line-height: 1.6;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #aaa;
                }}
                .footer a {{
                    color: #4CAF50;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <h2>Welcome, {email}!</h2>
                <p>Congratulations, your registration was successful. We're excited to have you with us!</p>
                <p>You can now log in to your account and start exploring our platform.</p>
                <div class="footer">
                    <p>&copy; 2024 HCHBet. All rights reserved.</p>
                    <p><a href="https://hchbet.vercel.app">Visit our site</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create the message
        msg = Message(subject=subject,
                      recipients=[email],
                      html=body)

        # Send the email
        mail.send(msg)
        return jsonify({
            'status': 200,
            'message': "email sent"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route("/send_email", methods=["GET", "POST"])
def sendEmail():
    try:
        # Get user data from the database (example: based on email)
        data = request.get_json()
        email = data['email']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            # Send email to the user
            subject = "Account Activation and Game Access"
            body = """
                <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f4f4f9;
                            margin: 0;
                            padding: 0;
                        }
                        .email-container {
                            background-color: #ffffff;
                            width: 600px;
                            margin: 20px auto;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        }
                        h2 {
                            color: #333;
                            font-size: 24px;
                            margin-bottom: 10px;
                        }
                        p {
                            font-size: 16px;
                            color: #555;
                            line-height: 1.6;
                        }
                        .footer {
                            text-align: center;
                            margin-top: 20px;
                            font-size: 12px;
                            color: #aaa;
                        }
                        .footer a {
                            color: #333;
                            text-decoration: none;
                        }
                    </style>
                </head>
                <body>
                    <div class="email-container">
                        <h2>Your account will be activated soon!</h2>
                        <p>Thank you for your payment. Your account is currently being processed and will be activated shortly.</p>
                        <p>The game you paid for will be accessible as soon as your account is activated. Please stay tuned for further updates!</p>
                        <div class="footer">
                            <p>&copy; 2024 HCHBet. All rights reserved.</p>
                            <p><a href="https://www.hchbet.com">Visit our site</a></p>
                        </div>
                    </div>
                </body>
                </html>
            """
            
            # Create a message
            msg = Message(subject=subject,
                          recipients=[email],
                          html=body)

            # Send the email
            mail.send(msg)

            return jsonify({
                'message': 'Email sent successfully',
                'status': 200
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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


@app.route("/update_balance", methods=["POST"])
def update_balance():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Extract the email and amount to add from the received data
        email = data.get("email")
        amount_to_add = data.get("amount")

        # Ensure that email and amount_to_add are provided
        if not email or amount_to_add is None:
            return jsonify({"error": "Email and amount are required"}), 400

        # Establish a database connection
        conn = get_db_connection()
        cur = conn.cursor()

        # Query to check if the user exists
        cur.execute("SELECT balance FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            # If user does not exist, return an error
            return jsonify({"error": "User not found"}), 404

        current_balance = user[0]  # Get the current balance

        # Add the amount to the current balance
        new_balance = current_balance + amount_to_add

        # Update the user's balance in the database
        cur.execute("UPDATE users SET balance = %s WHERE email = %s", (new_balance, email))
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()

        # Return a success response
        return jsonify({"message": "Balance updated successfully", "new_balance": new_balance}), 200

    except pymysql.MySQLError as e:
        # If there's an error with the database, return an error message
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        # Handle any other errors
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/signup", methods=["POST", "GET"])
def userSignup():
    try:
        # Get data from the request
        data = request.get_json()

        email = data['email'].strip()
        password = data['password'].strip()
        
        # Check if email is already in the database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            return json.jsonify({'error': 'Email already registered', "message": "Email already registered", "status": 400}), 400

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Create the users table if it doesn't exist
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        balance DECIMAL DEFAULT 0.00
                      )''')

        # Insert the new user into the database
        cur.execute("INSERT INTO users (email, password, balance) VALUES (%s, %s, %s)", 
                    (email, hashed_password, 0.00))

        conn.commit()

        # Get the user's ID (last inserted row ID)
        user_id = cur.lastrowid
        conn.close()

        # Create JWT token with user details (excluding the password)
        payload = {
            'id': user_id,
            'email': email,
            'balance': 0.00,
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        subject = "Registration Successful"
        body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    background-color: #ffffff;
                    width: 600px;
                    margin: 20px auto;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                h2 {{
                    color: #4CAF50;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                p {{
                    font-size: 16px;
                    color: #555;
                    line-height: 1.6;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #aaa;
                }}
                .footer a {{
                    color: #4CAF50;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <h2>Welcome, {email}!</h2>
                <p>Congratulations, your registration was successful. We're excited to have you with us!</p>
                <p>You can now log in to your account and start exploring our platform.</p>
                <div class="footer">
                    <p>&copy; 2024 HCHBet. All rights reserved.</p>
                    <p><a href="https://hchbet.vercel.app">Visit our site</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create the message
        msg = Message(subject=subject,
                      recipients=[email],
                      html=body)

        # Send the email
        mail.send(msg)

        return json.jsonify({
            'message': 'Account created successfully',
            'token': token,
            'status': 200
        }), 200

    except Exception as e:
        return json.jsonify({'error': str(e), 'status': 400, 'message': str(e)}), 400



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

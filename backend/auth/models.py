from datetime import datetime
from pymongo import MongoClient
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        try:
            # Fetch MongoDB URI from environment variable
            connection_string = os.getenv('MONGODB_URI')
            
            if not connection_string:
                raise ValueError("MONGODB_URI environment variable is not set.")

            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=50000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                retryWrites=True,
                tls=False
            )

            # Test the connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")

            # Connect to the database
            self.db = self.client["myuser"]  # "myuser" is the database name
            self.users = self.db["collect"]  # "collect" is the collection name
            self.backtests = self.db["backtests"]

            # Create an index for email (if needed)
            try:
                self.users.create_index('email', unique=True)
            except Exception as e:
                print(f"Warning: Could not create index: {str(e)}")

        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            raise Exception("Could not connect to database. Please check your connection string and network connection.")



    def get_latest_backtest_results(self):
        """Fetch the latest backtest result from the database."""
        latest_result = self.db.backtests.find_one(sort=[("_id", -1)])  # Fetch latest entry
        return latest_result if latest_result else {"message": "No backtest results found"}

class User:
    def __init__(self, db):
        self.db = db
        self.collection = db.users
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key')

    def create_user(self, email, password):
        try:
            # Hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            user = {
                'email': email,
                'password': hashed,
                'created_at': datetime.utcnow(),
                'reports': [],
                'settings': {
                    'default_timeframe': '1h',
                    'notifications_enabled': True
                }
            }
            
            result = self.collection.insert_one(user)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")

    def authenticate(self, email, password):
        user = self.collection.find_one({'email': email})
        if not user:
            return None
            
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            token = jwt.encode(
                {
                    'user_id': str(user['_id']),
                    'email': user['email'],
                    'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
                },
                self.jwt_secret,
                algorithm='HS256'
            )
            return {
                'token': token,
                'user': {
                    'id': str(user['_id']),
                    'email': user['email']
                }
            }
        return None

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except:
            return None

    def get_user_by_id(self, user_id):
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            user = self.collection.find_one({'_id': object_id})
            if user:
                user['_id'] = str(user['_id'])  # Convert ObjectId back to string
                user.pop('password', None)  # Remove password from response
                return user
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None

    def update_user(self, user_id, updates):
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            if 'password' in updates:
                updates['password'] = bcrypt.hashpw(
                    updates['password'].encode('utf-8'), 
                    bcrypt.gensalt()
                )
            result = self.collection.update_one(
                {'_id': object_id},
                {'$set': updates}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return False 
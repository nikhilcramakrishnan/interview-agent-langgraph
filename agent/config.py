import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
database_name = os.getenv("MONGODB_DB_NAME", "interviewDB")

client = None
db = None


try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster') # Check connection
    db = client[database_name]
    print(f"MongoDB connection successful! Connected to database: {database_name}")
except ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}")
    print("Please ensure MongoDB is running and accessible.")
    client = None
    db = None
except Exception as e:
    print(f"An unexpected error occurred during MongoDB connection: {e}")
    client = None
    db = None

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

TOTAL_QUESTIONS_PLANNED = int(os.getenv("NUM_QUESTIONS"))

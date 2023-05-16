from config import MONGO_DB_NAME, MONGO_DB_URI
from pymongo import MongoClient

client = MongoClient(host=MONGO_DB_URI)
database = client[MONGO_DB_NAME]

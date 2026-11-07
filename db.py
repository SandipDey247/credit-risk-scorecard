import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

#load data from .env file
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")

required = {
	"DB_USER": user,
	"DB_PASSWORD": password,
	"DB_HOST": host,
	"DB_PORT": port,
	"DB_NAME": database,
}

#handling missing env variable from
missing = [k for k, v in required.items() if v is None]
if missing:
	raise ValueError(f"Missing environment variables: {', '.join(missing)}")

assert password is not None, "DB_PASSWORD environment variable is not set"

#encode password using quote_plus
encoded_password = urllib.parse.quote_plus(password)
database_url = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/{database}"

#connecting database
try:
	engine = create_engine(database_url)
	
	with engine.connect() as connection:
		result = connection.execute(text("SELECT VERSION()"))
		print("Connection successful!")
		print("MySQL Version:", result.scalar())

except Exception as exc:
	raise RuntimeError("Database connection failed!") from exc
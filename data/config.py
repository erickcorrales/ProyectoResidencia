

# data/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # lee .env si existe

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "pizzas")

PAGE_TITLE = "Ventas Pizzas - Dashboard"
PAGE_LAYOUT = "wide"

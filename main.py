from database import create_tables
from crawler import LeetCodeCrawler
from renderer import render_anki

# create database
create_tables()

# start crawler
worker = LeetCodeCrawler()
worker.login()
worker.fetch_accepted_problems()

# render anki
render_anki()
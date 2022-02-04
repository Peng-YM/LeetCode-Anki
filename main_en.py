from database_en import create_tables
from crawler_en import LeetCodeCrawler
from renderer_en import render_anki

# create database
create_tables()

# start crawler
worker = LeetCodeCrawler()
worker.login()
worker.fetch_accepted_problems()

# render anki
render_anki()
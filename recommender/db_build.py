## This script is used to create the tables in the database

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

password = os.getenv("POSTGRES_PASSWORD")
CONNECTION = f"postgresql://postgres:{password}@localhost:5432/postgres"
# need to run this to enable vector data type
CREATE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS vector"

# TODO: Add create table statement
CREATE_PODCAST_TABLE = """
CREATE TABLE IF NOT EXISTS Podcast (
id VARCHAR(255) PRIMARY KEY,
title TEXT NOT NULL
);
"""
# TODO: Add create table statement
CREATE_SEGMENT_TABLE = """
CREATE TABLE IF NOT EXISTS Segment (
id VARCHAR(255) PRIMARY KEY,
start_time FLOAT,
end_time FLOAT,
content TEXT NOT NULL,
embedding vector(128) NOT NULL,
podcast_id VARCHAR(255) NOT NULL,
FOREIGN KEY (podcast_id) REFERENCES podcast(id)
);
"""

conn = psycopg2.connect(CONNECTION)
# TODO: Create tables with psycopg2 (example: https://www.geeksforgeeks.org/executing-sql-query-with-psycopg2-in-python/)
cur = conn.cursor()

cur.execute(CREATE_EXTENSION)
cur.execute(CREATE_PODCAST_TABLE)
cur.execute(CREATE_SEGMENT_TABLE)

conn.commit()
cur.close()
conn.close()


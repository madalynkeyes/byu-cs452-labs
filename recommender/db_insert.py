## This script is used to insert data into the database
import os
import json
from dotenv import load_dotenv
from datasets import load_dataset
import pandas as pd
import glob

import psycopg2

from utils import fast_pg_insert

load_dotenv()

password = os.getenv("POSTGRES_PASSWORD")
CONNECTION = f"postgresql://postgres:{password}@localhost:5432/postgres"

# Read the embedding files
print("Parsing the embedding files...")
embedding_files = sorted(glob.glob("data/embedding/embedding/*.jsonl"))

# with open(embedding_files[0], encoding="utf-8") as f:
#     first = json.loads(f.readline())
# print(first.keys())
# print(first["custom_id"])
# print(first["response"]["body"]["data"][0]["embedding"])

embedding_rows = []
for path in embedding_files:
    with open(path,encoding="utf-8") as f:
        for line in f:
            response = json.loads(line)
            if response["response"]["status_code"] != 200:
                continue
            embedding_rows.append({
                "custom_id":response["custom_id"],
                "embedding":response["response"]["body"]["data"][0]["embedding"]
            })

emb_response_dataframe = pd.DataFrame(embedding_rows)
# print(emb_response_dataframe.shape)
# print(emb_response_dataframe.head())


# Read documents files
print("Parsing the document files...")
documents_files = sorted(glob.glob("data/documents/documents/batch_request_*.jsonl"))

# with open(documents_files[0], encoding="utf-8") as f:
#     first = json.loads(f.readline())
# print(first.keys())
# print(first["body"]["metadata"])

document_rows = []
for path in documents_files:
    with open(path,encoding="utf-8") as f:
        for line in f:
            request = json.loads(line)
            metadata = request["body"]["metadata"]
            document_rows.append({
                "id":request["custom_id"],
                "content": request["body"]["input"],
                "podcast_id": metadata["podcast_id"],
                "title": metadata["title"],
                "start_time": metadata["start_time"],
                "end_time": metadata["stop_time"]
            })

batch_request_dataframe = pd.DataFrame(document_rows)
# print(batch_request_dataframe.shape)
# print(batch_request_dataframe.head())
# print(batch_request_dataframe["podcast_id"].nunique()) 

print("Merging embedding and document dataframes...")
merged_df = pd.merge(batch_request_dataframe, emb_response_dataframe,
                     left_on="id", right_on="custom_id", how="inner")
merged_df = merged_df.drop(columns=["custom_id"])
# print(merged_df.shape)
# print(merged_df.head())
# print(merged_df.columns)

segment_df = merged_df[["id","start_time","end_time","content","embedding","podcast_id"]].copy()
segment_df["content"] = segment_df["content"].str.strip()
podcast_df = merged_df[["podcast_id","title"]].copy()
podcast_df = podcast_df.rename(columns={"podcast_id":"id"})
podcast_df["title"] = podcast_df["title"].str.replace("Podcast: ","",n=1)
podcast_df = podcast_df.drop_duplicates()
# print(podcast_df.shape)
# print(podcast_df.head())
# print(segment_df.shape)
# print(segment_df.head())


# Clear the tables if data has already be put in them
print("Cleaning up database...")
conn = psycopg2.connect(CONNECTION)
cur = conn.cursor()
cur.execute("TRUNCATE segment, podcast;")
conn.commit()
cur.close()
conn.close()

# Insert into postgres
print("Beginning inserts for podcast table...")
fast_pg_insert(podcast_df,CONNECTION,"podcast",["id","title"])
print("Podcast data inserted.")
print("Beginning inserts for segment table...")
fast_pg_insert(segment_df, CONNECTION, "segment", ["id", "start_time", "end_time", "content", "embedding", "podcast_id"])
print("Segment data inserted.")
print("To view tables in postgres: 'docker exec -it pgvector psql -U postgres', then type SELECT statements, use '\q' to exit postgres")
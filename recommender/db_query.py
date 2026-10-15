## This script is used to query the database
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("POSTGRES_PASSWORD")
CONNECTION = f"postgresql://postgres:{password}@localhost:5432/postgres"

SIMILAR_SEGMENTS = """
WITH seg_limit AS (
    SELECT id, content, start_time, end_time, podcast_id,
           embedding <-> (SELECT embedding FROM segment WHERE id = %(seg_id)s) AS distance
    FROM segment
    WHERE id != %(seg_id)s
    ORDER BY distance
    LIMIT 5
)
SELECT podcast.title, seg_limit.id AS segment_id, content,
       start_time, end_time, distance
FROM seg_limit
JOIN podcast ON seg_limit.podcast_id = podcast.id
ORDER BY distance;
"""

DISSIMILAR_SEGMENTS = """
WITH seg_limit AS (
    SELECT id, content, start_time, end_time, podcast_id,
           embedding <-> (SELECT embedding FROM segment WHERE id = %(seg_id)s) AS distance
    FROM segment
    WHERE id != %(seg_id)s
    ORDER BY distance DESC
    LIMIT 5
)
SELECT podcast.title, seg_limit.id AS segment_id, content,
       start_time, end_time, distance
FROM seg_limit
JOIN podcast ON seg_limit.podcast_id = podcast.id
ORDER BY distance;
"""

SIMILAR_EPISODES_TO_SEGMENT = """
WITH episode_avg AS (
    -- One vector per episode: the average of all its segment vectors
    SELECT podcast_id, AVG(embedding) AS avg_embedding
    FROM segment
    GROUP BY podcast_id
)
SELECT podcast.title,
       e.avg_embedding <-> (SELECT embedding FROM segment WHERE id = %(seg_id)s) AS distance
FROM episode_avg e
JOIN podcast ON e.podcast_id = podcast.id
-- Exclude the episode the query segment comes from
WHERE e.podcast_id != (SELECT podcast_id FROM segment WHERE id = %(seg_id)s)
ORDER BY distance
LIMIT 5;
"""

SIMILAR_EPISODES_TO_EPISODE = """
WITH episode_avg AS (
    SELECT podcast_id, AVG(embedding) AS avg_embedding
    FROM segment
    GROUP BY podcast_id
)
SELECT podcast.title,
       e.avg_embedding <-> (SELECT avg_embedding FROM episode_avg
                            WHERE podcast_id = %(ep_id)s) AS distance
FROM episode_avg e
JOIN podcast ON e.podcast_id = podcast.id
WHERE e.podcast_id != %(ep_id)s
ORDER BY distance
LIMIT 5;
"""

import pandas as pd

conn = psycopg2.connect(CONNECTION)

# def run(label, sql, params):
#     df = pd.read_sql(sql, conn, params=params)
#     print(f"\n=== {label} ===")
#     print(f"```{sql}```")
#     print(df.to_markdown(tablefmt="grid",maxcolwidths=30))
html_parts = []

def run(label, sql, params):
    df = pd.read_sql(sql, conn, params=params)
    html_parts.append(f"<h2>{label}</h2>")
    html_parts.append(f"<pre>{sql}</pre>")
    html_parts.append(df.to_html(index=False))

run("Q1: similar to 267:476",  SIMILAR_SEGMENTS, {"seg_id": "267:476"})
run("Q2: dissimilar to 267:476", DISSIMILAR_SEGMENTS, {"seg_id":"267:476"})
run("Q3: similar to 48:511",   SIMILAR_SEGMENTS, {"seg_id": "48:511"})
run("Q4: similar to 51:56",    SIMILAR_SEGMENTS, {"seg_id": "51:56"})

for seg in ["267:476", "48:511", "51:56"]:
    run(f"Q5: episodes similar to segment {seg}", SIMILAR_EPISODES_TO_SEGMENT, {"seg_id": seg})

run("Q6: episodes similar to VeH7qKZr0WI", SIMILAR_EPISODES_TO_EPISODE, {"ep_id": "VeH7qKZr0WI"})

conn.close()

style = """
<style>
  body { font-family: Arial, sans-serif; font-size: 11px; margin: 20px; }
  pre  { background: #f4f4f4; padding: 8px; font-size: 10px; white-space: pre-wrap; }
  table { border-collapse: collapse; width: 100%; margin-bottom: 24px; }
  th, td { border: 1px solid #999; padding: 4px; vertical-align: top; text-align: left; }
  th { background: #e8e8e8; }
</style>
"""

with open("results.html", "w", encoding="utf-8") as f:
    f.write("<html><head><meta charset='utf-8'>" + style + "</head><body>")
    f.write("<h1>Podcast Recommender: Query Results</h1>")
    f.write("\n".join(html_parts))
    f.write("</body></html>")
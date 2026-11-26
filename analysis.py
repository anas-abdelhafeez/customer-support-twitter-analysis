"""Customer support on Twitter: response time and workload analysis.

Input : twcs.csv (Kaggle "Customer Support on Twitter", ~2.8M tweets)
Output: extracts/*.csv, extracts/*.hyper (Tableau), results.json

Run:  python analysis.py --csv path/to/twcs.csv
"""
import argparse, json, os
import duckdb

SQL_FRT = """
CREATE OR REPLACE TABLE tweets AS
SELECT CAST(tweet_id AS BIGINT) AS tweet_id, author_id, LOWER(inbound) = 'true' AS inbound,
       COALESCE(TRY_STRPTIME(created_at, '%a %b %d %H:%M:%S +0000 %Y'), TRY_CAST(created_at AS TIMESTAMP)) AS created_at,
       response_tweet_id, TRY_CAST(in_response_to_tweet_id AS BIGINT) AS in_response_to
FROM read_csv_auto('{csv}', header=true, all_varchar=true);

-- one row per customer conversation opener (a customer tweet that is not itself a reply)
CREATE OR REPLACE TABLE openers AS
SELECT tweet_id, author_id AS customer, created_at AS asked_at
FROM tweets WHERE inbound AND in_response_to IS NULL AND created_at >= TIMESTAMP '2017-10-01';

-- first brand reply to each opener
CREATE OR REPLACE TABLE frt AS
SELECT o.tweet_id, o.customer, o.asked_at, b.author_id AS brand,
       MIN(b.created_at) AS replied_at,
       DATE_DIFF('second', o.asked_at, MIN(b.created_at)) / 60.0 AS frt_min
FROM openers o JOIN tweets b ON b.in_response_to = o.tweet_id AND NOT b.inbound
GROUP BY o.tweet_id, o.customer, o.asked_at, b.author_id;
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--out', default='extracts')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    con = duckdb.connect()
    con.execute(SQL_FRT.format(csv=a.csv.replace("'", "''")))
    # keep one reply row per opener (earliest brand)
    con.execute("""CREATE OR REPLACE TABLE frt1 AS
      SELECT * EXCLUDE rn FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY tweet_id ORDER BY replied_at) rn FROM frt) WHERE rn = 1""")
    n_old = con.execute("SELECT COUNT(*) FROM tweets WHERE inbound AND in_response_to IS NULL AND created_at < TIMESTAMP '2017-10-01'").fetchone()[0]
    n_tw = con.execute("SELECT COUNT(*) FROM tweets").fetchone()[0]
    n_open = con.execute("SELECT COUNT(*) FROM openers").fetchone()[0]
    n_ans = con.execute("SELECT COUNT(*) FROM frt1").fetchone()[0]
    brands = con.execute("SELECT COUNT(DISTINCT author_id) FROM tweets WHERE NOT inbound").fetchone()[0]
    q = con.execute("SELECT quantile_cont(frt_min,[0.1,0.25,0.5,0.75,0.9,0.95,0.99]), AVG(frt_min), "
                    "AVG((frt_min<=60)::INT), AVG((frt_min<=240)::INT) FROM frt1").fetchone()
    res = dict(excluded_pre_oct_2017=n_old, tweets=n_tw, conversations=n_open, answered=n_ans, brands=brands,
               answered_pct=round(100 * n_ans / n_open, 1), unanswered=n_open - n_ans,
               percentiles=dict(zip(['p10', 'p25', 'p50', 'p75', 'p90', 'p95', 'p99'], [round(x, 1) for x in q[0]])),
               mean_min=round(q[1], 1), within_1h_pct=round(100 * q[2], 1), within_4h_pct=round(100 * q[3], 1))
    # Tableau-ready tables
    tables = {
      'brand_summary': """SELECT brand, COUNT(*) AS answered_conversations, ROUND(quantile_cont(frt_min,0.5),1) AS median_frt_min,
            ROUND(quantile_cont(frt_min,0.9),1) AS p90_frt_min, ROUND(100*AVG((frt_min<=60)::INT),1) AS within_1h_pct,
            ROUND(100*AVG((frt_min<=240)::INT),1) AS within_4h_pct FROM frt1 GROUP BY brand HAVING COUNT(*) >= 500 ORDER BY 2 DESC""",
      'daily_volume': """SELECT CAST(asked_at AS DATE) AS day, COUNT(*) AS conversations FROM openers GROUP BY 1 ORDER BY 1""",
      'hour_weekday': """SELECT DAYOFWEEK(asked_at) AS dow, DAYNAME(asked_at) AS weekday, HOUR(asked_at) AS hour, COUNT(*) AS conversations
            FROM openers GROUP BY 1,2,3 ORDER BY 1,3""",
      'frt_buckets': """SELECT CASE WHEN frt_min<=5 THEN '1. 0-5 min' WHEN frt_min<=15 THEN '2. 5-15 min' WHEN frt_min<=30 THEN '3. 15-30 min'
            WHEN frt_min<=60 THEN '4. 30-60 min' WHEN frt_min<=240 THEN '5. 1-4 h' WHEN frt_min<=1440 THEN '6. 4-24 h' ELSE '7. over 24 h' END AS bucket,
            COUNT(*) AS conversations FROM frt1 GROUP BY 1 ORDER BY 1""",
      'frt_by_hour': """SELECT HOUR(asked_at) AS hour, COUNT(*) AS answered, ROUND(quantile_cont(frt_min,0.5),1) AS median_frt_min,
            ROUND(quantile_cont(frt_min,0.9),1) AS p90_frt_min, ROUND(100*AVG((frt_min<=60)::INT),1) AS within_1h_pct FROM frt1 GROUP BY 1 ORDER BY 1""",
      'brand_hour': """SELECT brand, HOUR(asked_at) AS hour, COUNT(*) AS conversations, ROUND(quantile_cont(frt_min,0.5),1) AS median_frt_min
            FROM frt1 WHERE brand IN (SELECT brand FROM frt1 GROUP BY brand HAVING COUNT(*)>=5000) GROUP BY 1,2 ORDER BY 1,2""",
    }
    import pandas as pd
    frames = {}
    for name, sql in tables.items():
        df = con.execute(sql).df()
        df.to_csv(f'{a.out}/{name}.csv', index=False)
        frames[name] = df
    res['brand_table'] = frames['brand_summary'].head(20).to_dict('records')
    try:
        import pantab
        pantab.frames_to_hyper(frames, f'{a.out}/support_extracts.hyper')
        res['hyper'] = 'extracts/support_extracts.hyper'
    except Exception as e:  # Tableau extract is optional
        res['hyper'] = f'skipped: {e}'
    json.dump(res, open('results.json', 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k != 'brand_table'}, indent=1, default=str))

if __name__ == '__main__':
    main()

"""Checks first-response-time logic on a tiny hand-made fixture (not real data)."""
import csv, subprocess, sys, json, os, tempfile

ROWS = [
 # tweet_id, author_id, inbound, created_at, text, response_tweet_id, in_response_to_tweet_id
 (1, 'c1', 'True',  'Mon Oct 02 10:00:00 +0000 2017', 'help', '2',  ''),
 (2, 'BrandA', 'False', 'Mon Oct 02 10:10:00 +0000 2017', 'hi', '', '1'),
 (3, 'c2', 'True',  'Mon Oct 02 11:00:00 +0000 2017', 'help', '4,5', ''),
 (4, 'BrandA', 'False', 'Mon Oct 02 15:00:00 +0000 2017', 'late', '', '3'),
 (5, 'BrandA', 'False', 'Mon Oct 02 11:30:00 +0000 2017', 'first', '', '3'),
 (6, 'c3', 'True',  'Mon Oct 02 12:00:00 +0000 2017', 'ignored', '', ''),
 (7, 'c4', 'True',  'Mon Oct 02 13:00:00 +0000 2016', 'old', '', ''),
]

def run():
    d = tempfile.mkdtemp()
    p = os.path.join(d, 't.csv')
    with open(p, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['tweet_id','author_id','inbound','created_at','text','response_tweet_id','in_response_to_tweet_id']); w.writerows(ROWS)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, os.path.join(here, 'analysis.py'), '--csv', p, '--out', os.path.join(d, 'x')], check=True, cwd=d, capture_output=True)
    return json.load(open(os.path.join(d, 'results.json')))

def test_counts_and_first_reply():
    r = run()
    assert r['conversations'] == 3          # old 2016 opener excluded
    assert r['answered'] == 2               # c3 never answered
    assert r['unanswered'] == 1
    assert r['excluded_pre_oct_2017'] == 1

def test_uses_earliest_brand_reply():
    r = run()
    # waits are 10 min and 30 min (not 240 min): median = 20
    assert r['percentiles']['p50'] == 20.0
    assert r['within_1h_pct'] == 100.0

"""Builds docs/index.html (7-tab dark dashboard) from results.json and extracts/*.csv."""
import json, os
import pandas as pd
from dashboard_lib import *

R = json.load(open('results.json'))
E = 'extracts/'
daily = pd.read_csv(E + 'daily_volume.csv'); hw = pd.read_csv(E + 'hour_weekday.csv')
bk = pd.read_csv(E + 'frt_buckets.csv'); br = pd.read_csv(E + 'brand_summary.csv'); fh = pd.read_csv(E + 'frt_by_hour.csv')
P = R['percentiles']
conv, ans = R['conversations'], R['answered']
unans, unans_pct = R['unanswered'], round(100 * R['unanswered'] / conv, 1)
over4 = round(100 - R['within_4h_pct'], 1)
# dow index: duckdb DAYOFWEEK sunday=0 -> convert to Mon=0
hw['d'] = (hw.dow + 6) % 7
dow_tot = hw.groupby('d').conversations.sum().reindex(range(7))
hour_tot = hw.groupby('hour').conversations.sum()
top6 = sorted(hour_tot.sort_values(ascending=False).head(6).index.tolist())
assert top6 == list(range(top6[0], top6[0]+6)), top6
peak_h = int(hour_tot.idxmax()); trough_h = int(hour_tot.idxmin())
ratio = round(hour_tot.max() / hour_tot.min(), 1)
top = br.sort_values('answered_conversations', ascending=False).head(20).reset_index(drop=True)
fast, slow = top.sort_values('median_frt_min').iloc[0], top.sort_values('median_frt_min').iloc[-1]
gap = round(slow.median_frt_min / fast.median_frt_min)
best_day = DOW[int(dow_tot.idxmax())]; low_day = DOW[int(dow_tot.idxmin())]
worst_p90 = fh.sort_values('p90_frt_min', ascending=False).head(3)
bucket_lbl = [b.split('. ', 1)[1] for b in bk.bucket]
SRC = 'Source: "Customer Support on Twitter" (Kaggle, thoughtvector), real tweets, Oct 1 to Dec 3, 2017. Hours are UTC.'

p = []
p.append(page('1. Problem', lede(f'<b>The problem:</b> customers now ask for help in public. This dataset holds <b>{conv:,} real customer conversations</b> with {R["brands"]} brands on Twitter. Every unanswered or slow reply is visible to the customer\u2019s followers.')
 + kpi([(f'{R["tweets"]/1e6:.2f}M', 'tweets analyzed (customers + brands)'), (f'{conv:,}', 'customer conversations started'), (str(R['brands']), 'brands'),
        (f'{R["answered_pct"]}%', 'of conversations got a brand reply'), (f'{unans_pct}%', 'never got a reply')])
 + '<div class="g"><div class="c w12"><h3>Daily new conversations</h3><small>' + SRC + '</small>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": [d[5:] for d in daily.day], **AX}, "yAxis": {"type": "value", "name": "thousand", "nameTextStyle": {"color": "#9aa6d6"}, **AX},
   "series": [{"type": "line", "showSymbol": False, "data": [round(v / 1000, 1) for v in daily.conversations], "itemStyle": {"color": "#6c8cff"}, "areaStyle": {"opacity": 0.12}}]}}) + '</div></div>'))

p.append(page('2. Impact', lede(f'<b>The damage:</b> the median customer waits <b>{P["p50"]} minutes</b>, but the average is <b>{R["mean_min"]/60:.1f} hours</b>, because a long tail waits half a day or more. <b>{over4}% of answered conversations wait over 4 hours.</b>')
 + kpi([(f'{P["p50"]} min', 'median first response time'), (f'{R["within_1h_pct"]}%', 'answered within 1 hour'), (f'{R["within_4h_pct"]}%', 'answered within 4 hours'), (f'{P["p90"]:.0f} min', '90th percentile wait'), (f'{P["p99"]:,.0f} min', '99th percentile wait')])
 + f'<div class="g"><div class="c w8"><h3>First response time distribution ({ans:,} answered conversations)</h3>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": bucket_lbl, **AX}, "yAxis": {"type": "value", "name": "thousand", "nameTextStyle": {"color": "#9aa6d6"}, **AX},
   "series": [{"type": "bar", "data": [round(v / 1000, 1) for v in bk.conversations], "itemStyle": {"color": "#6c8cff", "borderRadius": [4, 4, 0, 0]}}]}}) + '</div>'
 + '<div class="c w4"><h3>Percentiles</h3>' + tbl([{'Percentile': k, 'Wait': f'{v:,} min'} for k, v in P.items()], ['Percentile', 'Wait']) + '</div></div>'
 + ins('What this means', [f'<b>The median hides the tail:</b> half of customers get an answer in about {P["p50"]:.0f} minutes, but 1 in {round(100/over4)} waits 4+ hours. Track p90, not only the median.',
   f'<b>{unans_pct}% get silence:</b> {unans:,} conversations never got a brand reply, in public.'])))

heat_data = [[int(r.hour), int(r.d), int(r.conversations)] for r in hw.itertuples()]
p.append(page('3. Where', lede(f'<b>Where the pressure sits:</b> inbound demand climbs through the day and peaks around <b>{peak_h:02d}:00 UTC</b>; the quietest hour is {trough_h:02d}:00 UTC, about {ratio}x lower.')
 + '<div class="g"><div class="c w12"><h3>Conversations by hour and day of week (UTC)</h3>'
 + ch(heat(heat_data, DOW, HRS, 'conversations', 0, int(hw.conversations.max())), 'ch t') + '</div></div>'
 + ins('What this means', [f'<b>One long evening peak:</b> the six busiest hours of the day are {min(top6):02d}:00 to {max(top6):02d}:59 UTC, with {int(hour_tot[top6].sum()):,} conversations ({round(100*hour_tot[top6].sum()/hour_tot.sum())}% of the total).',
   f'<b>Weekends are lighter, not empty:</b> {DOW[5]} and {DOW[6]} carry {int(dow_tot[5]):,} and {int(dow_tot[6]):,} conversations vs {int(dow_tot[4]):,} on {DOW[4]}. Social support is a 7-day operation.'])))

sc = [{"value": [int(r.answered_conversations), float(r.median_frt_min)], "name": r.brand} for r in top.itertuples()]
rows = [{'Brand': r.brand, 'Answered': f'{int(r.answered_conversations):,}', 'Median FRT (min)': r.median_frt_min, 'P90 FRT (min)': r.p90_frt_min, 'Within 1h %': r.within_1h_pct} for r in top.itertuples()]
p.append(page('4. Who', lede(f'<b>Who answers well, and who leaves customers waiting:</b> among the 20 busiest brands, the median wait runs from <b>{fast.median_frt_min} min</b> ({fast.brand}) to <b>{slow.median_frt_min:,.0f} min</b> ({slow.brand}), a gap of about <b>{gap}x</b>.')
 + '<div class="g"><div class="c w12"><h3>Volume vs speed: top 20 brands by volume</h3><small>X = answered conversations (log scale), Y = median first response time.</small>'
 + ch({**base(), **{"grid": {"left": 55, "right": 50, "top": 32, "bottom": 40}, "tooltip": {"trigger": "item", "formatter": "{b}: {c}"}, "xAxis": {"type": "log", "min": 9000, "max": 100000, "name": "answered conversations", **AX}, "yAxis": {"type": "value", "name": "median FRT (min)", **AX},
   "series": [{"type": "scatter", "symbolSize": 14, "data": sc, "itemStyle": {"color": "#ffb454"}, "label": {"show": True, "formatter": "{b}", "position": "right", "color": "#9aa6d6", "fontSize": 10}}]}}, 'ch t') + '</div>'
 + '<div class="c w12"><h3>Brand leaderboard (top 20 by volume)</h3>'
 + tbl(rows, ['Brand', 'Answered', 'Median FRT (min)', 'P90 FRT (min)', 'Within 1h %'], 'Within 1h %', lambda v: 'good' if float(v) >= 80 else ('mid' if float(v) >= 50 else 'bad')) + '</div></div>'
 + ins('What this means', [f'<b>Speed at scale exists:</b> AmazonHelp answers {int(top[top.brand=="AmazonHelp"].answered_conversations.iloc[0]):,} conversations at a {float(top[top.brand=="AmazonHelp"].median_frt_min.iloc[0])}-minute median; AppleSupport has similar volume at {float(top[top.brand=="AppleSupport"].median_frt_min.iloc[0])} minutes.',
   '<b>Volume does not explain the gap.</b> Brands of every size sit at both ends of the chart.'])))

p.append(page('5. Why', lede('<b>Why some customers wait:</b> the median wait barely moves through the day. The tail does. Waits of the slowest 10% jump overnight and again in the evening.')
 + '<div class="g"><div class="c"><h3>Median first response time by hour asked (UTC)</h3><small>Stays between ' + f'{fh.median_frt_min.min():.0f} and {fh.median_frt_min.max():.0f} minutes' + '</small>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": [f"{h:02d}:00" for h in fh.hour], **AX}, "yAxis": {"type": "value", "name": "min", **AX},
   "series": [{"type": "line", "smooth": True, "data": list(fh.median_frt_min), "itemStyle": {"color": "#27d3a2"}, "areaStyle": {"opacity": 0.12}}]}}) + '</div>'
 + '<div class="c"><h3>90th percentile wait by hour asked (UTC)</h3><small>The slow tail</small>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": [f"{h:02d}:00" for h in fh.hour], **AX}, "yAxis": {"type": "value", "name": "min", **AX},
   "series": [{"type": "line", "smooth": True, "data": list(fh.p90_frt_min), "itemStyle": {"color": "#ff6b8b"}, "areaStyle": {"opacity": 0.12}}]}}) + '</div></div>'
 + ins('What this means', [f'<b>The worst tails:</b> conversations started at ' + ', '.join(f'{int(h):02d}:00' for h in worst_p90.hour) + f' UTC have a p90 wait of {worst_p90.p90_frt_min.min():.0f} to {worst_p90.p90_frt_min.max():.0f} minutes.',
   '<b>Limit of this data:</b> the dataset has no staffing or ticket-queue fields, so this shows when waits are long, not why. Coverage gaps are a hypothesis to test, not a finding.'])))

p.append(page('6. When', lede(f'<b>When it happens:</b> {best_day} is the busiest weekday and {low_day} the quietest in this window. The share answered within an hour is highest late at night and lowest around 04:00 UTC.')
 + '<div class="g"><div class="c"><h3>Conversations by day of week</h3>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": DOW, **AX}, "yAxis": {"type": "value", "name": "thousand", **AX},
   "series": [{"type": "bar", "data": [round(v / 1000, 1) for v in dow_tot], "itemStyle": {"color": "#6c8cff", "borderRadius": [4, 4, 0, 0]}}]}}) + '</div>'
 + '<div class="c"><h3>% answered within 1 hour, by hour asked</h3>'
 + ch({**base(), **{"xAxis": {"type": "category", "data": [f"{h:02d}:00" for h in fh.hour], **AX}, "yAxis": {"type": "value", "min": 0, "max": 100, **AX},
   "series": [{"type": "bar", "data": list(fh.within_1h_pct), "itemStyle": {"color": "#27d3a2", "borderRadius": [3, 3, 0, 0]}}]}}) + '</div></div>'
 + ins('What this means', [f'<b>Weekdays are close:</b> Mon to Fri range from {dow_tot[:5].min()/1000:.0f}k to {dow_tot[:5].max()/1000:.0f}k conversations; Sat and Sun average {round(100*(1-dow_tot[5:].mean()/dow_tot[:5].mean()))}% below the weekday average.',
   '<b>Window caveat:</b> 64 days only (Oct to early Dec 2017), so seasonal claims are not supported.'])))

p.append(page('7. Fix', lede('<b>Recommendations</b> that this data supports.')
 + fixes([('Track p90, not only the median', f'The median ({P["p50"]} min) looks healthy. The p90 is {P["p90"]:.0f} minutes. Put the public SLA on p90 and review the over-4h tail weekly.', f'{over4}% wait over 4 hours'),
          ('Never leave a public thread unanswered', f'{unans_pct}% of conversations got no brand reply. A short holding reply with an ETA beats silence.', f'{unans:,} unanswered'),
          ('Look at the overnight and evening tail', 'p90 waits are longest for conversations started overnight and around 20:00 UTC. Check coverage for those hours first.', 'Wait by hour of day'),
          ('Benchmark against the fast brands', f'Brands answering in under 10 minutes at scale (for example {fast.brand}) show it is possible. Compare queue design and triage with the slow end.', 'Brand leaderboard'),
          ('Add resolution data before judging quality', 'This dataset cannot say whether a reply solved the problem. Add a resolution flag and CSAT to the next analysis.', 'Known data gap')])
 + f'<p class="note">Method: first response time = minutes from a customer\u2019s first inbound tweet (not a reply to anything) to the earliest brand reply to that tweet. Conversations started before Oct 1, 2017 ({R["excluded_pre_oct_2017"]:,}) are excluded as sparse outliers. Brand tables need 500+ answered conversations. Source data: Kaggle "Customer Support on Twitter". Code: analysis.py, build_dashboard.py.</p>'))

os.makedirs('docs', exist_ok=True)
open('docs/index.html', 'w').write(doc('Social Customer Support: Response Time and Workload', f'Real public data: {R["tweets"]/1e6:.1f}M customer-support tweets, {R["brands"]} brands, {conv:,} conversations (Kaggle "Customer Support on Twitter")', p))
print('wrote docs/index.html', os.path.getsize('docs/index.html'))

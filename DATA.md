# Data note

## Source
"Customer Support on Twitter", published on Kaggle by thoughtvector (https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). 2,811,774 public tweets between customers and 108 brand support accounts. The raw file is not included in this repo (500 MB). Download it and pass the path to `analysis.py`.

## Fields used
`tweet_id`, `author_id`, `inbound` (customer or brand), `created_at`, `in_response_to_tweet_id`.
Tweet text is not used in these results.

## Definitions
- **Conversation**: an inbound (customer) tweet that is not a reply to another tweet.
- **First response time (FRT)**: minutes from that tweet to the earliest brand tweet that replies to it.
- **Answered**: the conversation has at least one brand reply. **Unanswered**: none in the data.
- Window: conversations started on or after 2017-10-01 (781,458). 5,888 older conversations are excluded as sparse outliers.
- Brand tables require 500 or more answered conversations (top-20 view in the dashboard is by answered volume).

## Limits
No resolution flag, no staffing data, no direct messages, 64-day window, UTC timestamps. Brand accounts differ in scope (some handle sales or travel disruption), so brand comparisons describe observed speed, not quality.

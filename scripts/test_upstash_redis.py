from upstash_redis import Redis

redis = Redis(
    url="https://classic-lamb-172999.upstash.io",
    token="gQAAAAAAAqPHAAIgcDEwNzZiOGI5MDhlNTY0ZmZjOGY5ZjIzYjZjMjAwZGExNQ",
)

redis.set("foo", "bar")
value = redis.get("bar")

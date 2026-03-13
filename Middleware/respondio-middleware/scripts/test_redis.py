import redis
try:
    r = redis.Redis(host='localhost', port=6380, socket_connect_timeout=2)
    print(f"Ping: {r.ping()}")
except Exception as e:
    print(f"Error: {str(e)}")

import sqlite3
db='/home/raspberry/.openclaw/workspace/network-explorer/data/network_explorer.db'
conn=sqlite3.connect(db)
cur=conn.cursor()

# What are the 34 IPs from anonymous PIDs?
cur.execute("""
    SELECT po.ip, COUNT(DISTINCT po.pid) as cnt, no.name
    FROM peer_observations po
    LEFT JOIN node_observations no ON no.pid = po.pid
    LEFT JOIN api_nodes a ON a.bls = no.bls
    WHERE a.bls IS NULL
    AND po.ip NOT LIKE '192.168.%' AND po.ip NOT LIKE '127.%' AND po.ip NOT LIKE '10.%'
    GROUP BY po.ip, no.name
    ORDER BY cnt DESC
    LIMIT 50
""")
rows = cur.fetchall()
print(f'Anonymous PID IP samples:')
seen = set()
for r in rows:
    ip = r[0]
    if ip not in seen:
        seen.add(ip)
        name = r[2] or '(no name)'
        print(f'  ip={ip:<18} pids={r[1]:<4} name={name}')

conn.close()
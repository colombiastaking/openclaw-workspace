import sqlite3
db='/home/raspberry/.openclaw/workspace/network-explorer/data/network_explorer.db'
conn=sqlite3.connect(db)
cur=conn.cursor()

# Step 1: find IPs with 4-shard coverage and <=6 PIDs
cur.execute("""
    WITH observer_pids AS (
        SELECT DISTINCT no.pid, no.shard, no.name,
               po.ip
        FROM node_observations no
        JOIN peer_observations po ON po.pid = no.pid
        WHERE no.type = 'observer'
        AND po.ip NOT LIKE '192.168.%%' AND po.ip NOT LIKE '127.%%' AND po.ip NOT LIKE '10.%%'
        AND po.ip NOT LIKE '172.%%' AND po.ip NOT LIKE '172.18.%%'
    ),
    ip_shards AS (
        SELECT ip,
               SUM(CASE WHEN shard = 0 THEN 1 ELSE 0 END) as s0,
               SUM(CASE WHEN shard = 1 THEN 1 ELSE 0 END) as s1,
               SUM(CASE WHEN shard = 2 THEN 1 ELSE 0 END) as s2,
               SUM(CASE WHEN shard = 4294967295 THEN 1 ELSE 0 END) as sm,
               COUNT(*) as total_pids
        FROM observer_pids
        GROUP BY ip
        HAVING s0 > 0 AND s1 > 0 AND s2 > 0 AND sm > 0
        AND COUNT(*) <= 6
    )
    SELECT ip, s0, s1, s2, sm, total_pids
    FROM ip_shards
    ORDER BY total_pids ASC
    LIMIT 60
""")
rows = cur.fetchall()
print(f'Found {len(rows)} IPs with 4-shard coverage and <=6 PIDs\n')
print(f'{"IP":<20} s0 s1 s2 sm tot  Names (name/identity)')
print('-'*90)

for r in rows:
    ip = r[0]
    cur2 = conn.cursor()
    cur2.execute("""
        SELECT DISTINCT no.name, a.identity, a.owner
        FROM node_observations no
        JOIN peer_observations po ON po.pid = no.pid
        LEFT JOIN api_nodes a ON a.bls = no.bls
        WHERE po.ip = ?
        AND no.type = 'observer'
        AND po.ip NOT LIKE '192.168.%%' AND po.ip NOT LIKE '127.%%' AND po.ip NOT LIKE '10.%%'
        AND po.ip NOT LIKE '172.%%'
        ORDER BY no.shard
    """, (ip,))
    details = cur2.fetchall()
    parts = []
    for d in details:
        identity = d[1] if d[1] else '?'
        owner = d[2][:12] + '...' if d[2] and len(d[2]) > 12 else (d[2] or '?')
        parts.append(f'{d[0]}/{identity}')
    print(f'{r[0]:<20} {r[1]}   {r[2]}   {r[3]}   {r[4]}   {r[5]}   ' + ', '.join(parts))

conn.close()

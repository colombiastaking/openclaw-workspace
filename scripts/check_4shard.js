import sqlite3
db='/home/raspberry/.openclaw/workspace/network-explorer/data/network_explorer.db'
conn=sqlite3.connect(db)
cur=conn.cursor()

# Find IPs with 4-shard observer coverage, check identity/owner
cur.execute("""
    WITH observer_pids AS (
        SELECT DISTINCT no.pid, no.name, no.bls, no.shard, no.type,
               po.ip, a.identity, a.provider, a.owner
        FROM node_observations no
        JOIN peer_observations po ON po.pid = no.pid
        LEFT JOIN api_nodes a ON a.bls = no.bls
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
    ),
    observer_details AS (
        SELECT op.ip, op.pid, op.shard, op.name, op.identity, op.owner,
               ROW_NUMBER() OVER (PARTITION BY op.ip ORDER BY op.shard) as rn
        FROM observer_pids op
        INNER JOIN ip_shards is2 ON is2.ip = op.ip
    )
    SELECT ip, s0, s1, s2, sm, total_pids
    FROM ip_shards
    ORDER BY total_pids ASC
    LIMIT 50
""")
rows = cur.fetchall()
print(f'Found {len(rows)} IPs with 4-shard coverage and <=6 PIDs\n')

# For each, get the name+identity details
seen_ips = [r[0] for r in rows]
print(f'{"IP":<20} s0 s1 s2 sm tot  Names & identities')
print('-'*95)

for ip_row in rows:
    ip = ip_row[0]
    cur2 = conn.cursor()
    cur2.execute("""
        SELECT op.name, op.identity, op.owner
        FROM node_observations no
        JOIN peer_observations po ON po.pid = no.pid
        LEFT JOIN api_nodes a ON a.bls = no.bls
        JOIN (SELECT DISTINCT pid, name, identity, owner FROM node_observations) op ON op.pid = no.pid
        WHERE po.ip = ?
        AND no.type = 'observer'
        AND po.ip NOT LIKE '192.168.%%' AND po.ip NOT LIKE '127.%%' AND po.ip NOT LIKE '10.%%'
        AND po.ip NOT LIKE '172.%%'
        ORDER BY no.shard
    """, (ip,))
    details = cur2.fetchall()
    names = [f"{d[0]}/{d[1] or '?'}" for d in details]
    print(f'{ip:<20} {ip_row[1]}   {ip_row[2]}   {ip_row[3]}   {ip_row[4]}   {ip_row[5]}   ' + ', '.join(names[:4]))

conn.close()

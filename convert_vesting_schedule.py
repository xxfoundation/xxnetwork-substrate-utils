import json

q = json.load(open('query-claims.json', 'rb'))

out = open('out.csv', 'w')

#print(f"account_id, l1, l2, round_num, days", file=out)

calc_lockups = []
for account_id, lockups in q.items():
    for lockup in lockups:
        l1 = lockup[0]
        l2 = lockup[1]
        round_num = lockup[2]
        # *[roundtime] / num_seconds_in_minute / num_minutes_in_hr / num_hrs_in_day
        days = round_num*6/60/60/24
        # print(f"{account_id}, {l1}, {l2}, {round_num}, {days}", file=out)
        calc_lockups.append({
            'account_id': account_id,
            'l1': l1,
            'l2': l2,
            'round_num': round_num,
            'days': days,
        })

daynames = []
for cl in calc_lockups:
    if cl['days'] not in daynames:
        daynames.append(cl['days'])

colnames = sorted(daynames)
colnames.insert(0, 'account_id')
print(colnames)

import csv
rows = dict()
for cl in calc_lockups:
    aid = cl['account_id']
    if aid not in rows:
        rows[aid] = {
            'account_id': aid,
        }
    for col in colnames[1:]:
        if col not in rows[aid]:
            rows[aid][col] = 0
        if cl['days'] == col:
            rows[aid][col] = cl['l1']


out = csv.writer(open('out.csv', 'w'), delimiter=',')
out.writerow(colnames)
for _,r in rows.items():
    out.writerow([x for x in r.values()])

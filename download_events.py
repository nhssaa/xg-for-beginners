import json, os, concurrent.futures, urllib.request

matches = json.load(open('/tmp/matches_743.json'))
ids = [m['id'] for m in matches if m.get('available')]
os.makedirs('/tmp/events', exist_ok=True)

def fetch(mid):
    p = f'/tmp/events/events_{mid}.json'
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        return mid, 'cached'
    url = f'https://raw.githubusercontent.com/ImpectAPI/open-data/main/data/events/events_{mid}.json'
    try:
        urllib.request.urlretrieve(url, p)
        return mid, 'ok'
    except Exception as e:
        return mid, f'ERR {e}'

done = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
    for mid, status in ex.map(fetch, ids):
        done += 1
        if status.startswith('ERR'):
            print(mid, status)
        if done % 50 == 0:
            print(f'{done}/{len(ids)}', flush=True)
print('DONE', done)

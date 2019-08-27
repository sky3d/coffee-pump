import json
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from logger import log_debug, log_error, log_info

SLACK_HOOK_URL = 'https://hooks.slack.com/services/__YOUR_HOOK_URL__'
# ... other hooks

def notify_all(msg):
    for hook in [SLACK_HOOK_URL]:
        thread = threading.Thread(target=notify, args=(msg, hook))
        thread.start()


def notify(msg, hook_url):
    log_debug('[x] Alert: %s' % msg)

    req = Request(hook_url)
    try:
        data = json.dumps({'text': msg}).encode('ascii')
        response = urlopen(req, data)
        response.read()
    except HTTPError as e:
        log_error('Request failed: %d %s' % (e.code, e.reason))
    except URLError as e:
        log_error('Server connection failed: %s' % e.reason)

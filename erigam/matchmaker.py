#!/usr/bin/python
from redis import Redis
import uuid
import time
import logging
import os

from erigam.lib import api
from erigam.lib.model import sm, Message
from erigam.lib.messages import send_message
from erigam.lib.request_methods import redis_pool

logger = logging.getLogger()

if 'DEBUG' in os.environ:
    logger.setLevel("DEBUG")

OPTION_LABELS = {
    'para0': 'script style',
    'para1': 'paragraph style',
    'nsfw0': 'safe for work',
    'nsfw1': 'not safe for work',
}

def check_compatibility(first, second):
    selected_options = []
    for option in ["para", "nsfw"]:
        first_option = first['options'].get(option)
        second_option = second['options'].get(option)
        if (
            first_option is not None
            and second_option is not None
            and first_option != second_option
            and first['panda'] != second['panda']
        ):
            return False, None
        if first_option is not None:
            selected_options.append(option+first_option)
        elif second_option is not None:
            selected_options.append(option+second_option)

    return True, selected_options

if __name__ == '__main__':

    db = sm()
    redis = Redis(connection_pool=redis_pool)

    while True:
        searchers = redis.zrange('searchers', 0, -1)

        if len(searchers) >= 2:  # if there aren't at least 2 people, there can't be matches
            sessions = [{
                'id': session_id,
                'options': redis.hgetall('session.'+session_id+'.picky-options'),
                'panda': redis.hexists('punish-scene', redis.hget('session.'+session_id+'.meta', 'last_ip'))
            } for session_id in searchers]

            # https://docs.python.org/2/library/functions.html#zip
            for searcher1, searcher2 in zip(*[iter(sessions)]*2):
                logging.debug("Matching %s and %s" % (searcher1['id'], searcher2['id']))
                compatible, selected_options = check_compatibility(searcher1, searcher2)

                if not compatible:
                    logging.debug("%s not compatible with %s" % (searcher1['id'], searcher2['id']))
                    continue

                chat = str(uuid.uuid4()).replace('-', '')
                logging.debug('Match found, sending to %s.' % chat)
                logging.debug('%s: options %s' % (searcher1['id'], searcher1['options']))
                logging.debug('%s: options %s' % (searcher2['id'], searcher2['options']))
                log = api.chat.create(db, redis, chat, 'saved')

                # Send options message if options are present.
                if len(selected_options) > 0:
                    option_text = ', '.join(OPTION_LABELS[_] for _ in selected_options)
                    send_message(db, redis, Message(
                        log_id=log.id,
                        type="message",
                        counter=-1,
                        text="This is a {option} chat.".format(option=option_text)
                    ))

                matchdata = {
                    "chat": chat,
                    "log": log.id
                }

                redis.hmset('session.'+searcher1['id']+'.match', matchdata)
                redis.hmset('session.'+searcher2['id']+'.match', matchdata)
                redis.zrem('searchers', searcher1['id'])
                redis.zrem('searchers', searcher2['id'])

        time.sleep(1)

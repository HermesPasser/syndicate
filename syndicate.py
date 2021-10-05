import xml.etree.ElementTree as ET
import urllib.request as req
from os.path import exists
import json

FILENAME = 'db.json'
CONTENTS = dict()

def fetch_rss(url):
    # TODO: error handling when is not 200
    raw_text = ''
    with req.urlopen(url) as response:
        raw_text = response.read()

    return raw_text


def parse_rss(text, url=''):
    # this is the happy path, we need to handle malformated xml

    root = ET.fromstring(text)
    channel = root.find('channel')
    channel_name = channel.find('title').text
    item = new_channel(channel_name, url) # feed's url, not the embeded link inside of it
    append_channel(item)

    for item in channel.findall('item'):
        dict_item = new_feed_item(
            item.find('title').text,
            item.find('link').text,
            item.find('guid').text,
            # since for now were listing it on js, maybe the format should match to
            # make able to be parsed easily to a js date
            item.find('pubDate').text,
            item.find('description').text
        )
        append_item_to_feed(channel_name, dict_item)
    return channel_name


def mark_read(channel_name, id, is_read):
    global CONTENTS
    CONTENTS[channel_name]['feed'][id]['read'] = is_read


def new_feed_item(name, content, link, id, data):
    i = dict()
    i['name'] = name
    i['link'] = link
    i['id'] = id
    i['data'] = data
    i['read'] = False
    i['content'] = content
    return i


def append_item_to_feed(channel_name, item):
    global CONTENTS

    ch = CONTENTS.get(channel_name, None)
    if ch is None:
        return
    # i'm not testing if the item already existis
    ch['feed'][item['id']] = item


def new_channel(name, url):
    c = dict()
    c['name'] = name
    c['url'] = url
    c['feed'] = dict()
    return c


def append_channel(channel):
    global CONTENTS
    CONTENTS[channel['name']] =  channel


def close_db():
    global FILENAME, CONTENTS
    with open(FILENAME, 'a+') as file:
        txt = json.dumps(CONTENTS)
        file.truncate(0)
        file.write(txt)


def open_db():
    #       <channel name> { 
    #           name: '', 
    #           url: '', 
    #           feed: {
    #               <id>: {name: '', content: '', read: false, url: '', id: '', link: '', data: ''}
    #               ...
    #           }
    #       }
    global FILENAME, CONTENTS
    if not exists(FILENAME):
        print('no db found')
    else:
        try:
            with open(FILENAME, 'a+') as file:
                CONTENTS = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            pass


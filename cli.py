#!/usr/bin/env python3

import argparse
from datetime import UTC, datetime
import sys
from xml.etree.ElementTree import fromstring

from aggregator.connection import Connection
from aggregator.dao.rss.item import ItemDao
from aggregator.migration import migrate
from aggregator.dao.rss.channel import ChannelDao
from item import Item, ItemMetadataDao
from syndicate import (
    DB_FILE,
    fetch_rss,
    get_new_items_from_channel,
    parse_rss,
    ChannelList,
    uuid_from_url,
)


def add_rss(url: str):
    print("fetching rss")
    xml_text = fetch_rss(url)
    print("parsing rss")
    root = fromstring(xml_text)

    # TODO: It WILL break at some point, add a fallback using the url as name
    title = root.find("channel").find("title").text
    assert title
    print("saving rss")
    # TODO: isso tem que se ralterado para preencher mais info
    parse_rss(ChannelList(), xml_text, url, title)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="syndicate",
        description="Very simple RSS feed cli",
        epilog="Repository: https://github.com/HermesPasser/syndicate",
    )

    # commands = parser.add_subparsers(dest="command", required=False)

    parser.add_argument("channel", help="RSS channel management")

    # channel_parser = commands.add_parser("channel")
    # channel_commands = channel_parser.add_subparsers(
    #     dest="channel_command",
    #     required=True,
    # )

    # https://docs.python.org/3/howto/argparse.html#argparse-tutorial

    # add_parser = channel_commands.add_parser("add")
    # add_parser.add_argument("channel_url")
    # parser.add_argument('channel')
    args = parser.parse_args()
    print(args)
    return args


# TODO: download attachments
def cli_main():
    def print_channels():
        print("\ntitle\n-")
        for item in channel_dao.select_all():
            print(item.title)

    def sync_from_channel(channel_name: str):
        chan = channel_dao.get(channel_name)
        if not chan:
            print("Channel not found", file=sys.stderr)
            return

        # TODO: Get rid of it
        feed_link = channel.channel_link(channel_name)
        assert feed_link

        news = get_new_items_from_channel(
            # chan.link, TODO: this link is not the rss link, but the site link
            feed_link,
            # TODO: it seems i put the date as 0 if is not found, so this 'or' is unecessary
            item_dao.date_of_last_item(channel_name) or datetime.now(UTC),
        )

        # TODO: maybe move to a utility in syndicate.py since the this code already
        #       is duplicated there...
        # Upload the old models
        ch_id = uuid_from_url(feed_link)  # i think this link os the feed, not the site

        for item in news:
            channel.add_feed_item(
                item.title,
                item.description,
                item.link,
                item.guid[0],  # TODO: treat this if may be really null
                item.pub_date.timestamp() if item.pub_date else 0,
                ch_id,
            )

        # TODO: wip  Upload the new models, so we can merge the old way of read/unread and the
        #            new models that have all that sweet extra information
        item_dao.insert_many_into_channel(channel_name, news)

        for item_meta in item_metadata_dao.list(channel_name, only_unread=True):
            item = item_meta.item
            print(
                item.pub_date.isoformat() if item.pub_date else "Unknown date",
                item.title,
                item.link,
            )

    # NOTE: the classes used by ChannelList are initialized when ChannelList is instantiated
    migrate(Connection(str(DB_FILE)))
    channel = ChannelList()

    # Ambas essas abstrações utilizam o mesmo nome de tabela, porém
    # o schema delas é diferente.
    channel_dao = ChannelDao(Connection(str(DB_FILE)))
    item_metadata_dao = ItemMetadataDao(Connection(str(DB_FILE)))
    item_dao = ItemDao(Connection(str(DB_FILE)))

    args = parse_args()
    if args.channel:

        if args.list:
            # TODO: get name
            sync_from_channel("")

        else:
            print_channels()


cli_main()


# foo = ItemMetadataDao(Connection(str(DB_FILE))).select_many('AoQuadrado')

# add_rss('https://feeds.feedburner.com/AoQuadradoPodcast')

# Entidades da aplicação (não só do rss feed)
# channel - item

# Entidades do RSS (não estão sendo usadas?) (para que asa modelei?)
# category - channel_category - channel
# item_category


def old_cli():
    # esse código é da minha primeira tentativa (que desisti, aparentemente)
    from argparse import ArgumentParser

    def parse_args():
        parser = ArgumentParser(description="Very simple rss header")
        # parser.add_argument('foo', help='')
        # parser.add_argument(
        # 'ldc',
        # action='store',
        # dest='d',
        # type=int,
        # default=100,
        # required=False,
        # help='value',
        # )
        parser.add_argument("filename")
        parser.add_argument("lc", help="List all registered channels")
        # parser.add_argument(
        # '--d',
        # action='store_true',
        # dest='var',
        # required=False,
        # help='flag',
        # )

        return parser.parse_args()

    def main():
        print("hello, world!")
        return
        args = parse_args()

        if args.store_true:
            print("TODO: mostrar canais aqui")

            return

    # if not arguments are provided, show all unread

    def foo(bar):
        print("got", bar)

        def foo(self):
            print(self)
            return bar(self)

        return foo

    class Fo:
        @foo
        def baz(self):
            return lambda x: x

    Fo().baz()
    if __name__ == "__main__":
        main()

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


def build_parser():
    parser = argparse.ArgumentParser(
        prog="syndicate",
        description="Very simple RSS feed cli",
        epilog="Repository: https://github.com/HermesPasser/syndicate",
    )

    resources = parser.add_subparsers(dest="resource")

    channel = resources.add_parser("channel", help="Channel management")
    channel_actions = channel.add_subparsers(dest="action", required=True)

    add = channel_actions.add_parser("add", help="Add a channel")
    add.add_argument("url", help="RSS feed url")
    add.add_argument("--name", help="Overrides the channel name")

    channel_actions.add_parser("list", help="List the channels")

    show = channel_actions.add_parser("show", help="Show the channel details")
    show.add_argument(
        "channel", help="Channel identifier (feed url, channel display name)"
    )

    remove = channel_actions.add_parser("remove", help="Remove a channel")
    remove.add_argument(
        "channel", help="Channel identifier (feed url, channel display name)"
    )

    # TODO: traduzir en
    refresh = channel_actions.add_parser("refresh", help="Update the feed")
    refresh.add_argument(
        "channel",
        nargs="?",
        help="Canal a atualizar; sem argumento, atualiza todos",
    )

    rename = channel_actions.add_parser("rename", help="Renomear um canal")
    rename.add_argument("channel", help="Nome ou identificador atual do canal")
    rename.add_argument("new_name", help="Novo nome para o canal")

    # rss item ...
    item = resources.add_parser("item", help="Ler e gerenciar itens")
    item_actions = item.add_subparsers(dest="action", required=True)

    list_items = item_actions.add_parser("list", help="Listar itens")
    list_items.add_argument("channel", nargs="?", help="Filtrar por canal")
    list_items.add_argument(
        "--unread",
        action="store_true",
        help="Mostrar somente itens não lidos",
    )
    list_items.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Número máximo de itens",
    )

    for action, help_text in (
        ("read", "Exibir o conteúdo de um item"),
        ("open", "Abrir o link de um item no navegador"),
        ("mark-read", "Marcar um item como lido"),
        ("mark-unread", "Marcar um item como não lido"),
        ("download", "Baixar o enclosure de um item"),
    ):
        item_command = item_actions.add_parser(action, help=help_text)
        item_command.add_argument("id", help="Identificador do item")
        if action == "download":
            item_command.add_argument(
                "--output",
                "-o",
                help="Caminho de destino do arquivo",
            )

    mark_all = item_actions.add_parser(
        "mark-all-read",
        help="Marcar itens como lidos",
    )
    mark_all.add_argument(
        "channel",
        nargs="?",
        help="Limitar a ação a um canal",
    )

    # rss search ...
    search = resources.add_parser("search", help="Buscar itens")
    search.add_argument("term", help="Termo de busca")
    search.add_argument("--channel", help="Limitar a busca a um canal")

    # Ajuda e versão
    resources.add_parser("help", help="Mostrar ajuda")
    resources.add_parser("version", help="Mostrar versão")

    # Needs to be defined after the subparsers
    parser.set_defaults(resource="channel", action="list")

    return parser


def parse_args():
    parser = argparse.ArgumentParser(
        prog="syndicate",
        description="Very simple RSS feed cli",
        epilog="Repository: https://github.com/HermesPasser/syndicate",
    )

    channel = parser.add_subparsers(dest="channel", required=False)
    channel.add_argument()
    # parser.add_argument("channel", help="RSS channel management")

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

    args = build_parser().parse_args()

    print(args)

    def handle_channel_cli(args: argparse.Namespace):
        match args.action:
            case "add":
                # TODO: handle failures
                # TODO: handle changing the display name (args.name: str | None)
                add_rss(args.url)
            case "remove":
                ...
            case "list":
                print_channels()
            case "show":
                raise NotImplementedError
            case "refresh":
                # TODO: i think this should just sync, not show the new feed items
                #       (should show how many items were updated instead)
                if args.channel:
                    # TODO: handle failures (channel does not exits)
                    # TODO: handle display name and name not being the same
                    sync_from_channel(args.channel)
                else:
                    # TODO: sync all channels
                    raise NotImplementedError

            case "rename":
                raise NotImplementedError

    def handle_item_cli(args: argparse.Namespace):
        match args.action:
            case "list":
                raise NotImplementedError

            case _:
                raise NotImplementedError

    match args.resource:
        case "channel":
            handle_channel_cli(args)
        case "item":
            handle_item_cli(args)


cli_main()


# foo = ItemMetadataDao(Connection(str(DB_FILE))).select_many('AoQuadrado')

# add_rss('https://feeds.feedburner.com/AoQuadradoPodcast')

# Entidades da aplicação (não só do rss feed)
# channel - item

# Entidades do RSS (não estão sendo usadas?) (para que asa modelei?)
# category - channel_category - channel
# item_category

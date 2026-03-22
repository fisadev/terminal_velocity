import click

from tv.isolation import bot_server


@click.command()
@click.option("--bot-type", type=str, help="Bot type to run in the server")
@click.option("--port", type=int, help="Port to listen on for messages")
def main(bot_type, port):
    """
    A simple server that encapsulates a bot logic to be called remotely.
    """
    bot_server(bot_type, port)


if __name__ == '__main__':
    main()

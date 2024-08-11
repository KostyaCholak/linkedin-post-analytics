import asyncio

import click
from dotenv import load_dotenv

from src import database


load_dotenv()


@click.group()
def cli():
    pass


@cli.command("add-user")
@click.argument("username")
def add_user(username):
    """Add a new user to the database

You must own the account for the tool to work.
"""
    async def task():
        created = await database.new_linkedin_user(username, "", "")
        if not created:
            click.echo(click.style("User already exists in the database", fg="red"))
        else:
            click.echo(click.style("User successfully added to the database", fg="green"))
    
        await database.close()
    
    asyncio.run(task())


@cli.command("add-post")
@click.argument("username")
@click.argument("post-id")
def add_post(username: str, post_id: str):
    """Add a new post to the database

You must own the account and post for the tool to work.
"""
    async def task():
        user = await database.get_linkedin_user(username)
        created = await database.new_linkedin_post(user, post_id, database.utc_now())

        if not created:
            click.echo(click.style("Post already exists in the database", fg="red"))
        else:
            click.echo(click.style("Post successfully added to the database", fg="green"))

        await database.close()
    
    asyncio.run(task())


@cli.command("analyze")
@click.argument("username")
def analyze(username: str):
    """Analyze your LinkedIn posts

You must own the account for the tool to work.
"""
    from src.analyze import analyze

    async def task():
        try:
            await analyze(username)
        except KeyboardInterrupt:
            click.echo(click.style("Exiting...", fg="red"))
        finally:
            await database.close()

    asyncio.run(task())


if __name__ == '__main__':
    cli()

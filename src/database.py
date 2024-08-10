import asyncio
import datetime
import logging
import os
from dotenv import load_dotenv
from peewee import *
import peewee_async

from .linkedin import PostAnalytics, UserAnalytics


logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_NAME = os.environ['DATABASE_NAME']
DATABASE_USER = os.environ['DATABASE_USER']
DATABASE_PASSWORD = os.environ['DATABASE_PASSWORD']
DATABASE_HOST = os.environ['DATABASE_HOST']
DATABASE_PORT = int(os.environ['DATABASE_PORT'])

db = peewee_async.PostgresqlDatabase(
    DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class LinkedInUser(Model):
    username = CharField(primary_key=True, max_length=255)
    name = CharField(max_length=255)
    avatar_url = CharField(max_length=255)
    created_at = DateTimeField(default=utc_now)
    updated_at = DateTimeField(default=utc_now)
    last_state = DeferredForeignKey('LinkedInUserState', backref='user_br', null=True)

    class Meta:
        database = db


class LinkedInUserState(Model):
    id = AutoField()
    user = ForeignKeyField(LinkedInUser, backref='states', field='username', on_delete='CASCADE')
    followers_count = IntegerField()
    connections_count = IntegerField(null=True)
    profile_views_count = IntegerField()
    post_impressions_count = IntegerField()
    search_appears_count = IntegerField()
    created_at = DateTimeField(default=utc_now)

    class Meta:
        database = db


class LinkedInPost(Model):
    id = CharField(primary_key=True, max_length=255)
    user = ForeignKeyField(LinkedInUser, backref='posts', field='username', on_delete='CASCADE')
    post_created_at = DateTimeField()
    created_at = DateTimeField(default=utc_now)
    updated_at = DateTimeField(default=utc_now)
    last_state = DeferredForeignKey('LinkedInPostState', backref='post_br', null=True)

    class Meta:
        database = db


class LinkedInPostState(Model):
    id = AutoField()
    post = ForeignKeyField(LinkedInPost, backref='states', on_delete='CASCADE')
    content = TextField(null=True)
    created_at = DateTimeField(default=utc_now)
    reposts_count = IntegerField()
    comments_count = IntegerField()
    reactions_count = IntegerField()
    impressions_count = IntegerField()
    unique_views_count = IntegerField()

    class Meta:
        database = db


db.connect()
db.create_tables([LinkedInUser, LinkedInPost, LinkedInUserState, LinkedInPostState])

objects = peewee_async.Manager(db)
db.set_allow_sync(False)


async def get_linkedin_user(username) -> LinkedInUser | None:
    logger.info('Getting user "%s"', username)
    return await objects.get_or_none(LinkedInUser, username=username)


async def get_user_last_state(user: LinkedInUser) -> LinkedInUserState | None:
    logger.info('Getting last state for user "%s"', user.username)
    return await objects.get_or_none(LinkedInUserState, id=user.last_state_id)


async def get_post_last_state(post: LinkedInPost) -> LinkedInPostState | None:
    logger.info('Getting last state for post "%s"', post.id)
    return await objects.get_or_none(LinkedInPostState, id=post.last_state_id)


async def get_linkedin_post(id) -> LinkedInPost | None:
    logger.info('Getting post "%s"', id)
    return await objects.get_or_none(LinkedInPost, id=id)


async def new_linkedin_user(username, name, avatar_url) -> bool:
    if await get_linkedin_user(username):
        logger.info('User "%s" already exists', username)
        return False

    logger.info('Creating new user "%s"', username)
    await objects.create(
        LinkedInUser,
        username=username,
        name=name,
        avatar_url=avatar_url,
    )

    return True


async def new_linkedin_post(user, post_id, post_created_at) -> bool:
    if await get_linkedin_post(post_id):
        logger.info('Post "%s" already exists', post_id)
        return False

    logger.info('Creating new post "%s"', post_id)
    await objects.create(
        LinkedInPost,
        id=post_id,
        user=user, 
        post_created_at=post_created_at
    )

    return True


async def new_user_state(user: LinkedInUser, analytics: UserAnalytics):
    logger.info('Creating new user state for "%s"', user.username)

    state = await objects.create(
        LinkedInUserState,
        user=user,
        followers_count=analytics.followers_count,
        connections_count=analytics.connections_count,
        profile_views_count=analytics.profile_views_count,
        post_impressions_count=analytics.post_impressions_count,
        search_appears_count=analytics.search_appears_count,
    )

    await objects.execute(LinkedInUser.update(last_state=state).where(
        LinkedInUser.username == user.username))


async def new_post_state(post: LinkedInPost, analytics: PostAnalytics):
    logger.info('Creating new post state for "%s"', post.id)

    state = await objects.create(
        LinkedInPostState,
        post=post,
        content=analytics.content,
        reposts_count=analytics.reposts_count,
        comments_count=analytics.comments_count,
        reactions_count=analytics.reactions_count,
        impressions_count=analytics.impressions_count,
        unique_views_count=analytics.unique_views_count,
    )

    await objects.execute(LinkedInPost.update(last_state=state).where(
        LinkedInPost.id == post.id))


async def get_user_posts(user: LinkedInUser) -> list[LinkedInPost]:
    logger.info('Getting posts for user "%s"', user.username)
    return await objects.execute(LinkedInPost.select().where(LinkedInPost.user==user))


async def close():
    await objects.close()
    db.close()

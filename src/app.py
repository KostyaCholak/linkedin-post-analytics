import os
import time
import asyncio
import logging
import datetime

from dotenv import load_dotenv

from . import database
from . import linkedin


logging.basicConfig(filename='analytics_log.txt', level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logger = logging.getLogger(__name__)

load_dotenv()

LINKEDIN_USERNAME = os.environ['LINKEDIN_USERNAME']


async def main(username: str):
    next_update = time.time()
    while True:
        await update_user_data(username)
        next_update = next_update + 60
        await asyncio.sleep(next_update - time.time())


async def update_user_data(username: str):
    logger.info('Saving user state for "%s"', username)
    user = await database.get_linkedin_user(username)
    if user is None:
        logger.info('User "%s" not found in the database', username)
        raise Exception('User not found')
    
    await save_user_state(user)
    posts = await database.get_user_posts(user)
    for post in posts:
        await save_post_state(post)


async def save_user_state(user: database.LinkedInUser):
    update_after = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    last_state = await database.get_user_last_state(user)

    if last_state is not None and last_state.created_at.astimezone(datetime.timezone.utc) > update_after:
        logger.info('Skipping user "%s" because it was already saved', user.username)
        return

    user_analytics = await linkedin.get_my_user_analytics()
    if user_analytics is not None:
        await database.new_user_state(user, user_analytics)


async def save_post_state(post: database.LinkedInPost):
    now = datetime.datetime.now(datetime.timezone.utc)

    time_since_creation = now - post.post_created_at.astimezone(datetime.timezone.utc)
    if time_since_creation < datetime.timedelta(hours=1):
        update_after = now - datetime.timedelta(minutes=1)
    elif time_since_creation < datetime.timedelta(hours=24):
        update_after = now - datetime.timedelta(minutes=5)
    elif time_since_creation < datetime.timedelta(days=7):
        update_after = now - datetime.timedelta(hours=60)
    elif time_since_creation < datetime.timedelta(days=14):
        update_after = now - datetime.timedelta(hours=6)
    else:
        logger.debug('Skipping post "%s" because it was created more than a week ago', post.id)
        return
    
    last_state = await database.get_post_last_state(post)
    last_state_time = last_state.created_at if last_state is not None else None
    if last_state_time is not None and last_state_time.astimezone(datetime.timezone.utc) > update_after:
        logger.debug('Skipping post "%s" because it was already saved', post.id)
        return
    
    post_analytics = await linkedin.get_my_post_analytics(post.id)
    if post_analytics is None:
        return
    
    await database.new_post_state(post, post_analytics)


if __name__ == '__main__':
    asyncio.run(main(LINKEDIN_USERNAME))

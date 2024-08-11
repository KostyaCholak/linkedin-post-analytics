import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.linkedin import PostAnalytics, UserAnalytics

from . import database


logging.basicConfig(filename='server_log.txt', level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logger = logging.getLogger(__name__)

load_dotenv()


app = FastAPI()

origins = [
    "https://linkedin.com/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/linkedin/post/{post_id}/stats")
async def list_post_stats(post_id: str):
    states = await database.get_post_states(post_id)
    return [{
        'time': state.created_at.isoformat(),
        'impressions': state.impressions_count,
    } for state in states]


@app.get("/linkedin/user/{username}/stats")
async def list_user_stats(username: str):
    user = await database.get_linkedin_user(username)
    if not user:
        return {'error': 'User not found'}
    
    states = await database.get_user_states(user)
    return [{
        'time': state.created_at.isoformat(),
        'followers': state.followers_count,
    } for state in states]


@app.post("/linkedin/post/{post_id}/stats")
async def create_post_stats(post_id: str, impression_count: int, comment_count: int, reactions_count: int, reposts_count: int):
    post = await database.get_linkedin_post(post_id)
    if not post:
        return {'error': 'Post not found'}

    await database.new_post_state(post, PostAnalytics(
        post_id=post_id,
        content="",
        impressions_count=impression_count,
        comments_count=comment_count,
        reactions_count=reactions_count,
        reposts_count=reposts_count,
        unique_views_count=0,
    ))
    return {'success': True}


@app.post("/linkedin/user/{username}/stats")
async def create_user_stats(username: str, followers_count: int, connections_count: int, profile_views_count: int, post_impressions_count: int, search_appears_count: int):
    user = await database.get_linkedin_user(username)
    if not user:
        return {'error': 'User not found'}

    await database.new_user_state(user, UserAnalytics(
        followers_count=followers_count,
        connections_count=connections_count,
        profile_views_count=profile_views_count,
        post_impressions_count=post_impressions_count,
        search_appears_count=search_appears_count,
    ))
    return {'success': True}

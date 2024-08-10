import json
import asyncio
from dataclasses import dataclass
import logging
import os

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()

LINKEDIN_COOKIES = os.environ['LINKEDIN_COOKIES']


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'cookie': LINKEDIN_COOKIES,
    'dnt': '1',
    'priority': 'u=0, i',
    'referer': 'https://www.linkedin.com/',
    'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
}


@dataclass
class PostAnalytics:
    post_id: str
    content: str
    reposts_count: int
    comments_count: int
    reactions_count: int
    impressions_count: int
    unique_views_count: int


@dataclass
class UserAnalytics:
    followers_count: int
    connections_count: int | None
    profile_views_count: int
    post_impressions_count: int
    search_appears_count: int


async def get_my_user_analytics() -> UserAnalytics | None:
    logger.info('Getting my user analytics')

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            'https://www.linkedin.com/dashboard/',
        ) as response:
            if response.status != 200:
                logger.error('Failed to get user analytics: %s', response.status)
                return None
            
            followers_count = None
            profile_views_count = None
            post_impressions_count = None
            search_appears_count = None

            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            code = soup.find_all('code')[-3]
            try:
                data = json.loads(code.text.strip())['data']['data']
            except json.JSONDecodeError:
                logger.error('Looks like the LinkedIn cookies are invalid')
                exit(1)
            section = data['feedDashCreatorExperienceDashboard']['section'][0]['analyticsSection']
            analytics = section['analyticsPreviews']

            for item in analytics:
                value = int(item['analyticsTitle']['text'].replace(',', ''))
                title = item['description']['text']
                if title == 'Followers':
                    followers_count = value
                elif title == 'Profile viewers':
                    profile_views_count = value
                elif title == 'Post impressions':
                    post_impressions_count = value
                elif title == 'Search appearances':
                    search_appears_count = value
                else:
                    logger.warning('Unknown title in user analytics: %s', title)

            return UserAnalytics(
                followers_count=followers_count,
                connections_count=None,
                profile_views_count=profile_views_count,
                post_impressions_count=post_impressions_count,
                search_appears_count=search_appears_count,
            )


async def get_my_post_analytics(post_id: str) -> PostAnalytics | None:
    logger.info('Getting my post analytics for "%s"', post_id)
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            f'https://www.linkedin.com/analytics/post-summary/urn:li:activity:{post_id}/',
        ) as response:
            if response.status != 200:
                logger.error('Failed to get post analytics: %s', response.status)
                return None
                        
            impressions = None
            unique_views = None
            reactions = None
            comments = None
            reposts = None
            post_content = None

            content = await response.text()

            if 'Analytics failed to load' in content:
                logger.error('You might not have access to this post %s', post_id)
                return None

            soup = BeautifulSoup(content, 'html.parser')
            code = soup.find_all('code')[-3]
            data = json.loads(code.text.strip())['included'][1]

            for component in data['components']:
                if not component['summary']:
                    continue
                for item in component['summary']['keyMetrics']['items']:
                    if item['description']['text'] == 'Impressions':
                        impressions = int(item['title']['text'].replace(',', ''))
                    if item['description']['text'] == 'Unique views':
                        unique_views = int(item['title']['text'].replace(',', ''))

            data = json.loads(code.text.strip())['included'][2]
            component = data['component']

            for item in component['summary']['detail']['ctaList']['items']:
                if item['title'] == 'Reactions':
                    reactions = int(item['text'].replace(',', ''))
                if item['title'] == 'Comments':
                    comments = int(item['text'].replace(',', ''))
                if item['title'] == 'Reposts':
                    reposts = int(item['text'].replace(',', ''))

            data = json.loads(code.text.strip())['included'][6]
            post_content = data['commentary']['commentaryText']['text']

            return PostAnalytics(
                post_id=post_id,
                content=post_content,
                reposts_count=reposts,
                comments_count=comments,
                reactions_count=reactions,
                impressions_count=impressions,
                unique_views_count=unique_views,
            )

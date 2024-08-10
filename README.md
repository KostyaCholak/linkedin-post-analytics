# LinkedIn Post Analytics

This is a project that tracks your LinkedIn posts and provides you with analytics about them.

## Installation

Python 3.8+ is required.

1. Clone the repository

```bash
git clone https://github.com/KostyaCholak/linkedin-post-analytics.git
cd linkedin-post-analytics/
```

2. Create a `.env` file in the root directory of the project by copying the `.env.example` file and filling in the missing values

```bash
cp .env.example .env
```

Open the `.env` file and fill in the missing values.
LINKEDIN_USERNAME: Your LinkedIn username, for example `kostya-numan`. You MUST own this account for the tool to work.
LINKEDIN_COOKIES: The cookies that you get when you log in to LinkedIn. You can get them by opening the developer tools in your browser (network tab), reloading the page, opening the first request, scolling to the "Request Headers" section, and looking at the `li_sugr` cookie.
DATABASE_*: PostgreSQL database connection settings

3. Install the dependencies by running 

```bash
pip install -r requirements.txt
```

## Usage

> [!NOTE]
> You must be the owner the account and the posts for the tool to work.

1. Add your LinkedIn user to the database

Go to your profile and copy the username from the URL.
For example, if the URL is https://www.linkedin.com/in/kostya-numan/
then the username is "kostya-numan".

```bash
python -m analytics add-user "your-username"
```

2. Add your LinkedIn posts to the database

Go to your post and copy the post ID from the URL.
For example, if the URL is https://www.linkedin.com/feed/update/urn:li:activity:7227740367670898688/
then the post ID is "7227740367670898688".

```bash
python -m analytics add-post "your-username" "post-id"
```

3. Run the tracking pipeline

```bash
python -m analytics analyze "your-username"
```

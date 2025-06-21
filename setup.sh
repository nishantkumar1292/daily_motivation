pip install -r requirements.txt

# create .env file if doesn't exist
if [ ! -f .env ]; then
    touch .env
    # add env variables to .env
    echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
    echo "TWITTER_API_KEY=your_twitter_api_key" >> .env
    echo "TWITTER_API_SECRET=your_twitter_api_secret" >> .env
    echo "TWITTER_ACCESS_TOKEN=your_access_token" >> .env
    echo "TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret" >> .env
    echo "TWITTER_BEARER_TOKEN=your_bearer_token" >> .env
    echo "TWITTER_COMMUNITY_ID=your_community_id" >> .env
fi

# copy the config.yaml.copy to config.yaml
if [ ! -f config.yaml ]; then
    cp config.yaml.copy config.yaml
fi

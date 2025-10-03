echo DB URLs
set DATABASE_URL=mysql://app_user:123456@localhost:3306/agent_app
set DATABASES={"default":"%DATABASE_URL%","analytics":"mysql://app_user:123456@localhost:3306/agent_analytics"}

echo Auth
set JWT_SECRET=change_me_to_a_long_random_secret
set JWT_ALG=HS256
set ACCESS_TOKEN_EXPIRE_MINUTES=60

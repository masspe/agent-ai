echo DB URLs
set DATABASE_URL=mysql+pymysql://app_user:123456@localhost/agent_app?charset=utf8mb4
set STORAGE_DB_URL=mysql+pymysql://app_user:123456@localhost/agent_storage?charset=utf8mb4

echo Auth
set JWT_SECRET=change_me_to_a_long_random_secret
set JWT_ALG=HS256
set ACCESS_TOKEN_EXPIRE_MINUTES=60

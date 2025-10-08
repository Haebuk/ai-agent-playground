import os
import dotenv


dotenv.load_dotenv()


def get_env_variable(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(
            f"'{key}' 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요."
        )
    return value


OPENAI_API_KEY = get_env_variable("OPENAI_API_KEY")
FIRECRAWL_API_KEY = get_env_variable("FIRECRAWL_API_KEY")
GOOGLE_SEARCH_API_KEY = get_env_variable("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = get_env_variable("GOOGLE_SEARCH_CX")

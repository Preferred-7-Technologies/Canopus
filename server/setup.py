from setuptools import setup, find_packages

setup(
    name="Canopus",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.23",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "redis>=5.0.1",
        "aioredis>=2.0.1",
        "openai-whisper>=20231117",
        "torch>=2.0.0",
        "numpy>=1.26.2",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "fakeredis>=2.20.0",
        "httpx>=0.25.1",
        "psycopg2-binary>=2.9.9",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "fakeredis",
            "httpx",
        ],
        "dev": [
            "black",
            "isort",
            "mypy",
            "pre-commit",
        ],
    }
)

# RepoRadar API Readme
This project is a Github repository radar service implemented in FastAPI. The API allows you to fetch the most popular repositories created since a specified date, optionally filtered by language, and limited by number.

## Requirements
- Python 3.7+
- FastAPI
- Redis

## Installation
1. Clone the repository git clone https://github.com/mhsnrafi/repo-radar.git
2. Install the required packages using command:
```bash
pip3 install -r requirements.txt
```

## Usage
1. To start the server, run  docker-compose up -d --build
2. The server runs on http://localhost:8083 by default.
3. Available endpoints:
   1. GET repositories/popular/{top_n}: Fetches the top top_n repositories
   curl --location --request GET 'http://localhost:8083/repositories/popular/10'
   2. GET repositories/popular: Fetches the most popular repositories created since a specified date, optionally filtered by language and limited by number.
   curl --location --request GET 'http://localhost:8083/repositories/popular?since_date=2023-06-01&language=python&top_n=100'
4. To run the tests, run pytest -v
5. To stop the server, run docker-compose down
6. Swagger documentation link: http://localhost:8083/docs

## API Documentation
### RepoRadar
- GET repositories/popular/{top_n}: Fetches the top top_n repositories
- GET repositories/popular: Fetches the most popular repositories created since a specified date, optionally filtered by language and limited by number.

### Functions
#### get_cache_key
   This function generates a unique cache key for a function and a request.

#### cacheable
A decorator for making a function cacheable. It caches the result of a function for a certain period (time-to-live, or TTL), reducing the number of calls to the underlying function.

#### resilient_request
This function handles resilient HTTP requests with retries. It retries a request if an exception occurs during the request. It uses the Tenacity library to implement retry logic.

#### prepare_params
This function prepares the parameters for a GitHub API request.

#### get_top_repositories
This function fetches the top repositories. It's decorated with limiter.limit and cacheable to limit the number of requests per minute and cache the result.

#### get_repositories_since
This function fetches the most popular repositories created since a specified date, optionally filtered by language, and limited by number. It's also decorated with limiter.limit and cacheable to limit the number of requests per minute and cache the result.

## Limitations and Tradeoffs
The RepoRadar API uses caching and rate limiting to improve performance and prevent abuse. However, these methods come with their own tradeoffs.

Caching can greatly improve performance by reducing the number of calls to the underlying GitHub API. However, cached data might be outdated, and there's also the additional complexity of cache invalidation and serialization/deserialization.

Rate limiting prevents abuse of the API but may also limit legitimate high-frequency use.

Also, the current implementation uses a single Redis instance for caching, which might be a bottleneck if the load increases. A distributed cache could be used to improve scalability.

On the data fetching side, the API uses a simple exponential backoff strategy for retrying failed requests. While this improves reliability, it also increases the latency of the API. Other retry strategies could be considered to find a balance between reliability and latency.

## Tests
All endpoints of the application are covered with tests to ensure its correctness and reliability. To run the tests, use the command 
```bash
 docker-compose exec shopapotheke pytest .
```

## Project Structure
The chosen project structure is an adaptation of the domain-driven design (DDD). This structure was chosen because it logically separates different parts of the application and promotes code reusability and separation of concerns. It is a common structure for Python projects, especially web services, due to its maintainability and scalability.

Here's a breakdown of the project structure:
```docker
repo-radar
├── src
│   ├── app
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── limiter.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   └── repository_services.py
│   │   └── __init__.py
│   │   └── main.py
├── test
│   ├── __init__.py
│   ├── conftest.py
│   └── repository_service_test.py
├── .env
├── Dockerfile
├── requirements.txt
├── .gitignore
├── docker-compose.yml
└── README.md
```

1. **src/app/core**: Contains the core components of the application. Here, you'll find modules for application-wide configurations (config.py), rate limiting (limiter.py), and caching.
2. **src/app/services**: Contains the service layer of the application (repository_services.py). The service layer handles the business logic of the application, interacting with the database or external APIs, processing data, and so on.
3. **src/app/main.py**: Entry point of the application. It defines and starts the FastAPI application.
4. **.env**: Contains environment variables, which can include configurations, secrets, and other variables that should not be hard-coded in the application code.
5. **test**: Contains all the test files for the application, like repository_service_test.py.
6. **docker-compose.yml and Dockerfile**: Used to create a Docker container for the application.
7. **README.md**: Contains the documentation of the application.
8. **requirements.txt**: Lists the Python dependencies that need to be installed for the application.

# Architecture
The application follows a version of the layered architecture. This architecture was chosen because it allows for separation of concerns, where each layer has a specific role and responsibility. It makes the application easier to understand, maintain, and develop further.

The architecture consists of the following layers:

1. Presentation Layer: This is represented by the FastAPI routes in main.py that handle HTTP requests and responses.

2. Service Layer: This is in the services directory. It encapsulates the business logic of the application.

3. Infrastructure Layer

# Answers to questions:
## How is caching implemented in  API?
Caching is implemented using a custom decorator cacheable. This decorator generates a unique cache key for each function call based on function name and the provided request. If a cached result exists for this key, it returns the cached result. Otherwise, it calls the function, caches the result, and returns the result. The cacheable decorator also handles exceptions related to serialization and deserialization of cached results. The cache is implemented using Redis.

## How does the rate limiting work in API?
Rate limiting is implemented using a custom middleware limiter. It uses the ratelimit library to limit the number of requests that can be made to the API within a certain time period. In this API, the rate limit is set to


## Future Improvements:
### Continuous Integration and Deployment with CircleCI and Heroku
For integrating CircleCI and Heroku, we would need to setup a pipeline that builds a Docker image, tests the application, and then, on successful tests, pushes the Docker image to the Heroku Docker Registry and deploys it to Heroku.

In the CircleCI configuration file, we would define these steps as jobs. The "build" job would checkout the code and build the Docker image. The "test" job would run the test suite. The "deploy" job would login to Heroku's Docker Registry and push the built Docker image. Then, it would release the image to the Heroku app.

Remember to set HEROKU_API_KEY and HEROKU_APP_NAME in the CircleCI environment variables.

Ensure that Dockerfile is at the root of your project, and Docker Compose can run the tests.
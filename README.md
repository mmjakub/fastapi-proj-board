# fastapi-proj-board
Simple project management service implemented for learning purposes

# Current state
* First iteration yielded a working prototype that seems to smell like **Big Ball of Mud**
* There is some hope: there is `FileService` abstraction (port) which has three implementations (adapters):
   * Local Files
   * Fake using `tempfiles`
   * S3 using `boto3`
* Verified funcionality by running manual tests on local deployment connecting to local PostgreSQL and S3
* Implemented pytest fixtures to use `fastapi.TestClient` and `FastAPI.dependency_overrides` with fakes(inmemory sqlite and tempfiles)
* Some business use cases are covered by e2e api tests using fakes
* Created basic CI Action that runs pytest
* Created Action to build and push docker image to AWS ECR when creating github release
* App is deployed to ECS and can be tested [here](https://proj-board-1650300757.eu-west-1.elb.amazonaws.com/docs) (used self-signed ssl cert)

# In progress
* considering domain modeling and testing strategies
* learning about architecture and patterns from [Cosmic Python](https://www.cosmicpython.com/book/preface.html)
* learning and experimenting with AWS - ECR, ECS, S3, RDS

# Next steps
* consider ports & adapters architecure and reimplement using TDD and maybe some DDD?
* create unit tests for use cases (application layer) using fakes
* expand on domain - document versioning, granular permissions for project collaborators, project tasks, notifications for project members, etc.
* consume some outside rest service -> maybe document summary via LLM or searching with RAG?
* CD pipeline with ECR

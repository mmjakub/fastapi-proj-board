# fastapi-proj-board
Simple project management service implemented for learning purposes

# current state
* First iteration yielded a CRUD(e) prototype mainly architected as **Big Ball of Mud**
* Connects to local PostgreSQL and S3
* There is hope: there is `FileService` port which has local files and S3 adapters
* Unit testing is practically unfeasible, only e2e api test make sense here, and they could become integration tests in the long term

# next steps
* consider ports & adapters architecure and reimplement using TDD and maybe some DDD?
* Unit test usecases using fakes
* expand on domain - document versioning, granular permissions for project collaborators, project tasks, notifications for project members, etc.
* consume some outside rest service -> maybe document summary via LLM or searching with RAG?
* CI using github actions
* explore containerization and deployment to ECS
* CD pipeline with ECR

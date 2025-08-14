```mermaid
erDiagram
  user ||--o{ project: owns
  user ||--|{ collaborator: is
  user {
    int id PK
    string username
    string password
  }
  project ||--|{ collaborator: has
  project {
    int id PK
    int owner_id FK
    string name
    string description
  }
  collaborator {
    int user_id PK, FK
    int project_id PK, FK
  }
  project ||--o{ document : contains
  document {
    int id PK
    int project_id FK
    string upload_filename
  }
  
```

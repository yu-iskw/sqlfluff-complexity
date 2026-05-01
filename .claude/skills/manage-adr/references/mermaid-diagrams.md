# Mermaid Diagrams for ADRs

This guide provides examples and templates for using Mermaid diagrams in Architecture Decision Records (ADRs). Mermaid diagrams help visualize architectural decisions, system designs, and relationships.

## When to Use Diagrams

- **System Architecture**: Show component relationships and data flow
- **Software Architecture**: Illustrate module organization and dependencies
- **Sequence Diagrams**: Document interaction flows and decision processes
- **Concept Diagrams**: Visualize abstract concepts and relationships
- **State Diagrams**: Show state transitions and workflows
- **Class Diagrams**: Document type relationships and hierarchies

## Diagram Types

### System Architecture Diagram

Use to show high-level system components and their relationships:

```mermaid
graph TB
    subgraph clientLayer [Client Layer]
        CLI[CLI Tool]
        Web[Web App]
    end

    subgraph apiLayer [API Layer]
        API[REST API]
    end

    subgraph serviceLayer [Service Layer]
        Auth[Auth Service]
        Data[Data Service]
    end

    subgraph dataLayer [Data Layer]
        DB[(Database)]
        Cache[(Cache)]
    end

    CLI --> API
    Web --> API
    API --> Auth
    API --> Data
    Data --> DB
    Data --> Cache
```

### Software Architecture Diagram

Use to show module organization and package dependencies:

```mermaid
graph LR
    subgraph commonPkg [@lightdash-tools/common]
        Types[Types]
        Utils[Utils]
    end

    subgraph clientPkg [@lightdash-tools/client]
        Client[HTTP Client]
    end

    subgraph cliPkg [@lightdash-tools/cli]
        CLI[CLI Commands]
    end

    CLI --> Client
    Client --> Types
    CLI --> Types
    Client --> Utils
```

### Sequence Diagram

Use to document interaction flows, decision processes, or API call sequences:

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Client
    participant API

    User->>CLI: lightdash projects get
    CLI->>Client: initializeClient()
    Client->>Client: loadConfig()
    CLI->>Client: projects.get(id)
    Client->>API: GET /api/v1/projects/{id}
    API-->>Client: Project data
    Client-->>CLI: Project object
    CLI-->>User: Display project info
```

### Concept Diagram

Use to visualize abstract concepts, relationships, or decision trees:

```mermaid
graph TD
    Start[Architectural Decision] --> Evaluate{Evaluate Options}
    Evaluate -->|Option 1| Score1["Score: 85/100"]
    Evaluate -->|Option 2| Score2["Score: 90/100"]
    Evaluate -->|Option 3| Score3["Score: 75/100"]
    Score1 --> Compare[Compare Scores]
    Score2 --> Compare
    Score3 --> Compare
    Compare --> Select[Select Best Option]
    Select --> Implement[Implement Decision]
```

### Component Diagram

Use to show component relationships and interfaces:

```mermaid
graph TB
    subgraph commandModule [Command Module]
        Cmd[Command Base]
        OrgCmd[Organization Command]
        ProjCmd[Projects Command]
    end

    subgraph clientModule [Client Module]
        Client[HTTP Client]
        OrgClient[Organization Client]
        ProjClient[Projects Client]
    end

    OrgCmd --> OrgClient
    ProjCmd --> ProjClient
    OrgClient --> Client
    ProjClient --> Client
    Cmd -.->|extends| OrgCmd
    Cmd -.->|extends| ProjCmd
```

### State Diagram

Use to show state transitions and workflows:

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Initialized: initialize()
    Initialized --> Authenticated: authenticate()
    Authenticated --> Ready: loadConfig()
    Ready --> Executing: executeCommand()
    Executing --> Ready: commandComplete()
    Ready --> [*]: shutdown()
    Authenticated --> Error: authFailed()
    Executing --> Error: executionFailed()
    Error --> Ready: retry()
```

### Class/Type Diagram

Use to document type relationships and hierarchies:

```mermaid
classDiagram
    class Command {
        +execute()
        +validate()
    }

    class OrganizationCommand {
        +get()
    }

    class ProjectsCommand {
        +get()
        +list()
    }

    class Client {
        +request()
    }

    Command <|-- OrganizationCommand
    Command <|-- ProjectsCommand
    OrganizationCommand --> Client
    ProjectsCommand --> Client
```

## Best Practices

1. **Placement**: Add diagrams in the "Decision" or "Architecture" section of your ADR
2. **Context**: Always provide a brief description before the diagram explaining what it shows
3. **Simplicity**: Keep diagrams focused - one diagram per concept or relationship
4. **Labels**: Use clear, descriptive labels for nodes and edges
5. **Consistency**: Use consistent naming conventions across diagrams
6. **Version Control**: Mermaid diagrams render in GitHub, GitLab, and many Markdown viewers

## Common Patterns

### Before/After Comparison

```mermaid
graph LR
    subgraph before [Before]
        A1[Package A] --> B1[Package B]
        A1 --> C1[Package C]
    end

    subgraph after [After]
        A2[Package A] --> Common[Common Package]
        B2[Package B] --> Common
        C2[Package C] --> Common
    end
```

### Decision Flow

```mermaid
flowchart TD
    Start[Need to make decision] --> Analyze[Analyze requirements]
    Analyze --> Options[Identify options]
    Options --> Evaluate[Evaluate each option]
    Evaluate --> Compare[Compare scores]
    Compare --> Select[Select best option]
    Select --> Document[Document decision]
    Document --> Implement[Implement]
```

### Dependency Graph

```mermaid
graph TD
    Root[Root Package] --> Common[Common Package]
    Root --> Client[Client Package]
    Root --> CLI[CLI Package]
    Client --> Common
    CLI --> Common
    CLI --> Client
```

## Rendering

Mermaid diagrams render automatically in:

- GitHub/GitLab Markdown viewers
- Many IDEs (VS Code with Mermaid extension)
- Documentation sites (MkDocs, Docusaurus, etc.)
- Online editors: [Mermaid Live Editor](https://mermaid.live/)

## References

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Syntax Guide](https://mermaid.js.org/intro/syntax-reference.html)
- [Mermaid Diagram Types](https://mermaid.js.org/intro/getting-started.html)

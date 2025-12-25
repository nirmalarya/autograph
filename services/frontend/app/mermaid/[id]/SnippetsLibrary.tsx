'use client';

import { useState } from 'react';

export interface Snippet {
  id: string;
  title: string;
  description: string;
  category: 'flowchart' | 'sequence' | 'class' | 'state' | 'er' | 'gantt' | 'git' | 'other';
  code: string;
}

export const SNIPPET_LIBRARY: Snippet[] = [
  // Basic Flowchart Snippets
  {
    id: 'basic-flowchart',
    title: 'Basic Flowchart',
    description: 'A simple flowchart with decision nodes',
    category: 'flowchart',
    code: `graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]`
  },
  {
    id: 'microservices-architecture',
    title: 'Microservices Architecture',
    description: 'Template for microservices architecture diagram',
    category: 'flowchart',
    code: `graph TB
    subgraph "Frontend"
        A[Web App]
        B[Mobile App]
    end

    subgraph "API Gateway"
        C[API Gateway]
    end

    subgraph "Services"
        D[Auth Service]
        E[User Service]
        F[Order Service]
        G[Payment Service]
    end

    subgraph "Data"
        H[(User DB)]
        I[(Order DB)]
        J[(Payment DB)]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    D --> H
    E --> H
    F --> I
    G --> J`
  },
  {
    id: 'deployment-pipeline',
    title: 'Deployment Pipeline',
    description: 'CI/CD deployment pipeline',
    category: 'flowchart',
    code: `graph LR
    A[Code Commit] --> B[Build]
    B --> C{Tests Pass?}
    C -->|Yes| D[Deploy to Staging]
    C -->|No| E[Notify Developer]
    D --> F{QA Approved?}
    F -->|Yes| G[Deploy to Production]
    F -->|No| E
    G --> H[Monitor]`
  },

  // Sequence Diagram Snippets
  {
    id: 'sequence-basic',
    title: 'Sequence Diagram',
    description: 'Basic sequence diagram template',
    category: 'sequence',
    code: `sequenceDiagram
    participant U as User
    participant A as Application
    participant D as Database

    U->>A: Request data
    A->>D: Query database
    D-->>A: Return results
    A-->>U: Display data`
  },
  {
    id: 'sequence-auth',
    title: 'Authentication Flow',
    description: 'User authentication sequence',
    category: 'sequence',
    code: `sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant D as Database

    U->>F: Enter credentials
    F->>A: Login request
    A->>D: Verify credentials
    D-->>A: User data
    A->>A: Generate JWT
    A-->>F: Return token
    F-->>U: Login successful`
  },
  {
    id: 'sequence-api',
    title: 'API Request Flow',
    description: 'RESTful API request sequence',
    category: 'sequence',
    code: `sequenceDiagram
    participant C as Client
    participant G as Gateway
    participant S as Service
    participant DB as Database
    participant Q as Queue

    C->>G: POST /api/orders
    G->>S: Create order
    S->>DB: Insert order
    DB-->>S: Order ID
    S->>Q: Publish event
    S-->>G: 201 Created
    G-->>C: Order response`
  },

  // ER Diagram Snippets
  {
    id: 'er-basic',
    title: 'ER Diagram',
    description: 'Basic entity-relationship diagram',
    category: 'er',
    code: `erDiagram
    USER ||--o{ ORDER : places
    USER {
        int id PK
        string email
        string name
        date created_at
    }
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        int id PK
        int user_id FK
        date created_at
        string status
    }
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
    }
    PRODUCT {
        int id PK
        string name
        string description
        decimal price
    }`
  },
  {
    id: 'er-ecommerce',
    title: 'E-commerce Database',
    description: 'Complete e-commerce database schema',
    category: 'er',
    code: `erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--o{ REVIEW : writes
    CUSTOMER {
        int id PK
        string email
        string password_hash
        string name
        string address
    }
    ORDER ||--|{ LINE_ITEM : contains
    ORDER {
        int id PK
        int customer_id FK
        datetime order_date
        string status
        decimal total
    }
    PRODUCT ||--o{ LINE_ITEM : "appears in"
    PRODUCT ||--o{ REVIEW : receives
    PRODUCT ||--o{ CATEGORY : "belongs to"
    PRODUCT {
        int id PK
        string name
        string description
        decimal price
        int stock
    }
    LINE_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
    }
    REVIEW {
        int id PK
        int customer_id FK
        int product_id FK
        int rating
        string comment
    }
    CATEGORY {
        int id PK
        string name
    }`
  },

  // Class Diagram Snippets
  {
    id: 'class-basic',
    title: 'Class Diagram',
    description: 'Basic class diagram with inheritance',
    category: 'class',
    code: `classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
        +eat()
    }
    class Dog {
        +String breed
        +bark()
        +fetch()
    }
    class Cat {
        +String color
        +meow()
        +scratch()
    }
    Animal <|-- Dog
    Animal <|-- Cat`
  },
  {
    id: 'class-design-pattern',
    title: 'Design Pattern',
    description: 'Observer design pattern',
    category: 'class',
    code: `classDiagram
    class Subject {
        -List~Observer~ observers
        +attach(Observer)
        +detach(Observer)
        +notify()
    }
    class Observer {
        <<interface>>
        +update()
    }
    class ConcreteSubject {
        -state
        +getState()
        +setState()
    }
    class ConcreteObserver {
        -observerState
        +update()
    }
    Subject <|-- ConcreteSubject
    Observer <|.. ConcreteObserver
    Subject o-- Observer`
  },

  // State Diagram Snippets
  {
    id: 'state-basic',
    title: 'State Diagram',
    description: 'Basic state machine',
    category: 'state',
    code: `stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : Start
    Processing --> Success : Complete
    Processing --> Failed : Error
    Success --> [*]
    Failed --> Idle : Retry
    Failed --> [*] : Cancel`
  },
  {
    id: 'state-order',
    title: 'Order Lifecycle',
    description: 'E-commerce order state machine',
    category: 'state',
    code: `stateDiagram-v2
    [*] --> Pending
    Pending --> Confirmed : Payment Received
    Pending --> Cancelled : Customer Cancels
    Confirmed --> Processing : Start Fulfillment
    Processing --> Shipped : Package Dispatched
    Shipped --> Delivered : Customer Receives
    Delivered --> [*]
    Cancelled --> [*]
    Processing --> Cancelled : Out of Stock`
  },

  // Gantt Chart Snippets
  {
    id: 'gantt-basic',
    title: 'Gantt Chart',
    description: 'Basic project timeline',
    category: 'gantt',
    code: `gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Planning
    Requirements    :done, req, 2024-01-01, 7d
    Design         :done, des, after req, 5d
    section Development
    Backend        :active, dev1, after des, 14d
    Frontend       :dev2, after des, 14d
    Testing        :test, after dev1, 7d
    section Deployment
    Deploy         :deploy, after test, 2d`
  },
  {
    id: 'gantt-sprint',
    title: 'Sprint Planning',
    description: 'Agile sprint Gantt chart',
    category: 'gantt',
    code: `gantt
    title Sprint 1 - Two Week Sprint
    dateFormat YYYY-MM-DD
    section Sprint Planning
    Planning Meeting    :milestone, m1, 2024-01-08, 0d
    section Week 1
    User Story 1       :active, us1, 2024-01-08, 3d
    User Story 2       :us2, 2024-01-08, 5d
    Code Review        :cr1, after us1, 1d
    section Week 2
    User Story 3       :us3, 2024-01-15, 4d
    Testing            :test, 2024-01-17, 3d
    Sprint Review      :milestone, m2, 2024-01-19, 0d`
  },

  // Git Graph Snippets
  {
    id: 'git-basic',
    title: 'Git Graph',
    description: 'Basic git branching workflow',
    category: 'git',
    code: `gitGraph
    commit
    commit
    branch develop
    checkout develop
    commit
    commit
    checkout main
    merge develop
    commit`
  },
  {
    id: 'git-feature',
    title: 'Feature Branch Workflow',
    description: 'Git flow with feature branches',
    category: 'git',
    code: `gitGraph
    commit id: "Initial"
    branch develop
    checkout develop
    commit id: "Setup"
    branch feature/login
    checkout feature/login
    commit id: "Add login UI"
    commit id: "Add auth logic"
    checkout develop
    merge feature/login
    checkout main
    merge develop tag: "v1.0"`
  },

  // Advanced Sequence Diagram Features (Feature #292, #293)
  {
    id: 'sequence-notes',
    title: 'Sequence with Notes',
    description: 'Sequence diagram with notes and comments',
    category: 'sequence',
    code: `sequenceDiagram
    participant Alice
    participant Bob
    participant Carol

    Note over Alice: Alice starts here
    Alice->>Bob: Hello Bob!
    Note over Bob: Bob processes request
    Bob->>Carol: Forward to Carol
    Note over Alice,Carol: This note spans multiple participants
    Carol-->>Alice: Response to Alice
    Note right of Carol: Carol's note on the right
    Note left of Alice: Alice's note on the left`
  },
  {
    id: 'sequence-parallel',
    title: 'Parallel Messages',
    description: 'Sequence diagram with parallel execution',
    category: 'sequence',
    code: `sequenceDiagram
    participant Alice
    participant Bob
    participant Carol

    Alice->>Bob: Sequential message

    par Parallel Block
        Alice->>Bob: Parallel message 1
    and
        Alice->>Carol: Parallel message 2
    end

    Bob->>Alice: Response from Bob
    Carol->>Alice: Response from Carol

    par Multiple Parallel Tasks
        Alice->>Bob: Task A
    and
        Alice->>Carol: Task B
    and
        Bob->>Carol: Task C
    end`
  },

  // Advanced Class Diagram Features (Feature #294, #295)
  {
    id: 'class-visibility',
    title: 'Visibility Modifiers',
    description: 'Class diagram with public, private, protected members',
    category: 'class',
    code: `classDiagram
    class User {
        +String publicField
        -String privateField
        #String protectedField
        ~String packageField

        +publicMethod()
        -privateMethod()
        #protectedMethod()
        ~packageMethod()
    }

    class Account {
        +String username
        -String passwordHash
        #Date createdAt

        +login(password) bool
        -validatePassword(password) bool
        #updateLastLogin() void
    }`
  },
  {
    id: 'class-abstract',
    title: 'Abstract Classes & Interfaces',
    description: 'Abstract classes and interface patterns',
    category: 'class',
    code: `classDiagram
    class IUser {
        <<interface>>
        +getId() String
        +getEmail() String
        +save() void
    }

    class AbstractUser {
        <<abstract>>
        #String id
        #String email
        +getId() String
        +getEmail() String
        +save()* void
    }

    class RegularUser {
        -String password
        +login() bool
    }

    class AdminUser {
        -Array~String~ permissions
        +hasPermission() bool
    }

    IUser <|.. AbstractUser
    AbstractUser <|-- RegularUser
    AbstractUser <|-- AdminUser`
  },

  // Advanced State Diagram Features (Feature #296, #297)
  {
    id: 'state-choice',
    title: 'Choice Nodes',
    description: 'State diagram with conditional choice nodes',
    category: 'state',
    code: `stateDiagram-v2
    [*] --> CheckAuth
    CheckAuth --> choice1

    state choice1 <<choice>>
    choice1 --> LoggedIn: if authenticated
    choice1 --> Login: if not authenticated

    Login --> CheckAuth: after login

    LoggedIn --> Processing: start task
    Processing --> choice2

    state choice2 <<choice>>
    choice2 --> Success: if valid
    choice2 --> Error: if error
    choice2 --> Retry: if timeout

    Success --> [*]
    Error --> [*]
    Retry --> Processing`
  },
  {
    id: 'state-fork-join',
    title: 'Fork and Join',
    description: 'Parallel state execution with fork and join',
    category: 'state',
    code: `stateDiagram-v2
    [*] --> Init
    Init --> fork1

    state fork1 <<fork>>
    fork1 --> ProcessA
    fork1 --> ProcessB
    fork1 --> ProcessC

    ProcessA --> join1
    ProcessB --> join1
    ProcessC --> join1

    state join1 <<join>>
    join1 --> Complete
    Complete --> [*]

    state ProcessA {
        [*] --> TaskA1
        TaskA1 --> TaskA2
        TaskA2 --> [*]
    }

    state ProcessB {
        [*] --> TaskB1
        TaskB1 --> [*]
    }`
  },

  // Advanced Gantt Features (Feature #298, #299)
  {
    id: 'gantt-dependencies',
    title: 'Task Dependencies',
    description: 'Gantt chart with task dependencies',
    category: 'gantt',
    code: `gantt
    title Project with Dependencies
    dateFormat YYYY-MM-DD

    section Foundation
    Requirements    :done, req, 2024-01-01, 7d
    Architecture    :done, arch, after req, 5d

    section Development
    Backend API     :active, be, after arch, 14d
    Database        :db, after arch, 10d
    Frontend UI     :fe, after db, 14d
    Integration     :int, after be, 7d

    section Testing
    Unit Tests      :test1, after int, 5d
    Integration     :test2, after test1, 5d
    UAT            :test3, after test2, 7d

    section Deployment
    Staging        :deploy1, after test3, 2d
    Production     :deploy2, after deploy1, 1d`
  },
  {
    id: 'gantt-critical',
    title: 'Critical Path',
    description: 'Gantt with critical path highlighting',
    category: 'gantt',
    code: `gantt
    title Critical Path Analysis
    dateFormat YYYY-MM-DD

    section Critical Path
    Design         :crit, des, 2024-01-01, 10d
    Development    :crit, dev, after des, 20d
    Testing        :crit, test, after dev, 10d
    Deployment     :crit, deploy, after test, 3d

    section Non-Critical
    Documentation  :doc, 2024-01-01, 30d
    Training       :train, after doc, 10d
    Marketing      :market, 2024-01-15, 20d

    section Milestones
    Design Complete    :milestone, m1, after des, 0d
    Development Done   :milestone, m2, after dev, 0d
    Go Live           :milestone, m3, after deploy, 0d`
  },

  // Git Advanced Features (Feature #300)
  {
    id: 'git-cherrypick',
    title: 'Cherry-pick Workflow',
    description: 'Git graph with cherry-pick operations',
    category: 'git',
    code: `gitGraph
    commit id: "Initial"
    commit id: "Feature work"

    branch hotfix
    checkout hotfix
    commit id: "Critical fix"
    checkout main
    cherry-pick id: "Critical fix"

    branch feature
    checkout feature
    commit id: "Feature A"
    commit id: "Feature B"
    commit id: "Feature C"

    checkout main
    cherry-pick id: "Feature B"

    checkout feature
    commit id: "Feature D"

    checkout main
    merge feature tag: "v2.0"`
  }
];

interface SnippetsLibraryProps {
  onInsert: (code: string) => void;
}

export default function SnippetsLibrary({ onInsert }: SnippetsLibraryProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const categories = [
    { id: 'all', label: 'All Snippets', icon: '📚' },
    { id: 'flowchart', label: 'Flowcharts', icon: '🔀' },
    { id: 'sequence', label: 'Sequence', icon: '⏱️' },
    { id: 'class', label: 'Class', icon: '🏛️' },
    { id: 'state', label: 'State', icon: '🔄' },
    { id: 'er', label: 'ER Diagram', icon: '🗂️' },
    { id: 'gantt', label: 'Gantt', icon: '📊' },
    { id: 'git', label: 'Git', icon: '🌿' },
  ];

  const filteredSnippets = SNIPPET_LIBRARY.filter(snippet => {
    const matchesCategory = selectedCategory === 'all' || snippet.category === selectedCategory;
    const matchesSearch = searchQuery === '' ||
      snippet.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      snippet.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleInsert = (code: string) => {
    onInsert(code);
    setIsOpen(false);
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition flex items-center gap-2 border border-gray-300 rounded-md hover:bg-gray-50"
        title="Code Snippets"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
        </svg>
        Snippets
      </button>

      {/* Snippets Panel */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Code Snippets Library</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search snippets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 flex overflow-hidden">
              {/* Categories Sidebar */}
              <div className="w-48 flex-shrink-0 border-r border-gray-200 overflow-y-auto">
                <nav className="p-2 space-y-1">
                  {categories.map(category => (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm transition flex items-center gap-2 ${
                        selectedCategory === category.id
                          ? 'bg-blue-50 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span>{category.icon}</span>
                      <span>{category.label}</span>
                    </button>
                  ))}
                </nav>
              </div>

              {/* Snippets Grid */}
              <div className="flex-1 overflow-y-auto p-6">
                {filteredSnippets.length === 0 ? (
                  <div className="text-center py-12">
                    <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-gray-500">No snippets found</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredSnippets.map(snippet => (
                      <div
                        key={snippet.id}
                        className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition cursor-pointer"
                        onClick={() => handleInsert(snippet.code)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-gray-900">{snippet.title}</h3>
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded capitalize">
                            {snippet.category}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{snippet.description}</p>
                        <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto max-h-32">
                          <code>{snippet.code}</code>
                        </pre>
                        <button
                          className="mt-3 w-full py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleInsert(snippet.code);
                          }}
                        >
                          Insert Code
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

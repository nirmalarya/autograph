'use client';

/**
 * Feature #670: Polish: Onboarding: Example Diagrams
 * 
 * A gallery of pre-made example diagrams that users can view, duplicate, and learn from.
 * Helps new users understand what's possible and get started quickly.
 * 
 * Features:
 * - Gallery of professional example diagrams
 * - Categories: Architecture, Flowchart, ERD, Sequence, Class, State
 * - Preview thumbnails
 * - One-click duplicate to create editable copy
 * - Detailed descriptions
 * - Responsive grid layout
 * - Dark mode support
 * - Accessibility (ARIA labels, keyboard navigation)
 * - Loading states
 * - Error handling
 */

import { useState, useCallback } from 'react';
import {
  Copy,
  X,
  Network,
  GitBranch,
  Database,
  Activity,
  Box,
  Workflow,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/lib/api-config';

interface ExampleDiagram {
  id: string;
  title: string;
  description: string;
  category: 'architecture' | 'flowchart' | 'erd' | 'sequence' | 'class' | 'state';
  thumbnail: string;
  canvasData?: any;
  mermaidCode?: string;
  type: 'canvas' | 'mermaid';
  complexity: 'beginner' | 'intermediate' | 'advanced';
  tags: string[];
}

const EXAMPLE_DIAGRAMS: ExampleDiagram[] = [
  // Architecture Examples
  {
    id: 'microservices-arch',
    title: 'Microservices Architecture',
    description: 'A complete microservices architecture with API gateway, services, databases, and message queues. Perfect for learning distributed systems design.',
    category: 'architecture',
    thumbnail: '🏗️',
    type: 'canvas',
    complexity: 'advanced',
    tags: ['microservices', 'cloud', 'distributed', 'api'],
    canvasData: {
      shapes: [
        { type: 'rectangle', x: 100, y: 50, width: 150, height: 80, text: 'API Gateway', color: 'blue' },
        { type: 'rectangle', x: 50, y: 200, width: 120, height: 80, text: 'User Service', color: 'green' },
        { type: 'rectangle', x: 200, y: 200, width: 120, height: 80, text: 'Order Service', color: 'green' },
        { type: 'rectangle', x: 350, y: 200, width: 120, height: 80, text: 'Payment Service', color: 'green' },
        { type: 'cylinder', x: 50, y: 350, width: 100, height: 60, text: 'User DB', color: 'purple' },
        { type: 'cylinder', x: 200, y: 350, width: 100, height: 60, text: 'Order DB', color: 'purple' },
        { type: 'cylinder', x: 350, y: 350, width: 100, height: 60, text: 'Payment DB', color: 'purple' },
        { type: 'rectangle', x: 500, y: 250, width: 120, height: 80, text: 'Message Queue', color: 'orange' },
      ]
    }
  },
  {
    id: 'three-tier-arch',
    title: '3-Tier Web Application',
    description: 'Classic 3-tier architecture with presentation, business logic, and data layers. Great starting point for web applications.',
    category: 'architecture',
    thumbnail: '📊',
    type: 'canvas',
    complexity: 'beginner',
    tags: ['web', 'architecture', 'layers', 'basic'],
    canvasData: {
      shapes: [
        { type: 'rectangle', x: 150, y: 50, width: 200, height: 80, text: 'Presentation Layer\n(React/Next.js)', color: 'blue' },
        { type: 'rectangle', x: 150, y: 180, width: 200, height: 80, text: 'Business Logic Layer\n(FastAPI/Node.js)', color: 'green' },
        { type: 'rectangle', x: 150, y: 310, width: 200, height: 80, text: 'Data Layer\n(PostgreSQL)', color: 'purple' },
      ]
    }
  },
  {
    id: 'serverless-arch',
    title: 'Serverless Architecture',
    description: 'Modern serverless architecture using AWS Lambda, API Gateway, DynamoDB, and S3. Learn cloud-native design patterns.',
    category: 'architecture',
    thumbnail: '☁️',
    type: 'mermaid',
    complexity: 'intermediate',
    tags: ['serverless', 'aws', 'cloud', 'lambda'],
    mermaidCode: `graph TB
    User[User] --> APIGateway[API Gateway]
    APIGateway --> Lambda1[Lambda: Auth]
    APIGateway --> Lambda2[Lambda: Data]
    APIGateway --> Lambda3[Lambda: Upload]
    Lambda1 --> DynamoDB[(DynamoDB)]
    Lambda2 --> DynamoDB
    Lambda3 --> S3[S3 Bucket]
    Lambda1 --> Cognito[Cognito]
    Lambda2 --> SQS[SQS Queue]
    SQS --> Lambda4[Lambda: Process]
    Lambda4 --> SNS[SNS Topic]`
  },

  // Flowchart Examples
  {
    id: 'user-registration',
    title: 'User Registration Flow',
    description: 'Complete user registration process with validation, email verification, and error handling. Essential for any application.',
    category: 'flowchart',
    thumbnail: '👤',
    type: 'mermaid',
    complexity: 'beginner',
    tags: ['flowchart', 'registration', 'auth', 'user'],
    mermaidCode: `flowchart TD
    Start([User Visits Registration Page]) --> Input[Enter Email & Password]
    Input --> Validate{Valid Input?}
    Validate -->|No| Error1[Show Error Message]
    Error1 --> Input
    Validate -->|Yes| CheckEmail{Email Exists?}
    CheckEmail -->|Yes| Error2[Show 'Email Already Exists']
    Error2 --> Input
    CheckEmail -->|No| Create[Create Account]
    Create --> SendEmail[Send Verification Email]
    SendEmail --> ShowSuccess[Show Success Message]
    ShowSuccess --> End([Redirect to Login])`
  },
  {
    id: 'order-processing',
    title: 'E-Commerce Order Processing',
    description: 'Order processing workflow including payment, inventory check, and fulfillment. Learn business process modeling.',
    category: 'flowchart',
    thumbnail: '🛒',
    type: 'mermaid',
    complexity: 'intermediate',
    tags: ['flowchart', 'ecommerce', 'order', 'payment'],
    mermaidCode: `flowchart TD
    Start([Customer Places Order]) --> CheckInventory{Items in Stock?}
    CheckInventory -->|No| OutOfStock[Notify Out of Stock]
    OutOfStock --> End1([Cancel Order])
    CheckInventory -->|Yes| ProcessPayment[Process Payment]
    ProcessPayment --> PaymentSuccess{Payment Successful?}
    PaymentSuccess -->|No| PaymentFailed[Payment Failed]
    PaymentFailed --> Retry{Retry?}
    Retry -->|Yes| ProcessPayment
    Retry -->|No| End2([Cancel Order])
    PaymentSuccess -->|Yes| UpdateInventory[Update Inventory]
    UpdateInventory --> CreateShipment[Create Shipment]
    CreateShipment --> SendConfirmation[Send Order Confirmation]
    SendConfirmation --> End3([Order Complete])`
  },

  // ERD Examples
  {
    id: 'ecommerce-erd',
    title: 'E-Commerce Database Schema',
    description: 'Complete database schema for an e-commerce platform with users, products, orders, and payments. Learn data modeling.',
    category: 'erd',
    thumbnail: '🗄️',
    type: 'mermaid',
    complexity: 'intermediate',
    tags: ['erd', 'database', 'ecommerce', 'schema'],
    mermaidCode: `erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        string id PK
        string email
        string name
        string password_hash
        datetime created_at
    }
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        string id PK
        string customer_id FK
        decimal total_amount
        string status
        datetime created_at
    }
    ORDER_ITEM }o--|| PRODUCT : references
    ORDER_ITEM {
        string id PK
        string order_id FK
        string product_id FK
        int quantity
        decimal price
    }
    PRODUCT {
        string id PK
        string name
        string description
        decimal price
        int stock_quantity
        string category
    }
    ORDER ||--|| PAYMENT : has
    PAYMENT {
        string id PK
        string order_id FK
        decimal amount
        string method
        string status
        datetime processed_at
    }`
  },
  {
    id: 'blog-erd',
    title: 'Blog Platform Database',
    description: 'Database design for a blog platform with posts, comments, tags, and user relationships. Great for content management systems.',
    category: 'erd',
    thumbnail: '📝',
    type: 'mermaid',
    complexity: 'beginner',
    tags: ['erd', 'blog', 'cms', 'content'],
    mermaidCode: `erDiagram
    USER ||--o{ POST : writes
    USER ||--o{ COMMENT : writes
    USER {
        string id PK
        string username
        string email
        string bio
        datetime joined_at
    }
    POST ||--o{ COMMENT : has
    POST }o--o{ TAG : tagged_with
    POST {
        string id PK
        string author_id FK
        string title
        text content
        string status
        datetime published_at
    }
    COMMENT {
        string id PK
        string post_id FK
        string author_id FK
        text content
        datetime created_at
    }
    TAG {
        string id PK
        string name
        string slug
    }`
  },

  // Sequence Diagram Examples
  {
    id: 'api-authentication',
    title: 'API Authentication Flow',
    description: 'JWT authentication sequence showing login, token generation, and API requests. Essential for secure applications.',
    category: 'sequence',
    thumbnail: '🔐',
    type: 'mermaid',
    complexity: 'intermediate',
    tags: ['sequence', 'auth', 'jwt', 'api'],
    mermaidCode: `sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database
    participant TokenService

    User->>Frontend: Enter credentials
    Frontend->>API: POST /login
    API->>Database: Verify credentials
    Database-->>API: User found
    API->>TokenService: Generate JWT
    TokenService-->>API: Access & Refresh tokens
    API-->>Frontend: Return tokens
    Frontend->>Frontend: Store tokens
    Frontend-->>User: Login successful
    
    Note over User,TokenService: Subsequent API Request
    
    User->>Frontend: Request data
    Frontend->>API: GET /data (with token)
    API->>TokenService: Verify token
    TokenService-->>API: Token valid
    API->>Database: Fetch data
    Database-->>API: Return data
    API-->>Frontend: Return data
    Frontend-->>User: Display data`
  },
  {
    id: 'payment-processing',
    title: 'Payment Processing Sequence',
    description: 'Payment gateway integration showing the complete flow from checkout to confirmation. Learn payment system design.',
    category: 'sequence',
    thumbnail: '💳',
    type: 'mermaid',
    complexity: 'advanced',
    tags: ['sequence', 'payment', 'gateway', 'transaction'],
    mermaidCode: `sequenceDiagram
    participant Customer
    participant Frontend
    participant Backend
    participant PaymentGateway
    participant Bank
    participant Database

    Customer->>Frontend: Click "Pay Now"
    Frontend->>Backend: POST /checkout
    Backend->>Database: Create order (pending)
    Database-->>Backend: Order ID
    Backend-->>Frontend: Payment session
    Frontend->>PaymentGateway: Initialize payment
    PaymentGateway-->>Frontend: Payment form
    Customer->>PaymentGateway: Enter card details
    PaymentGateway->>Bank: Process payment
    Bank-->>PaymentGateway: Payment result
    PaymentGateway-->>Frontend: Payment status
    Frontend->>Backend: POST /payment/confirm
    Backend->>Database: Update order (paid)
    Backend->>Backend: Send confirmation email
    Backend-->>Frontend: Success response
    Frontend-->>Customer: Show confirmation`
  },

  // Class Diagram Examples
  {
    id: 'oop-design-patterns',
    title: 'Design Patterns: Strategy & Observer',
    description: 'Implementation of common design patterns in object-oriented programming. Learn software design principles.',
    category: 'class',
    thumbnail: '🎯',
    type: 'mermaid',
    complexity: 'advanced',
    tags: ['class', 'oop', 'patterns', 'design'],
    mermaidCode: `classDiagram
    class PaymentStrategy {
        <<interface>>
        +processPayment(amount)
    }
    class CreditCardPayment {
        -cardNumber
        -cvv
        +processPayment(amount)
    }
    class PayPalPayment {
        -email
        +processPayment(amount)
    }
    class CryptoPayment {
        -walletAddress
        +processPayment(amount)
    }
    PaymentStrategy <|-- CreditCardPayment
    PaymentStrategy <|-- PayPalPayment
    PaymentStrategy <|-- CryptoPayment
    
    class Subject {
        -observers[]
        +attach(observer)
        +detach(observer)
        +notify()
    }
    class Observer {
        <<interface>>
        +update(data)
    }
    class EmailNotifier {
        +update(data)
    }
    class SMSNotifier {
        +update(data)
    }
    Subject o-- Observer
    Observer <|-- EmailNotifier
    Observer <|-- SMSNotifier`
  },

  // State Diagram Examples
  {
    id: 'order-state-machine',
    title: 'Order State Machine',
    description: 'State transitions for an order lifecycle from creation to delivery. Learn state management patterns.',
    category: 'state',
    thumbnail: '🔄',
    type: 'mermaid',
    complexity: 'intermediate',
    tags: ['state', 'fsm', 'order', 'lifecycle'],
    mermaidCode: `stateDiagram-v2
    [*] --> Created: Order Placed
    Created --> PaymentPending: Await Payment
    PaymentPending --> PaymentFailed: Payment Declined
    PaymentFailed --> Cancelled: Cancel Order
    PaymentPending --> Paid: Payment Successful
    Paid --> Processing: Start Processing
    Processing --> Shipped: Ship Order
    Shipped --> InTransit: Out for Delivery
    InTransit --> Delivered: Delivery Confirmed
    Delivered --> [*]
    
    Processing --> Cancelled: Cancel Request
    Shipped --> Returned: Return Initiated
    Returned --> Refunded: Refund Processed
    Refunded --> [*]
    Cancelled --> [*]`
  }
];

const CATEGORY_INFO = {
  architecture: {
    label: 'Architecture',
    icon: Network,
    color: 'blue',
    description: 'System architecture and infrastructure diagrams'
  },
  flowchart: {
    label: 'Flowchart',
    icon: GitBranch,
    color: 'green',
    description: 'Process flows and decision trees'
  },
  erd: {
    label: 'ERD',
    icon: Database,
    color: 'purple',
    description: 'Database schemas and entity relationships'
  },
  sequence: {
    label: 'Sequence',
    icon: Activity,
    color: 'orange',
    description: 'Interaction sequences and message flows'
  },
  class: {
    label: 'Class',
    icon: Box,
    color: 'pink',
    description: 'Object-oriented class structures'
  },
  state: {
    label: 'State',
    icon: Workflow,
    color: 'teal',
    description: 'State machines and transitions'
  }
};

interface ExampleDiagramsProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ExampleDiagrams({ isOpen, onClose }: ExampleDiagramsProps) {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [duplicating, setDuplicating] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleDuplicate = useCallback(async (example: ExampleDiagram) => {
    setDuplicating(example.id);

    try {
      // Get user ID from token
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const payload = JSON.parse(atob(token.split('.')[1]));
      const userId = payload.sub;

      // Create diagram from example
      const response = await fetch(API_ENDPOINTS.diagrams.create, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({
          title: `${example.title} (Copy)`,
          file_type: example.type === 'mermaid' ? 'note' : 'canvas',
          canvas_data: example.canvasData || null,
          note_content: example.mermaidCode || null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate diagram');
      }

      const diagram = await response.json();

      // Close modal and navigate to the new diagram
      onClose();
      
      if (example.type === 'mermaid') {
        router.push(`/mermaid/${diagram.id}`);
      } else {
        router.push(`/canvas/${diagram.id}`);
      }
    } catch (err) {
      console.error('Failed to duplicate diagram:', err);
      alert('Failed to duplicate diagram. Please try again.');
    } finally {
      setDuplicating(null);
    }
  }, [router, onClose]);

  const filteredExamples = EXAMPLE_DIAGRAMS.filter(example => {
    const matchesCategory = selectedCategory === 'all' || example.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      example.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      example.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      example.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="examples-title"
    >
      <div 
        className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div>
              <h2 id="examples-title" className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Example Diagrams
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Professional templates to help you get started
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition touch-target-small"
            aria-label="Close examples"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Search and Filters */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 space-y-4">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search examples by name, description, or tags..."
              className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Category Filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-4 py-2 rounded-lg font-medium transition touch-target-small ${
                selectedCategory === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              All ({EXAMPLE_DIAGRAMS.length})
            </button>
            {Object.entries(CATEGORY_INFO).map(([key, info]) => {
              const Icon = info.icon;
              const count = EXAMPLE_DIAGRAMS.filter(e => e.category === key).length;
              return (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key)}
                  className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 touch-target-small ${
                    selectedCategory === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {info.label} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {/* Examples Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredExamples.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">No examples found</p>
              <p className="text-gray-500 dark:text-gray-500 text-sm">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredExamples.map((example) => {
                const categoryInfo = CATEGORY_INFO[example.category];
                const CategoryIcon = categoryInfo.icon;
                const isDuplicating = duplicating === example.id;

                return (
                  <div
                    key={example.id}
                    className="bg-white dark:bg-gray-750 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition group"
                  >
                    {/* Thumbnail */}
                    <div className="h-40 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 flex items-center justify-center text-6xl">
                      {example.thumbnail}
                    </div>

                    {/* Content */}
                    <div className="p-4">
                      {/* Category Badge */}
                      <div className="flex items-center gap-2 mb-2">
                        <CategoryIcon className={`w-4 h-4 text-${categoryInfo.color}-600`} />
                        <span className={`text-xs font-medium text-${categoryInfo.color}-600 dark:text-${categoryInfo.color}-400`}>
                          {categoryInfo.label}
                        </span>
                        <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                          example.complexity === 'beginner' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                          example.complexity === 'intermediate' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                          'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {example.complexity}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-1">
                        {example.title}
                      </h3>

                      {/* Description */}
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                        {example.description}
                      </p>

                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mb-4">
                        {example.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                        {example.tags.length > 3 && (
                          <span className="text-xs px-2 py-0.5 text-gray-500 dark:text-gray-500">
                            +{example.tags.length - 3}
                          </span>
                        )}
                      </div>

                      {/* Action Button */}
                      <button
                        onClick={() => handleDuplicate(example)}
                        disabled={isDuplicating}
                        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-medium transition flex items-center justify-center gap-2 touch-target-medium"
                      >
                        {isDuplicating ? (
                          <>
                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Duplicating...
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Duplicate & Edit
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            💡 Tip: Click "Duplicate & Edit" to create your own editable copy of any example
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to manage example diagrams state
 */
export function useExampleDiagrams() {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}

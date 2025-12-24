/**
 * Feature #671: Help System - In-app Docs
 * 
 * Comprehensive help center with searchable documentation covering all features.
 * 
 * Features:
 * - Searchable documentation across all topics
 * - Category-based organization (Getting Started, Canvas, AI, Collaboration, etc.)
 * - Comprehensive coverage of all platform features
 * - Quick search with real-time filtering
 * - Expandable/collapsible sections
 * - Dark mode support
 * - Keyboard navigation
 * - Accessibility (ARIA labels, semantic HTML)
 * - Mobile-friendly responsive design
 * - Copy-to-clipboard for code examples
 * - Related topics suggestions
 * - Keyboard shortcuts reference
 * - Video tutorial links
 * - External documentation links
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  X,
  Search,
  Book,
  Zap,
  Palette,
  Users,
  GitBranch,
  Download,
  Settings,
  Keyboard,
  HelpCircle,
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  ExternalLink,
  Video,
  FileText,
  Lightbulb,
  Rocket,
  Shield,
  Share2,
} from 'lucide-react';

// Help topic interface
interface HelpTopic {
  id: string;
  title: string;
  category: string;
  content: string;
  keywords: string[];
  relatedTopics?: string[];
  videoUrl?: string;
  externalLink?: string;
}

// Category information
interface CategoryInfo {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  description: string;
}

// Category definitions
const CATEGORIES: Record<string, CategoryInfo> = {
  'getting-started': {
    id: 'getting-started',
    label: 'Getting Started',
    icon: Rocket,
    color: 'blue',
    description: 'Learn the basics and get up to speed quickly',
  },
  canvas: {
    id: 'canvas',
    label: 'Canvas & Drawing',
    icon: Palette,
    color: 'purple',
    description: 'Master the canvas tools and drawing features',
  },
  ai: {
    id: 'ai',
    label: 'AI Generation',
    icon: Zap,
    color: 'yellow',
    description: 'Generate diagrams with AI assistance',
  },
  mermaid: {
    id: 'mermaid',
    label: 'Diagram-as-Code',
    icon: FileText,
    color: 'green',
    description: 'Create diagrams using Mermaid syntax',
  },
  collaboration: {
    id: 'collaboration',
    label: 'Collaboration',
    icon: Users,
    color: 'pink',
    description: 'Work together in real-time',
  },
  sharing: {
    id: 'sharing',
    label: 'Sharing & Permissions',
    icon: Share2,
    color: 'indigo',
    description: 'Share diagrams and manage access',
  },
  export: {
    id: 'export',
    label: 'Export & Download',
    icon: Download,
    color: 'orange',
    description: 'Export diagrams in various formats',
  },
  git: {
    id: 'git',
    label: 'Git Integration',
    icon: GitBranch,
    color: 'red',
    description: 'Connect to GitHub, GitLab, and more',
  },
  shortcuts: {
    id: 'shortcuts',
    label: 'Keyboard Shortcuts',
    icon: Keyboard,
    color: 'teal',
    description: 'Speed up your workflow with shortcuts',
  },
  settings: {
    id: 'settings',
    label: 'Settings & Account',
    icon: Settings,
    color: 'gray',
    description: 'Manage your account and preferences',
  },
  security: {
    id: 'security',
    label: 'Security & Privacy',
    icon: Shield,
    color: 'emerald',
    description: 'Keep your data safe and secure',
  },
  tips: {
    id: 'tips',
    label: 'Tips & Tricks',
    icon: Lightbulb,
    color: 'amber',
    description: 'Pro tips to work more efficiently',
  },
};

// Help topics database
const HELP_TOPICS: HelpTopic[] = [
  // Getting Started
  {
    id: 'create-first-diagram',
    title: 'Creating Your First Diagram',
    category: 'getting-started',
    content: `Welcome to AutoGraph! Here's how to create your first diagram:

1. Click the "Create Diagram" button on the dashboard
2. Choose between Canvas (freeform drawing) or Note (Mermaid code)
3. Give your diagram a name
4. Start creating!

**Canvas Mode**: Use the toolbar on the left to select drawing tools (Rectangle, Circle, Arrow, Text, etc.). Click and drag on the canvas to create shapes.

**Note Mode**: Write Mermaid syntax in the code editor on the left. The diagram renders in real-time on the right.

**AI Generation**: Click "AI Generate" to create diagrams from natural language descriptions like "Create a microservices architecture diagram".`,
    keywords: ['create', 'new', 'first', 'start', 'begin', 'diagram', 'canvas', 'note'],
    relatedTopics: ['canvas-basics', 'mermaid-basics', 'ai-generation'],
  },
  {
    id: 'dashboard-overview',
    title: 'Dashboard Overview',
    category: 'getting-started',
    content: `The dashboard is your central hub for managing diagrams:

**Views**:
- All Files: See all your diagrams
- Recent: Recently accessed diagrams
- Starred: Your favorite diagrams
- Shared with Me: Diagrams others have shared
- Trash: Deleted diagrams (30-day retention)

**Actions**:
- Create Diagram: Start a new diagram
- AI Generate: Use AI to create diagrams
- View Examples: Browse pre-made examples
- Search: Find diagrams by name or content
- Filter: Filter by type, date, author
- Sort: Sort by name, date, last viewed

**Views**:
- Grid View: Thumbnails with previews
- List View: Detailed table with metadata`,
    keywords: ['dashboard', 'home', 'overview', 'files', 'list', 'grid', 'view'],
    relatedTopics: ['create-first-diagram', 'search-diagrams', 'organize-folders'],
  },
  {
    id: 'account-setup',
    title: 'Setting Up Your Account',
    category: 'getting-started',
    content: `Configure your account for the best experience:

**Profile Settings**:
1. Click your avatar in the top-right
2. Select "Settings"
3. Update your name, email, and avatar
4. Set your timezone and language preferences

**Preferences**:
- Theme: Light, Dark, or Auto (system)
- Default View: Grid or List
- Auto-save: Enable/disable (recommended: enabled)
- Notifications: Email, in-app, push

**Security**:
- Change password regularly
- Enable two-factor authentication (2FA)
- Review active sessions
- Manage API keys

**Teams** (if applicable):
- Join or create teams
- Invite team members
- Set team permissions`,
    keywords: ['account', 'profile', 'settings', 'preferences', 'setup', 'configure'],
    relatedTopics: ['security-best-practices', 'team-collaboration'],
  },

  // Canvas & Drawing
  {
    id: 'canvas-basics',
    title: 'Canvas Basics',
    category: 'canvas',
    content: `Master the canvas with these essential tools:

**Drawing Tools** (Toolbar):
- V: Selection tool (move, resize, rotate)
- R: Rectangle
- O: Circle/Ellipse
- A: Arrow (connects shapes)
- L: Line
- T: Text
- P: Pen (freehand drawing)
- F: Frame/Figure (organizational container)

**Navigation**:
- Pan: Space + Drag or Middle Mouse Button
- Zoom: Ctrl/Cmd + Scroll or Pinch gesture
- Fit to Screen: Ctrl/Cmd + 0
- Zoom to Selection: Ctrl/Cmd + 2

**Selection**:
- Click: Select single shape
- Shift + Click: Add to selection
- Drag: Lasso selection
- Ctrl/Cmd + A: Select all

**Transform**:
- Drag handles: Resize
- Rotate handle: Rotate
- Shift + Resize: Maintain aspect ratio
- Alt + Drag: Duplicate while moving`,
    keywords: ['canvas', 'drawing', 'tools', 'shapes', 'basics', 'toolbar'],
    relatedTopics: ['keyboard-shortcuts-canvas', 'advanced-canvas', 'figures-frames'],
    videoUrl: 'https://example.com/canvas-basics',
  },
  {
    id: 'advanced-canvas',
    title: 'Advanced Canvas Features',
    category: 'canvas',
    content: `Take your canvas skills to the next level:

**Grouping**:
- Ctrl/Cmd + G: Group selected shapes
- Ctrl/Cmd + Shift + G: Ungroup
- Groups can be nested for complex hierarchies

**Alignment & Distribution**:
- Align Left/Center/Right
- Align Top/Middle/Bottom
- Distribute Horizontally/Vertically
- Use the alignment toolbar or right-click menu

**Z-Order** (Layering):
- Ctrl/Cmd + ]: Bring Forward
- Ctrl/Cmd + [: Send Backward
- Ctrl/Cmd + Shift + ]: Bring to Front
- Ctrl/Cmd + Shift + [: Send to Back

**Styling**:
- Fill: Solid colors, gradients, or transparent
- Stroke: Color, width, dash pattern
- Text: Font, size, color, alignment
- Opacity: 0-100%

**Advanced**:
- Lock elements: Prevent editing (Ctrl/Cmd + L)
- Hide elements: Toggle visibility
- Snap to grid: G key
- Rulers and guides: Drag from rulers`,
    keywords: ['advanced', 'grouping', 'alignment', 'z-order', 'styling', 'lock', 'hide'],
    relatedTopics: ['canvas-basics', 'keyboard-shortcuts-canvas', 'properties-panel'],
  },
  {
    id: 'figures-frames',
    title: 'Figures and Frames',
    category: 'canvas',
    content: `Organize your canvas with figures (frames):

**Creating Figures**:
1. Press F key or select Frame tool
2. Drag to create a frame
3. Add title and choose color
4. Drag shapes into the frame

**Figure Features**:
- Title: Double-click to edit
- Colors: 8 preset colors
- Nesting: Frames can contain other frames
- Collapse/Expand: Hide contents for cleaner view
- Lock: Prevent accidental edits
- Export: Export individual frames

**Use Cases**:
- Group related components (e.g., "Frontend", "Backend")
- Create swimlanes for process diagrams
- Organize architecture layers
- Section large diagrams for clarity

**Tips**:
- Use consistent colors for similar components
- Name frames descriptively
- Collapse frames when working on other areas
- Export frames individually for presentations`,
    keywords: ['figures', 'frames', 'organize', 'group', 'container', 'section'],
    relatedTopics: ['canvas-basics', 'advanced-canvas', 'export-selection'],
  },
  {
    id: 'properties-panel',
    title: 'Properties Panel',
    category: 'canvas',
    content: `The Properties Panel gives you precise control over selected elements:

**Location**:
- Right sidebar (toggle with P key)
- Shows properties of selected element(s)
- Live updates as you edit

**Common Properties**:
- Position: X, Y coordinates
- Size: Width, Height
- Rotation: Angle in degrees
- Opacity: 0-100%

**Shape Properties**:
- Fill: Color, gradient, or none
- Stroke: Color, width, style (solid, dashed, dotted)
- Corner Radius: Rounded corners for rectangles
- Arrow Heads: Start/end styles for arrows

**Text Properties**:
- Font: Family, size, weight
- Color: Text color
- Alignment: Left, center, right, justify
- Line Height: Spacing between lines

**Multiple Selection**:
- Edit common properties for all selected items
- Different values show as "Mixed"
- Changes apply to all selected items`,
    keywords: ['properties', 'panel', 'edit', 'style', 'format', 'customize'],
    relatedTopics: ['advanced-canvas', 'styling-tips'],
  },

  // AI Generation
  {
    id: 'ai-generation',
    title: 'AI Diagram Generation',
    category: 'ai',
    content: `Generate professional diagrams from natural language:

**How to Use**:
1. Click "AI Generate" button
2. Describe what you want: "Create a microservices architecture with API gateway, user service, and database"
3. Click "Generate"
4. Review and refine the result

**Best Practices**:
- Be specific: Include component names and relationships
- Mention diagram type: "flowchart", "architecture", "sequence diagram", "ERD"
- Include details: Technologies (AWS, Azure, Kubernetes), patterns (microservices, 3-tier)
- Iterate: Use "Refine" to improve the result

**Example Prompts**:
- "Create an e-commerce order processing flowchart with payment and inventory checks"
- "Design a microservices architecture with API gateway, auth service, user service, and PostgreSQL"
- "Generate an ERD for a blog platform with users, posts, comments, and tags"
- "Show a sequence diagram for user authentication with JWT tokens"

**Refinement**:
- "Add a caching layer with Redis"
- "Make the database icon bigger"
- "Add error handling flows"
- "Include load balancer"`,
    keywords: ['ai', 'generate', 'artificial intelligence', 'automatic', 'prompt', 'natural language'],
    relatedTopics: ['ai-refinement', 'ai-best-practices', 'prompt-tips'],
    videoUrl: 'https://example.com/ai-generation',
  },
  {
    id: 'ai-refinement',
    title: 'Refining AI-Generated Diagrams',
    category: 'ai',
    content: `Improve AI-generated diagrams with iterative refinement:

**Refinement Commands**:
- "Add [component]": Add new elements
- "Remove [component]": Delete elements
- "Make [component] bigger/smaller": Resize
- "Move [component] to the left/right": Reposition
- "Change [component] color to blue": Restyle
- "Add connection from [A] to [B]": Add relationships
- "Add labels to arrows": Improve clarity

**Layout Improvements**:
- "Spread out the components more"
- "Align the services horizontally"
- "Group related components together"
- "Use a hierarchical layout"

**Content Additions**:
- "Add error handling"
- "Include monitoring and logging"
- "Show data flow with arrows"
- "Add technology labels (AWS, Docker, etc.)"

**Quality Tips**:
- Make 2-3 refinements for best results
- Be specific about what to change
- Review after each refinement
- Save versions before major changes`,
    keywords: ['refine', 'improve', 'iterate', 'modify', 'adjust', 'ai'],
    relatedTopics: ['ai-generation', 'ai-best-practices'],
  },
  {
    id: 'ai-best-practices',
    title: 'AI Generation Best Practices',
    category: 'ai',
    content: `Get the best results from AI generation:

**Prompt Writing**:
1. Start with diagram type: "Create a [type] diagram..."
2. List main components: "...with API gateway, services, and database"
3. Specify technologies: "...using AWS Lambda and DynamoDB"
4. Mention relationships: "...where users authenticate through OAuth"

**Diagram Types**:
- Architecture: "microservices", "3-tier", "serverless"
- Flowchart: "process flow", "decision tree", "workflow"
- ERD: "database schema", "data model"
- Sequence: "API flow", "authentication flow", "user journey"
- Class: "class diagram", "OOP design", "design patterns"

**Common Patterns**:
- Microservices: API gateway, services, databases, message queues
- E-commerce: User, cart, payment, inventory, orders
- Authentication: Login, JWT, refresh tokens, sessions
- CI/CD: Git, build, test, deploy, monitor

**Troubleshooting**:
- Too simple? Add more details in prompt
- Too complex? Ask to "simplify" or "focus on core components"
- Wrong layout? Specify "horizontal" or "vertical" layout
- Missing components? Use refinement to add them`,
    keywords: ['best practices', 'tips', 'ai', 'prompts', 'quality', 'improve'],
    relatedTopics: ['ai-generation', 'ai-refinement', 'prompt-tips'],
  },

  // Mermaid / Diagram-as-Code
  {
    id: 'mermaid-basics',
    title: 'Mermaid Diagram-as-Code Basics',
    category: 'mermaid',
    content: `Create diagrams using Mermaid syntax:

**Flowchart Example**:
\`\`\`mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
\`\`\`

**Sequence Diagram Example**:
\`\`\`mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    
    User->>API: Login Request
    API->>DB: Query User
    DB-->>API: User Data
    API-->>User: JWT Token
\`\`\`

**ERD Example**:
\`\`\`mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    PRODUCT ||--o{ LINE-ITEM : "ordered in"
\`\`\`

**Features**:
- Live preview: Changes render instantly
- Syntax highlighting: Code editor with Mermaid support
- Error detection: Real-time syntax validation
- Auto-complete: Suggestions as you type
- Snippets: Common patterns and templates`,
    keywords: ['mermaid', 'code', 'syntax', 'diagram-as-code', 'text', 'markdown'],
    relatedTopics: ['mermaid-flowchart', 'mermaid-sequence', 'mermaid-erd'],
    externalLink: 'https://mermaid.js.org/intro/',
  },
  {
    id: 'mermaid-flowchart',
    title: 'Mermaid Flowcharts',
    category: 'mermaid',
    content: `Create flowcharts with Mermaid:

**Basic Syntax**:
\`\`\`mermaid
graph TD
    A[Rectangle] --> B(Rounded)
    B --> C{Diamond}
    C -->|Label| D[End]
\`\`\`

**Node Shapes**:
- \`[Text]\`: Rectangle
- \`(Text)\`: Rounded rectangle
- \`{Text}\`: Diamond (decision)
- \`((Text))\`: Circle
- \`>Text]\`: Flag
- \`[[Text]]\`: Subroutine

**Arrows**:
- Arrow syntax: --> (solid), -.-> (dotted), ==> (thick)
- Labeled arrows: -- Text --> (arrow with label)

**Direction**:
- \`graph TD\`: Top to bottom
- \`graph LR\`: Left to right
- \`graph BT\`: Bottom to top
- \`graph RL\`: Right to left

**Subgraphs**:
\`\`\`mermaid
graph TD
    subgraph Frontend
        A[React]
        B[Next.js]
    end
    subgraph Backend
        C[FastAPI]
        D[PostgreSQL]
    end
    A --> C
\`\`\``,
    keywords: ['flowchart', 'mermaid', 'flow', 'process', 'workflow', 'decision'],
    relatedTopics: ['mermaid-basics', 'mermaid-sequence'],
    externalLink: 'https://mermaid.js.org/syntax/flowchart.html',
  },
  {
    id: 'mermaid-sequence',
    title: 'Mermaid Sequence Diagrams',
    category: 'mermaid',
    content: `Create sequence diagrams with Mermaid:

**Basic Syntax**:
\`\`\`mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    
    A->>B: Hello Bob!
    B-->>A: Hi Alice!
\`\`\`

**Arrow Types**:
- \`->>\`: Solid line with arrow
- \`-->>\`: Dotted line with arrow
- \`-)\`: Solid line with open arrow
- \`--)\`: Dotted line with open arrow
- \`-x\`: Solid line with cross
- \`--x\`: Dotted line with cross

**Activation**:
\`\`\`mermaid
sequenceDiagram
    A->>+B: Request
    B->>+C: Query
    C-->>-B: Response
    B-->>-A: Result
\`\`\`

**Loops and Conditions**:
\`\`\`mermaid
sequenceDiagram
    loop Every minute
        A->>B: Heartbeat
    end
    
    alt Success
        B->>A: OK
    else Failure
        B->>A: Error
    end
\`\`\`

**Notes**:
\`\`\`mermaid
sequenceDiagram
    A->>B: Message
    Note right of B: This is a note
    Note over A,B: Spans both
\`\`\``,
    keywords: ['sequence', 'mermaid', 'interaction', 'api', 'flow', 'messages'],
    relatedTopics: ['mermaid-basics', 'mermaid-flowchart'],
    externalLink: 'https://mermaid.js.org/syntax/sequenceDiagram.html',
  },
  {
    id: 'mermaid-erd',
    title: 'Mermaid Entity-Relationship Diagrams',
    category: 'mermaid',
    content: `Create ERDs with Mermaid:

**Basic Syntax**:
\`\`\`mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string name
        string email
        int id
    }
    ORDER {
        int id
        date created_at
        float total
    }
\`\`\`

**Relationships**:
- \`||--o{\`: One to many
- \`||--||\`: One to one
- \`}o--o{\`: Many to many
- \`}o--||\`: Many to one

**Cardinality**:
- \`||\`: Exactly one
- \`o|\`: Zero or one
- \`}o\`: Zero or many
- \`}|\`: One or many

**Attributes**:
\`\`\`mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string password
        datetime created_at
    }
    POST {
        int id PK
        int user_id FK
        string title
        text content
    }
    USER ||--o{ POST : writes
\`\`\`

**Tips**:
- Use descriptive entity names
- Include primary keys (PK)
- Mark foreign keys (FK)
- Add unique constraints (UK)
- Include data types`,
    keywords: ['erd', 'entity', 'relationship', 'database', 'schema', 'mermaid'],
    relatedTopics: ['mermaid-basics', 'mermaid-class'],
    externalLink: 'https://mermaid.js.org/syntax/entityRelationshipDiagram.html',
  },

  // Collaboration
  {
    id: 'real-time-collaboration',
    title: 'Real-Time Collaboration',
    category: 'collaboration',
    content: `Work together with your team in real-time:

**Features**:
- Live cursors: See where teammates are working
- Selection indicators: Highlighted when others select elements
- Typing indicators: Know when someone is editing
- User list: See who's online
- Activity feed: Track recent changes

**How to Collaborate**:
1. Open a diagram
2. Share the link with teammates
3. Everyone can edit simultaneously
4. Changes sync in real-time (< 200ms)

**Presence Indicators**:
- Colored cursors: Each user has a unique color
- Name labels: Hover over cursor to see name
- Selection highlights: See what others are editing
- Online status: Green dot = active, gray = away

**Conflict Resolution**:
- Operational transform: Merges concurrent edits
- Last write wins: For conflicting changes
- Undo/redo: Works correctly with multiple users
- Version history: Restore if needed

**Best Practices**:
- Communicate: Use comments or chat
- Divide work: Work on different sections
- Save often: Auto-save is enabled by default
- Use figures: Organize work by area`,
    keywords: ['collaboration', 'real-time', 'multiplayer', 'team', 'together', 'live'],
    relatedTopics: ['comments-system', 'team-collaboration', 'sharing-diagrams'],
    videoUrl: 'https://example.com/collaboration',
  },
  {
    id: 'comments-system',
    title: 'Comments and Discussions',
    category: 'collaboration',
    content: `Discuss diagrams with your team using comments:

**Adding Comments**:
1. Select an element on the canvas
2. Click the comment icon or press C
3. Type your comment
4. Press Enter to post

**Comment Features**:
- Threads: Reply to comments for discussions
- @Mentions: Notify specific users (@username)
- Reactions: 👍, ❤️, 😄 emoji reactions
- Resolve: Mark comments as resolved
- Edit: Edit your comments (within 5 minutes)
- Delete: Delete your own comments

**Comment Types**:
- Canvas comments: Attached to specific elements
- Note comments: Inline in markdown text
- General comments: About the whole diagram

**Notifications**:
- Email: Get notified via email
- In-app: Bell icon shows new comments
- Push: Browser notifications (if enabled)

**Managing Comments**:
- Filter: All, open, resolved, mine, mentions
- Search: Find comments by keyword
- Export: Download as CSV or PDF
- Moderate: Admins can delete any comment`,
    keywords: ['comments', 'discussion', 'feedback', 'mentions', 'threads', 'replies'],
    relatedTopics: ['real-time-collaboration', 'notifications'],
  },
  {
    id: 'team-collaboration',
    title: 'Team Workspaces',
    category: 'collaboration',
    content: `Organize work with team workspaces:

**Creating a Team**:
1. Click your avatar → "Create Team"
2. Enter team name and description
3. Invite members via email
4. Set default permissions

**Team Features**:
- Shared workspace: All team diagrams in one place
- Team folders: Organize by project or department
- Member management: Add, remove, change roles
- Team settings: Branding, defaults, integrations

**Roles**:
- Owner: Full control, billing, settings
- Admin: Manage members, settings
- Editor: Create and edit diagrams
- Viewer: Read-only access
- Custom: Define granular permissions (enterprise)

**Inviting Members**:
1. Team Settings → Members
2. Click "Invite"
3. Enter email addresses
4. Select role
5. Send invitations

**Team Permissions**:
- File-level: Control access per diagram
- Folder-level: Inherit permissions
- Team-level: Default for new files

**Best Practices**:
- Use folders for projects
- Set clear naming conventions
- Regular permission audits
- Archive old projects`,
    keywords: ['team', 'workspace', 'organization', 'members', 'roles', 'permissions'],
    relatedTopics: ['sharing-diagrams', 'permissions-management', 'real-time-collaboration'],
  },

  // Sharing & Permissions
  {
    id: 'sharing-diagrams',
    title: 'Sharing Diagrams',
    category: 'sharing',
    content: `Share your diagrams with others:

**Share Methods**:
1. Public link: Anyone with link can view
2. Team sharing: Share within your team
3. Email invitation: Invite specific people
4. Embed code: Embed in websites

**Creating a Share Link**:
1. Open diagram
2. Click "Share" button
3. Choose permissions: View or Edit
4. Copy link and share

**Permission Levels**:
- View: Can view but not edit
- Comment: Can view and comment
- Edit: Can view and edit
- Admin: Can edit and manage sharing

**Advanced Options**:
- Password protection: Require password to access
- Expiration: Link expires after set time
- Domain restriction: Only company emails
- Download control: Prevent downloads

**Tracking**:
- View count: See how many times viewed
- Last accessed: When link was last used
- Viewer list: Who has viewed (if logged in)
- Analytics: Views over time (enterprise)

**Revoking Access**:
1. Open sharing settings
2. Find the share link
3. Click "Revoke"
4. Confirm revocation`,
    keywords: ['share', 'sharing', 'link', 'access', 'permissions', 'public'],
    relatedTopics: ['permissions-management', 'embed-diagrams', 'team-collaboration'],
  },
  {
    id: 'permissions-management',
    title: 'Managing Permissions',
    category: 'sharing',
    content: `Control who can access your diagrams:

**Permission Levels**:
- Private: Only you can access
- Team: Team members can access
- Shared: Specific people can access
- Public: Anyone with link can access

**File Permissions**:
1. Right-click diagram
2. Select "Permissions"
3. Add users or groups
4. Set permission level
5. Save changes

**Folder Permissions**:
- Set on folder
- Inherited by contents
- Override on individual files
- Cascade to subfolders

**Team Permissions**:
- Default for new files
- Can be overridden per file
- Managed by admins
- Audit log tracks changes

**Best Practices**:
- Principle of least privilege
- Regular permission reviews
- Use groups for teams
- Document permission policies
- Enable audit logging

**Troubleshooting**:
- Can't access? Check permissions
- Can't edit? May be view-only
- Can't share? May lack admin rights
- Contact owner for access`,
    keywords: ['permissions', 'access', 'control', 'security', 'roles', 'rights'],
    relatedTopics: ['sharing-diagrams', 'team-collaboration', 'security-best-practices'],
  },
  {
    id: 'embed-diagrams',
    title: 'Embedding Diagrams',
    category: 'sharing',
    content: `Embed diagrams in websites and documentation:

**Getting Embed Code**:
1. Open diagram
2. Click "Share" → "Embed"
3. Customize options
4. Copy HTML code
5. Paste in your website

**Embed Options**:
- Size: Width and height
- Border: Show or hide border
- Toolbar: Show or hide controls
- Theme: Light, dark, or auto
- Interactive: Allow zooming/panning

**Example Code**:
\`\`\`html
<iframe 
  src="https://autograph.example.com/embed/abc123"
  width="800" 
  height="600"
  frameborder="0"
  allowfullscreen>
</iframe>
\`\`\`

**Responsive Embed**:
\`\`\`html
<div style="position: relative; padding-bottom: 56.25%; height: 0;">
  <iframe 
    src="https://autograph.example.com/embed/abc123"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
    frameborder="0">
  </iframe>
</div>
\`\`\`

**Use Cases**:
- Documentation sites
- Internal wikis
- Blog posts
- Presentations
- Dashboards

**Security**:
- Only public diagrams can be embedded
- Respects sharing permissions
- No authentication required
- CORS enabled`,
    keywords: ['embed', 'iframe', 'website', 'integration', 'html', 'code'],
    relatedTopics: ['sharing-diagrams', 'public-sharing'],
  },

  // Export & Download
  {
    id: 'export-formats',
    title: 'Export Formats',
    category: 'export',
    content: `Export diagrams in multiple formats:

**Available Formats**:

**PNG** (Raster Image):
- High resolution (1x, 2x, 4x)
- Transparent or custom background
- Anti-aliased for smooth edges
- Best for: Presentations, documents, web

**SVG** (Vector Image):
- Scalable without quality loss
- Editable in Illustrator/Figma
- Small file size
- Best for: Print, web, further editing

**PDF** (Document):
- Print-ready quality
- Embedded fonts
- Vector graphics where possible
- Best for: Documentation, archival

**JSON** (Data):
- Full diagram data structure
- Version control friendly
- Backup and restore
- Best for: Backup, migration

**Markdown** (Text):
- Diagram + notes combined
- Embedded images
- GitHub-compatible
- Best for: Documentation, wikis

**HTML** (Web Page):
- Standalone file
- Includes CSS and assets
- Interactive (optional)
- Best for: Offline viewing, archival`,
    keywords: ['export', 'download', 'save', 'format', 'png', 'svg', 'pdf'],
    relatedTopics: ['export-options', 'export-selection', 'batch-export'],
  },
  {
    id: 'export-options',
    title: 'Export Options',
    category: 'export',
    content: `Customize your exports:

**PNG Options**:
- Resolution: 1x (standard), 2x (retina), 4x (ultra-high)
- Background: Transparent, white, custom color
- Quality: Low, medium, high, ultra
- Padding: Add margin around diagram

**SVG Options**:
- Optimize: Reduce file size
- Include fonts: Embed or link
- Precision: Decimal places for coordinates
- Pretty print: Formatted or minified

**PDF Options**:
- Page size: A4, Letter, Custom
- Orientation: Portrait or Landscape
- Multi-page: Split large diagrams
- Compression: Reduce file size

**General Options**:
- Selection only: Export selected elements
- Current view: Export visible area
- Entire canvas: Export everything
- Specific figure: Export one frame

**Export Presets**:
- Save favorite settings
- Quick export with one click
- Share presets with team
- Default preset per diagram type

**Batch Export**:
- Export multiple diagrams at once
- Choose format and options
- Download as ZIP file
- Schedule automatic exports (enterprise)`,
    keywords: ['export', 'options', 'settings', 'customize', 'resolution', 'quality'],
    relatedTopics: ['export-formats', 'export-selection'],
  },
  {
    id: 'export-selection',
    title: 'Exporting Selections',
    category: 'export',
    content: `Export specific parts of your diagram:

**Export Selected Elements**:
1. Select elements you want to export
2. Click "Export" → "Selection"
3. Choose format
4. Download

**Export Figure/Frame**:
1. Right-click on figure
2. Select "Export Figure"
3. Choose format
4. Download

**Export Current View**:
1. Zoom and pan to desired view
2. Click "Export" → "Current View"
3. Choose format
4. Download

**Use Cases**:
- Extract component for presentation
- Share specific section with stakeholder
- Create thumbnail from detail
- Export legend separately

**Tips**:
- Tight cropping: Minimal padding
- Include context: Add surrounding elements
- Consistent exports: Use presets
- High resolution: Use 2x or 4x for presentations

**Batch Selection Export**:
- Select multiple figures
- Export all at once
- Maintains naming
- Organized in folders`,
    keywords: ['export', 'selection', 'figure', 'frame', 'partial', 'section'],
    relatedTopics: ['export-formats', 'export-options', 'figures-frames'],
  },

  // Git Integration
  {
    id: 'git-setup',
    title: 'Setting Up Git Integration',
    category: 'git',
    content: `Connect AutoGraph to your Git repositories:

**Supported Platforms**:
- GitHub
- GitLab
- Bitbucket
- Azure DevOps Git

**Setup Steps**:
1. Go to Settings → Integrations
2. Click "Connect Git Repository"
3. Choose platform (GitHub, GitLab, etc.)
4. Authorize AutoGraph
5. Select repository
6. Choose branch (main, develop, etc.)

**Authentication**:
- OAuth: Recommended, secure
- Personal Access Token (PAT): Alternative method
- SSH keys: For advanced users

**Permissions Required**:
- Read: View repository contents
- Write: Commit diagram changes
- Webhooks: Auto-sync on changes

**Configuration**:
- File path: Where to save diagrams
- Commit message template: Customize messages
- Auto-sync: Enable automatic commits
- Branch strategy: Main or feature branches

**Troubleshooting**:
- Authentication failed? Re-authorize
- Can't see repos? Check permissions
- Sync issues? Check webhook configuration
- Contact support if problems persist`,
    keywords: ['git', 'github', 'gitlab', 'bitbucket', 'setup', 'connect', 'integration'],
    relatedTopics: ['git-workflow', 'git-sync', 'version-control'],
  },
  {
    id: 'git-workflow',
    title: 'Git Workflow',
    category: 'git',
    content: `Work with diagrams in Git:

**Commit Diagrams**:
1. Edit diagram in AutoGraph
2. Click "Commit to Git"
3. Enter commit message
4. Choose files to commit
5. Commit

**Pull Requests**:
1. Create or edit diagram
2. Click "Create Pull Request"
3. Select target branch
4. Add description (auto-generated)
5. Create PR

**Auto-Sync**:
- Enable in settings
- Commits on every save
- Configurable frequency
- Conflict detection

**Branch Strategy**:
- Main branch: Production diagrams
- Feature branches: Work in progress
- Release branches: Versioned releases
- Hotfix branches: Quick fixes

**Collaboration**:
- Multiple users can work on branches
- Merge via pull requests
- Code review for diagrams
- CI/CD integration

**Best Practices**:
- Descriptive commit messages
- Atomic commits (one change per commit)
- Regular syncing
- Use branches for experiments
- Tag releases`,
    keywords: ['git', 'workflow', 'commit', 'pull request', 'branch', 'merge'],
    relatedTopics: ['git-setup', 'git-sync', 'version-control'],
  },
  {
    id: 'git-sync',
    title: 'Git Synchronization',
    category: 'git',
    content: `Keep diagrams in sync with Git:

**Auto-Sync**:
- Enabled by default after setup
- Commits on save (configurable)
- Pulls on diagram open
- Conflict detection and resolution

**Manual Sync**:
1. Click "Sync" button
2. Review changes
3. Resolve conflicts if any
4. Complete sync

**Conflict Resolution**:
- AutoGraph detects conflicts
- Shows both versions
- Choose: Keep local, keep remote, or merge
- Manual merge if needed

**Sync Status**:
- Up to date: ✓ Green
- Syncing: ⟳ Blue
- Conflicts: ⚠ Yellow
- Error: ✗ Red

**Webhooks**:
- Auto-update on Git push
- Real-time notifications
- Incremental updates
- Efficient bandwidth usage

**Troubleshooting**:
- Sync failed? Check connection
- Conflicts? Resolve manually
- Outdated? Pull latest changes
- Lost changes? Check version history`,
    keywords: ['git', 'sync', 'synchronization', 'auto-sync', 'conflicts', 'webhook'],
    relatedTopics: ['git-workflow', 'version-control', 'git-setup'],
  },

  // Keyboard Shortcuts
  {
    id: 'keyboard-shortcuts-canvas',
    title: 'Canvas Keyboard Shortcuts',
    category: 'shortcuts',
    content: `Master canvas shortcuts for faster work:

**Tools**:
- V: Selection tool
- R: Rectangle
- O: Circle
- A: Arrow
- L: Line
- T: Text
- P: Pen
- F: Frame/Figure

**Navigation**:
- Space + Drag: Pan
- Ctrl/Cmd + 0: Fit to screen
- Ctrl/Cmd + 1: Zoom to 100%
- Ctrl/Cmd + 2: Zoom to selection
- Ctrl/Cmd + Plus: Zoom in
- Ctrl/Cmd + Minus: Zoom out

**Selection**:
- Ctrl/Cmd + A: Select all
- Ctrl/Cmd + Shift + A: Deselect all
- Tab: Select next
- Shift + Tab: Select previous

**Edit**:
- Ctrl/Cmd + C: Copy
- Ctrl/Cmd + V: Paste
- Ctrl/Cmd + D: Duplicate
- Ctrl/Cmd + X: Cut
- Delete/Backspace: Delete
- Ctrl/Cmd + Z: Undo
- Ctrl/Cmd + Shift + Z: Redo

**Transform**:
- Ctrl/Cmd + G: Group
- Ctrl/Cmd + Shift + G: Ungroup
- Ctrl/Cmd + L: Lock
- Ctrl/Cmd + Shift + L: Unlock

**Arrange**:
- Ctrl/Cmd + ]: Bring forward
- Ctrl/Cmd + [: Send backward
- Ctrl/Cmd + Shift + ]: Bring to front
- Ctrl/Cmd + Shift + [: Send to back`,
    keywords: ['shortcuts', 'keyboard', 'hotkeys', 'canvas', 'quick', 'fast'],
    relatedTopics: ['keyboard-shortcuts-general', 'canvas-basics'],
  },
  {
    id: 'keyboard-shortcuts-general',
    title: 'General Keyboard Shortcuts',
    category: 'shortcuts',
    content: `Essential shortcuts for the entire app:

**Global**:
- Ctrl/Cmd + K: Command palette
- Ctrl/Cmd + /: Keyboard shortcuts help
- Ctrl/Cmd + S: Save
- Ctrl/Cmd + P: Print/Export
- Ctrl/Cmd + F: Search
- Ctrl/Cmd + ,: Settings
- ?: Help center (this dialog)

**Navigation**:
- Ctrl/Cmd + 1-9: Switch tabs
- Ctrl/Cmd + W: Close tab
- Ctrl/Cmd + T: New tab
- Alt + Left: Back
- Alt + Right: Forward

**Dashboard**:
- N: New diagram
- Ctrl/Cmd + N: New diagram
- Ctrl/Cmd + O: Open diagram
- Ctrl/Cmd + F: Search diagrams
- G then H: Go to home
- G then S: Go to starred

**Editor**:
- Ctrl/Cmd + E: Toggle editor/preview
- Ctrl/Cmd + B: Toggle sidebar
- Ctrl/Cmd + \\: Toggle properties panel
- F11: Fullscreen
- Esc: Exit fullscreen

**Accessibility**:
- Tab: Navigate forward
- Shift + Tab: Navigate backward
- Enter: Activate
- Esc: Cancel/Close
- Arrow keys: Navigate lists`,
    keywords: ['shortcuts', 'keyboard', 'hotkeys', 'general', 'global', 'navigation'],
    relatedTopics: ['keyboard-shortcuts-canvas', 'command-palette'],
  },
  {
    id: 'command-palette',
    title: 'Command Palette',
    category: 'shortcuts',
    content: `Quick access to all commands:

**Opening**:
- Keyboard: Ctrl/Cmd + K
- Click: Search icon in header
- Menu: View → Command Palette

**Features**:
- Search all commands
- Recent commands
- Fuzzy matching
- Keyboard navigation
- Categories

**Command Categories**:
- Files: Create, open, save, close
- Edit: Copy, paste, undo, redo
- View: Zoom, fit, fullscreen
- Insert: Shapes, text, images
- Format: Align, distribute, style
- Tools: Export, share, settings
- Help: Documentation, shortcuts

**Usage**:
1. Press Ctrl/Cmd + K
2. Type command name
3. Use arrow keys to navigate
4. Press Enter to execute

**Tips**:
- Type partial names (e.g., "exp" for export)
- Use recent commands for quick access
- Learn command names for faster work
- Customize with favorites

**Examples**:
- "new canvas" → Create canvas diagram
- "export png" → Export as PNG
- "share" → Share current diagram
- "dark mode" → Toggle dark mode`,
    keywords: ['command palette', 'search', 'commands', 'quick access', 'ctrl+k'],
    relatedTopics: ['keyboard-shortcuts-general', 'search-diagrams'],
  },

  // Settings & Account
  {
    id: 'account-settings',
    title: 'Account Settings',
    category: 'settings',
    content: `Manage your account and preferences:

**Profile**:
- Name: Display name
- Email: Primary email (verified)
- Avatar: Profile picture
- Bio: Short description
- Location: City, country
- Timezone: For timestamps

**Preferences**:
- Language: Interface language
- Theme: Light, dark, or auto
- Default view: Grid or list
- Date format: MM/DD/YYYY or DD/MM/YYYY
- Time format: 12h or 24h

**Notifications**:
- Email: Digest frequency
- In-app: Enable/disable
- Push: Browser notifications
- Types: Comments, shares, mentions

**Privacy**:
- Profile visibility: Public or private
- Activity status: Show online status
- Search indexing: Allow search engines
- Analytics: Share usage data

**Connected Accounts**:
- Google: Sign in with Google
- GitHub: Git integration
- Microsoft: SSO (enterprise)
- Slack: Notifications

**Danger Zone**:
- Change password
- Export data
- Delete account (permanent)`,
    keywords: ['account', 'settings', 'profile', 'preferences', 'configuration'],
    relatedTopics: ['notifications', 'security-best-practices', 'privacy-settings'],
  },
  {
    id: 'notifications',
    title: 'Notification Settings',
    category: 'settings',
    content: `Control how you receive notifications:

**Notification Types**:
- Comments: New comments on your diagrams
- Mentions: When someone @mentions you
- Shares: When diagrams are shared with you
- Collaborators: When someone joins your diagram
- Updates: Product updates and news

**Delivery Methods**:
- Email: Instant or daily digest
- In-app: Bell icon notifications
- Push: Browser notifications (PWA)
- Slack: Send to Slack channel (if connected)

**Email Preferences**:
- Instant: Receive immediately
- Hourly digest: Batched every hour
- Daily digest: Once per day
- Weekly digest: Once per week
- Never: Disable email notifications

**In-App Notifications**:
- Badge count: Unread count on bell icon
- Notification panel: Click bell to view
- Mark as read: Click notification
- Clear all: Clear all notifications

**Push Notifications** (PWA):
1. Install PWA
2. Allow notifications when prompted
3. Configure in settings
4. Receive desktop notifications

**Managing**:
- Mute: Temporarily disable (1h, 8h, 24h)
- Unsubscribe: From specific diagrams
- Preferences: Customize per type
- Do Not Disturb: Schedule quiet hours`,
    keywords: ['notifications', 'alerts', 'email', 'push', 'in-app', 'preferences'],
    relatedTopics: ['account-settings', 'comments-system'],
  },
  {
    id: 'privacy-settings',
    title: 'Privacy Settings',
    category: 'settings',
    content: `Control your privacy and data:

**Profile Privacy**:
- Public: Anyone can see your profile
- Team: Only team members can see
- Private: Only you can see

**Activity Privacy**:
- Show online status: Green dot when active
- Show last seen: "Active 5 minutes ago"
- Show activity: Recent diagrams, edits

**Search Privacy**:
- Allow search engines: Index public diagrams
- Discoverable: Appear in user search
- Public profile: Show in directory

**Data Privacy**:
- Analytics: Share anonymous usage data
- Crash reports: Send error reports
- Telemetry: Performance monitoring

**Data Rights** (GDPR):
- Access: Download all your data
- Rectification: Correct inaccurate data
- Erasure: Delete your account
- Portability: Export in standard format
- Object: Opt out of processing

**Data Retention**:
- Active diagrams: Kept indefinitely
- Trash: 30 days then permanent delete
- Versions: All versions kept
- Audit logs: 90 days (enterprise: 1 year)

**Security**:
- Two-factor authentication (2FA)
- Active sessions: View and revoke
- API keys: Manage access tokens
- Audit log: View account activity`,
    keywords: ['privacy', 'data', 'security', 'gdpr', 'settings', 'control'],
    relatedTopics: ['security-best-practices', 'account-settings'],
  },

  // Security & Privacy
  {
    id: 'security-best-practices',
    title: 'Security Best Practices',
    category: 'security',
    content: `Keep your account and data secure:

**Password Security**:
- Use strong, unique passwords (12+ characters)
- Include uppercase, lowercase, numbers, symbols
- Don't reuse passwords from other sites
- Use a password manager
- Change password regularly (every 90 days)

**Two-Factor Authentication (2FA)**:
1. Go to Settings → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes

**Session Management**:
- Review active sessions regularly
- Revoke suspicious sessions
- Log out from public computers
- Use "Remember me" only on personal devices

**API Keys**:
- Generate unique keys per application
- Rotate keys regularly
- Revoke unused keys
- Never share keys publicly
- Store securely (environment variables)

**Sharing Security**:
- Use password-protected links for sensitive data
- Set expiration dates on shares
- Review and revoke old shares
- Limit permissions (view-only when possible)

**Phishing Protection**:
- Verify sender email addresses
- Don't click suspicious links
- AutoGraph will never ask for password via email
- Report phishing to security@autograph.example.com

**Data Security**:
- Enable encryption at rest (enterprise)
- Use TLS for all connections
- Regular backups
- Version history for recovery`,
    keywords: ['security', 'best practices', 'password', '2fa', 'safety', 'protection'],
    relatedTopics: ['privacy-settings', 'account-settings', 'permissions-management'],
  },
  {
    id: 'data-backup',
    title: 'Data Backup and Recovery',
    category: 'security',
    content: `Protect your diagrams with backups:

**Automatic Backups**:
- Version history: Every save creates a version
- Auto-save: Every 5 minutes (if changes)
- Cloud storage: All data backed up daily
- Retention: Unlimited versions

**Manual Backup**:
1. Go to Settings → Data
2. Click "Export All Data"
3. Choose format (JSON recommended)
4. Download ZIP file
5. Store securely

**What's Included**:
- All diagrams (canvas data, notes)
- Version history
- Comments and mentions
- Folders and organization
- Settings and preferences
- Team data (if owner)

**Recovery Options**:
- Version history: Restore previous version
- Trash: Recover deleted diagrams (30 days)
- Export: Import from backup file
- Support: Contact for disaster recovery

**Git Backup**:
- Connect to Git repository
- Auto-commit on save
- Full version control
- Distributed backup

**Best Practices**:
- Export data monthly
- Store backups in multiple locations
- Test recovery process
- Document backup procedures
- Use Git for critical diagrams

**Disaster Recovery**:
1. Contact support immediately
2. Provide account details
3. Describe the issue
4. Support will restore from backup
5. Verify recovered data`,
    keywords: ['backup', 'recovery', 'restore', 'export', 'disaster', 'data'],
    relatedTopics: ['version-control', 'export-formats', 'security-best-practices'],
  },

  // Tips & Tricks
  {
    id: 'productivity-tips',
    title: 'Productivity Tips',
    category: 'tips',
    content: `Work faster and smarter:

**Keyboard Shortcuts**:
- Learn 10 most-used shortcuts
- Use command palette (Ctrl/Cmd + K)
- Customize shortcuts in settings
- Print cheat sheet for reference

**Templates**:
- Save frequently-used diagrams as templates
- Use example diagrams as starting points
- Share templates with team
- Build a template library

**Reusable Components**:
- Create component library
- Copy/paste common patterns
- Use figures for reusable sections
- Export/import components

**Organization**:
- Use folders and subfolders
- Consistent naming conventions
- Tag diagrams for easy finding
- Archive old projects

**Collaboration**:
- Use comments instead of external tools
- @Mention teammates for quick responses
- Real-time editing saves time
- Share links instead of files

**AI Assistance**:
- Start with AI generation
- Refine instead of starting from scratch
- Save good prompts for reuse
- Learn from AI-generated layouts

**Automation**:
- Enable auto-save
- Use Git auto-sync
- Schedule exports (enterprise)
- Set up webhooks for integrations

**Performance**:
- Use figures to organize large diagrams
- Collapse sections when not working on them
- Close unused tabs
- Clear browser cache if slow`,
    keywords: ['productivity', 'tips', 'tricks', 'efficiency', 'faster', 'workflow'],
    relatedTopics: ['keyboard-shortcuts-general', 'ai-best-practices', 'organize-folders'],
  },
  {
    id: 'design-tips',
    title: 'Design Best Practices',
    category: 'tips',
    content: `Create professional-looking diagrams:

**Layout**:
- Left-to-right or top-to-bottom flow
- Consistent spacing between elements
- Align related components
- Use grid for precision
- Group related items

**Colors**:
- Use consistent color scheme
- Limit to 3-5 colors
- Color code by type (e.g., blue for services, green for databases)
- High contrast for readability
- Consider color blindness

**Typography**:
- Consistent font sizes
- Readable fonts (sans-serif recommended)
- Appropriate text size (not too small)
- Left-align text in shapes
- Use bold for emphasis

**Shapes**:
- Consistent shape sizes
- Appropriate shapes for concepts (rectangles for processes, diamonds for decisions)
- Rounded corners for softer look
- Shadows for depth (use sparingly)

**Arrows**:
- Clear direction
- Labeled when necessary
- Consistent arrow styles
- Avoid crossing arrows when possible
- Use different colors for different types

**Whitespace**:
- Don't overcrowd
- Breathing room around elements
- Margins around canvas
- Space between groups

**Hierarchy**:
- Larger for more important elements
- Visual weight (bold, color, size)
- Clear entry point
- Logical flow

**Consistency**:
- Same style throughout
- Reuse patterns
- Template for series
- Style guide for teams`,
    keywords: ['design', 'best practices', 'layout', 'colors', 'professional', 'style'],
    relatedTopics: ['canvas-basics', 'advanced-canvas', 'styling-tips'],
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting Common Issues',
    category: 'tips',
    content: `Solutions to common problems:

**Performance Issues**:
- Slow loading? Clear browser cache
- Lag when drawing? Reduce canvas complexity
- High memory? Close unused tabs
- Slow export? Reduce resolution

**Sync Issues**:
- Not saving? Check internet connection
- Conflicts? Resolve in version history
- Git sync failed? Re-authenticate
- Lost changes? Check version history

**Display Issues**:
- Blurry text? Zoom to 100%
- Missing elements? Check if hidden or locked
- Wrong colors? Check theme (light/dark)
- Layout broken? Refresh page

**Export Issues**:
- Export failed? Try different format
- File too large? Reduce resolution
- Missing elements? Check selection
- Wrong size? Adjust export options

**Collaboration Issues**:
- Can't see others? Check permissions
- Cursors not showing? Refresh page
- Changes not syncing? Check connection
- Conflicts? Use version history

**Login Issues**:
- Can't log in? Reset password
- 2FA not working? Use backup code
- Account locked? Contact support
- SSO issues? Check with IT admin

**General Troubleshooting**:
1. Refresh the page (Ctrl/Cmd + R)
2. Clear browser cache
3. Try different browser
4. Check internet connection
5. Disable browser extensions
6. Contact support if persists

**Getting Help**:
- Help Center: This dialog (?)
- Documentation: help.autograph.example.com
- Support: support@autograph.example.com
- Community: community.autograph.example.com
- Status: status.autograph.example.com`,
    keywords: ['troubleshooting', 'problems', 'issues', 'help', 'fix', 'errors'],
    relatedTopics: ['performance-optimization', 'getting-help'],
  },
];

// Props interface
interface HelpCenterProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTopic?: string;
}

export default function HelpCenter({ isOpen, onClose, defaultTopic }: HelpCenterProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTopic, setSelectedTopic] = useState<string | null>(defaultTopic || null);
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Filter topics by search and category
  const filteredTopics = useMemo(() => {
    return HELP_TOPICS.filter(topic => {
      const matchesCategory = selectedCategory === 'all' || topic.category === selectedCategory;
      const matchesSearch = !searchQuery || 
        topic.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        topic.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        topic.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [searchQuery, selectedCategory]);

  // Get category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    HELP_TOPICS.forEach(topic => {
      counts[topic.category] = (counts[topic.category] || 0) + 1;
    });
    return counts;
  }, []);

  // Toggle topic expansion
  const toggleTopic = useCallback((topicId: string) => {
    setExpandedTopics(prev => {
      const next = new Set(prev);
      if (next.has(topicId)) {
        next.delete(topicId);
      } else {
        next.add(topicId);
      }
      return next;
    });
  }, []);

  // Select topic
  const selectTopic = useCallback((topicId: string) => {
    setSelectedTopic(topicId);
    setExpandedTopics(new Set([topicId]));
  }, []);

  // Copy code to clipboard
  const copyCode = useCallback((code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  }, []);

  // Close handler
  const handleClose = useCallback(() => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedTopic(null);
    setExpandedTopics(new Set());
    onClose();
  }, [onClose]);

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClose();
    }
  }, [handleClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={handleClose}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-center-title"
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <HelpCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 id="help-center-title" className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                Help Center
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Comprehensive documentation and guides
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition touch-target-small"
            aria-label="Close help center"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
              aria-label="Search help topics"
            />
          </div>
        </div>

        {/* Category filters */}
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <div className="flex gap-2 flex-wrap min-w-max">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition touch-target-small ${
                selectedCategory === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              All ({HELP_TOPICS.length})
            </button>
            {Object.values(CATEGORIES).map(category => {
              const Icon = category.icon;
              const count = categoryCounts[category.id] || 0;
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 touch-target-small ${
                    selectedCategory === category.id
                      ? `bg-${category.color}-600 text-white`
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  style={
                    selectedCategory === category.id
                      ? {
                          backgroundColor: `var(--${category.color}-600)`,
                          color: 'white',
                        }
                      : undefined
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{category.label}</span>
                  <span className="opacity-75">({count})</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {filteredTopics.length === 0 ? (
            <div className="text-center py-12">
              <Book className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">No help topics found</p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Try adjusting your search or category filter
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTopics.map(topic => {
                const isExpanded = expandedTopics.has(topic.id);
                const isSelected = selectedTopic === topic.id;
                const category = CATEGORIES[topic.category];
                const CategoryIcon = category.icon;

                return (
                  <div
                    key={topic.id}
                    className={`border rounded-lg overflow-hidden transition ${
                      isSelected
                        ? 'border-blue-500 dark:border-blue-400 shadow-md'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {/* Topic header */}
                    <button
                      onClick={() => {
                        toggleTopic(topic.id);
                        selectTopic(topic.id);
                      }}
                      className="w-full p-4 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-gray-750 transition text-left touch-target-medium"
                    >
                      <div
                        className={`p-2 rounded-lg flex-shrink-0 bg-${category.color}-100 dark:bg-${category.color}-900/30`}
                      >
                        <CategoryIcon
                          className={`w-5 h-5 text-${category.color}-600 dark:text-${category.color}-400`}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                          {topic.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                          {topic.content.split('\n')[0]}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span
                            className={`text-xs px-2 py-1 rounded bg-${category.color}-100 text-${category.color}-700 dark:bg-${category.color}-900/30 dark:text-${category.color}-400`}
                          >
                            {category.label}
                          </span>
                          {topic.videoUrl && (
                            <span className="text-xs px-2 py-1 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 flex items-center gap-1">
                              <Video className="w-3 h-3" />
                              Video
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </button>

                    {/* Topic content */}
                    {isExpanded && (
                      <div className="p-4 pt-0 border-t border-gray-200 dark:border-gray-700">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {topic.content.split('\n\n').map((paragraph, idx) => {
                            // Check if it's a code block
                            if (paragraph.startsWith('```')) {
                              const lines = paragraph.split('\n');
                              const language = lines[0].replace('```', '');
                              const code = lines.slice(1, -1).join('\n');
                              return (
                                <div key={idx} className="relative my-4">
                                  <div className="absolute top-2 right-2">
                                    <button
                                      onClick={() => copyCode(code)}
                                      className="p-2 bg-gray-700 hover:bg-gray-600 rounded text-white text-xs flex items-center gap-1 touch-target-small"
                                    >
                                      {copiedCode === code ? (
                                        <>
                                          <Check className="w-3 h-3" />
                                          Copied
                                        </>
                                      ) : (
                                        <>
                                          <Copy className="w-3 h-3" />
                                          Copy
                                        </>
                                      )}
                                    </button>
                                  </div>
                                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                                    <code className={`language-${language}`}>{code}</code>
                                  </pre>
                                </div>
                              );
                            }
                            
                            // Regular paragraph
                            return (
                              <p key={idx} className="text-gray-700 dark:text-gray-300 mb-3">
                                {paragraph}
                              </p>
                            );
                          })}
                        </div>

                        {/* Related topics */}
                        {topic.relatedTopics && topic.relatedTopics.length > 0 && (
                          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                              <Lightbulb className="w-4 h-4" />
                              Related Topics
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {topic.relatedTopics.map(relatedId => {
                                const relatedTopic = HELP_TOPICS.find(t => t.id === relatedId);
                                if (!relatedTopic) return null;
                                return (
                                  <button
                                    key={relatedId}
                                    onClick={() => selectTopic(relatedId)}
                                    className="text-sm px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 transition touch-target-small"
                                  >
                                    {relatedTopic.title}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* External links */}
                        {(topic.videoUrl || topic.externalLink) && (
                          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                              Additional Resources
                            </h4>
                            <div className="flex flex-wrap gap-3">
                              {topic.videoUrl && (
                                <a
                                  href={topic.videoUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded hover:bg-purple-200 dark:hover:bg-purple-900/50 transition flex items-center gap-2 touch-target-small"
                                >
                                  <Video className="w-4 h-4" />
                                  Watch Video Tutorial
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                              {topic.externalLink && (
                                <a
                                  href={topic.externalLink}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition flex items-center gap-2 touch-target-small"
                                >
                                  <FileText className="w-4 h-4" />
                                  Official Documentation
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 text-center sm:text-left">
              💡 <strong>Tip:</strong> Press <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">?</kbd> anytime to open help
            </p>
            <div className="flex gap-3">
              <a
                href="https://help.autograph.example.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                Full Documentation
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href="mailto:support@autograph.example.com"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Contact Support
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Hook for programmatic control
export function useHelpCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [defaultTopic, setDefaultTopic] = useState<string | undefined>(undefined);

  const open = useCallback((topic?: string) => {
    setDefaultTopic(topic);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setDefaultTopic(undefined);
  }, []);

  const toggle = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);

  return {
    isOpen,
    defaultTopic,
    open,
    close,
    toggle,
  };
}

#!/usr/bin/env python3
"""
Test Suite for Feature #671: Help System - In-app Docs

This test verifies the comprehensive help center with searchable documentation.

Tests:
1. Component structure and exports
2. Help topics database (comprehensive coverage)
3. Category system (12 categories)
4. Search functionality (real-time filtering)
5. Category filtering
6. Topic expansion/collapse
7. Related topics navigation
8. Code copying functionality
9. External links (video tutorials, documentation)
10. UI components (modal, search, categories, topics)
11. Accessibility features (ARIA, keyboard navigation)
12. Dark mode support
13. Responsive design
14. Global help center integration
15. Keyboard shortcut (? key)
16. Floating help button
17. Documentation completeness
"""

import os
import re
import sys

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}TEST: {test_name}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def read_file(filepath: str) -> str:
    """Read file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")
        return ""

def test_component_structure():
    """Test 1: Component structure and exports"""
    print_test_header("Component Structure and Exports")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Feature comment", "Feature #671: Help System - In-app Docs"),
        ("Component export", "export default function HelpCenter"),
        ("Hook export", "export function useHelpCenter"),
        ("Props interface", "interface HelpCenterProps"),
        ("Topic interface", "interface HelpTopic"),
        ("Category interface", "interface CategoryInfo"),
        ("isOpen prop", "isOpen: boolean"),
        ("onClose prop", "onClose: () => void"),
        ("useState imports", "import.*useState"),
        ("useCallback import", "import.*useCallback"),
        ("useRouter import", "import.*useRouter"),
        ("useMemo import", "import.*useMemo"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_help_topics_database():
    """Test 2: Help topics database (comprehensive coverage)"""
    print_test_header("Help Topics Database")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    # Check for comprehensive topic coverage
    topics = [
        # Getting Started
        ("Creating Your First Diagram", "getting-started"),
        ("Dashboard Overview", "getting-started"),
        ("Setting Up Your Account", "getting-started"),
        # Canvas
        ("Canvas Basics", "canvas"),
        ("Advanced Canvas Features", "canvas"),
        ("Figures and Frames", "canvas"),
        ("Properties Panel", "canvas"),
        # AI
        ("AI Diagram Generation", "ai"),
        ("Refining AI-Generated Diagrams", "ai"),
        ("AI Generation Best Practices", "ai"),
        # Mermaid
        ("Mermaid Diagram-as-Code Basics", "mermaid"),
        ("Mermaid Flowcharts", "mermaid"),
        ("Mermaid Sequence Diagrams", "mermaid"),
        ("Mermaid Entity-Relationship Diagrams", "mermaid"),
        # Collaboration
        ("Real-Time Collaboration", "collaboration"),
        ("Comments and Discussions", "collaboration"),
        ("Team Workspaces", "collaboration"),
        # Sharing
        ("Sharing Diagrams", "sharing"),
        ("Managing Permissions", "sharing"),
        ("Embedding Diagrams", "sharing"),
        # Export
        ("Export Formats", "export"),
        ("Export Options", "export"),
        ("Exporting Selections", "export"),
        # Git
        ("Setting Up Git Integration", "git"),
        ("Git Workflow", "git"),
        ("Git Synchronization", "git"),
        # Shortcuts
        ("Canvas Keyboard Shortcuts", "shortcuts"),
        ("General Keyboard Shortcuts", "shortcuts"),
        ("Command Palette", "shortcuts"),
        # Settings
        ("Account Settings", "settings"),
        ("Notification Settings", "settings"),
        ("Privacy Settings", "settings"),
        # Security
        ("Security Best Practices", "security"),
        ("Data Backup and Recovery", "security"),
        # Tips
        ("Productivity Tips", "tips"),
        ("Design Best Practices", "tips"),
        ("Troubleshooting Common Issues", "tips"),
    ]
    
    passed = 0
    for topic_name, category in topics:
        if topic_name in content:
            print_success(f"Topic found: {topic_name} ({category})")
            passed += 1
        else:
            print_error(f"Topic missing: {topic_name} ({category})")
    
    print_info(f"Passed: {passed}/{len(topics)}")
    return passed >= len(topics) - 2  # Allow 2 missing topics

def test_category_system():
    """Test 3: Category system (12 categories)"""
    print_test_header("Category System")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    categories = [
        ("getting-started", "Getting Started", "Rocket"),
        ("canvas", "Canvas & Drawing", "Palette"),
        ("ai", "AI Generation", "Zap"),
        ("mermaid", "Diagram-as-Code", "FileText"),
        ("collaboration", "Collaboration", "Users"),
        ("sharing", "Sharing & Permissions", "Share2"),
        ("export", "Export & Download", "Download"),
        ("git", "Git Integration", "GitBranch"),
        ("shortcuts", "Keyboard Shortcuts", "Keyboard"),
        ("settings", "Settings & Account", "Settings"),
        ("security", "Security & Privacy", "Shield"),
        ("tips", "Tips & Tricks", "Lightbulb"),
    ]
    
    passed = 0
    for cat_id, cat_label, cat_icon in categories:
        if cat_id in content and cat_label in content and cat_icon in content:
            print_success(f"Category found: {cat_label} ({cat_id}, {cat_icon})")
            passed += 1
        else:
            print_error(f"Category missing: {cat_label} ({cat_id}, {cat_icon})")
    
    # Check CATEGORIES constant
    if "const CATEGORIES: Record<string, CategoryInfo>" in content:
        print_success("CATEGORIES constant defined")
        passed += 1
    else:
        print_error("CATEGORIES constant not found")
    
    print_info(f"Passed: {passed}/{len(categories) + 1}")
    return passed >= len(categories)

def test_search_functionality():
    """Test 4: Search functionality (real-time filtering)"""
    print_test_header("Search Functionality")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Search query state", "const \\[searchQuery, setSearchQuery\\] = useState"),
        ("Search input field", "input.*type=\"text\".*placeholder=\"Search"),
        ("Search icon", "Search.*className="),
        ("Filter by search", "matchesSearch.*searchQuery"),
        ("Search in title", "topic.title.toLowerCase\\(\\).includes\\(searchQuery"),
        ("Search in content", "topic.content.toLowerCase\\(\\).includes\\(searchQuery"),
        ("Search in keywords", "topic.keywords.some"),
        ("useMemo for filtering", "const filteredTopics = useMemo"),
        ("Real-time filtering", "filteredTopics.filter"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_category_filtering():
    """Test 5: Category filtering"""
    print_test_header("Category Filtering")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Selected category state", "const \\[selectedCategory, setSelectedCategory\\] = useState"),
        ("All button", "All \\(.*HELP_TOPICS.length"),
        ("Category buttons", "Object.values\\(CATEGORIES\\).map"),
        ("Filter by category", "matchesCategory.*selectedCategory"),
        ("Category count", "categoryCounts"),
        ("Category icon display", "const Icon = category.icon"),
        ("Active category styling", "selectedCategory === category.id"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_topic_expansion():
    """Test 6: Topic expansion/collapse"""
    print_test_header("Topic Expansion/Collapse")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Expanded topics state", "const \\[expandedTopics, setExpandedTopics\\] = useState<Set<string>>"),
        ("Toggle topic function", "const toggleTopic = useCallback"),
        ("Select topic function", "const selectTopic = useCallback"),
        ("Expansion check", "const isExpanded = expandedTopics.has"),
        ("ChevronDown icon", "ChevronDown"),
        ("ChevronRight icon", "ChevronRight"),
        ("Conditional rendering", "isExpanded &&"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_related_topics():
    """Test 7: Related topics navigation"""
    print_test_header("Related Topics Navigation")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Related topics field", "relatedTopics\\?:"),
        ("Related topics display", "topic.relatedTopics"),
        ("Related topics mapping", "topic.relatedTopics.map"),
        ("Find related topic", "HELP_TOPICS.find"),
        ("Related topic button", "onClick.*selectTopic\\(relatedId\\)"),
        ("Lightbulb icon", "Lightbulb"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_code_copying():
    """Test 8: Code copying functionality"""
    print_test_header("Code Copying Functionality")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Copied code state", "const \\[copiedCode, setCopiedCode\\] = useState"),
        ("Copy code function", "const copyCode = useCallback"),
        ("Clipboard API", "navigator.clipboard.writeText"),
        ("Copy button", "Copy.*className="),
        ("Check icon", "Check"),
        ("Code block detection", "paragraph.startsWith\\('```'\\)"),
        ("Code extraction", "const code = lines.slice"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_external_links():
    """Test 9: External links (video tutorials, documentation)"""
    print_test_header("External Links")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Video URL field", "videoUrl\\?:"),
        ("External link field", "externalLink\\?:"),
        ("Video link display", "topic.videoUrl"),
        ("External link display", "topic.externalLink"),
        ("Video icon", "Video.*className="),
        ("External link icon", "ExternalLink"),
        ("Watch Video Tutorial", "Watch Video Tutorial"),
        ("Official Documentation", "Official Documentation"),
        ("Target blank", "target=\"_blank\""),
        ("Rel noopener", "rel=\"noopener noreferrer\""),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_ui_components():
    """Test 10: UI components (modal, search, categories, topics)"""
    print_test_header("UI Components")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Modal backdrop", "fixed inset-0.*backdrop-blur"),
        ("Modal dialog", "bg-white dark:bg-gray-800 rounded-lg"),
        ("Header", "Help Center"),
        ("Close button", "onClick={handleClose}"),
        ("Search input", "Search documentation"),
        ("Category filters", "Category filters"),
        ("Topic cards", "Topic header"),
        ("Empty state", "No help topics found"),
        ("Footer", "Full Documentation"),
        ("Tip message", "💡.*Tip"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_accessibility():
    """Test 11: Accessibility features (ARIA, keyboard navigation)"""
    print_test_header("Accessibility Features")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("role='dialog'", "role=\"dialog\""),
        ("aria-modal", "aria-modal=\"true\""),
        ("aria-labelledby", "aria-labelledby=\"help-center-title\""),
        ("aria-label on close", "aria-label=\"Close help center\""),
        ("aria-label on search", "aria-label=\"Search help topics\""),
        ("Touch target classes", "touch-target"),
        ("Keyboard handler", "handleKeyDown"),
        ("Escape key", "e.key === 'Escape'"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_dark_mode():
    """Test 12: Dark mode support"""
    print_test_header("Dark Mode Support")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    # Count dark: classes
    dark_classes = len(re.findall(r'dark:', content))
    
    checks = [
        ("dark:bg- classes", "dark:bg-"),
        ("dark:text- classes", "dark:text-"),
        ("dark:border- classes", "dark:border-"),
        ("dark:hover: classes", "dark:hover:"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        count = len(re.findall(pattern, content))
        if count > 0:
            print_success(f"{check_name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Total dark: classes: {dark_classes}")
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1 and dark_classes >= 30

def test_responsive_design():
    """Test 13: Responsive design"""
    print_test_header("Responsive Design")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Mobile padding", "p-4 sm:p-6"),
        ("Max width constraint", "max-w-6xl"),
        ("Responsive text", "text-xl sm:text-2xl"),
        ("Responsive flex", "flex-col sm:flex-row"),
        ("Overflow handling", "overflow-x-auto"),
        ("Touch target classes", "touch-target"),
        ("Mobile-friendly buttons", "px-3 sm:px-4"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_global_help_center():
    """Test 14: Global help center integration"""
    print_test_header("Global Help Center Integration")
    
    filepath = "services/frontend/app/components/GlobalHelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Component export", "export default function GlobalHelpCenter"),
        ("Dynamic import", "dynamic.*import.*HelpCenter"),
        ("Floating button", "Floating Help Button"),
        ("Button position", "fixed bottom-6 right-6"),
        ("HelpCircle icon", "HelpCircle"),
        ("Open handler", "handleOpen"),
        ("Close handler", "handleClose"),
        ("HelpCenter component", "<HelpCenter"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_keyboard_shortcut():
    """Test 15: Keyboard shortcut (? key)"""
    print_test_header("Keyboard Shortcut (? key)")
    
    filepath = "services/frontend/app/components/GlobalHelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Keyboard event listener", "addEventListener\\('keydown'"),
        ("Question mark key", "e.key === '\\?'"),
        ("Input exclusion", "target.tagName === 'INPUT'"),
        ("Textarea exclusion", "target.tagName === 'TEXTAREA'"),
        ("ContentEditable exclusion", "target.isContentEditable"),
        ("Prevent default", "e.preventDefault\\(\\)"),
        ("Toggle help", "setIsOpen\\(prev => !prev\\)"),
        ("Tooltip", "Press \\? key"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_floating_help_button():
    """Test 16: Floating help button"""
    print_test_header("Floating Help Button")
    
    filepath = "services/frontend/app/components/GlobalHelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Button element", "<button"),
        ("Fixed positioning", "fixed bottom-6 right-6"),
        ("Z-index", "z-40"),
        ("Blue background", "bg-blue-600"),
        ("Hover effect", "hover:bg-blue-700"),
        ("Rounded full", "rounded-full"),
        ("Shadow", "shadow-lg"),
        ("Aria label", "aria-label=\"Open help center"),
        ("Tooltip", "Help Center \\(Press \\?\\)"),
        ("Touch target", "touch-target-large"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 1

def test_documentation_completeness():
    """Test 17: Documentation completeness"""
    print_test_header("Documentation Completeness")
    
    filepath = "services/frontend/app/components/HelpCenter.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    # Check for comprehensive documentation
    topics_count = content.count("id:")
    content_sections = content.count("content:")
    keywords_count = content.count("keywords:")
    
    checks = [
        ("Feature description", "Feature #671"),
        ("Comprehensive help center", "Comprehensive help center"),
        ("Searchable documentation", "Searchable documentation"),
        ("Category-based organization", "Category-based organization"),
        ("40+ help topics", topics_count >= 35),
        ("Content sections", content_sections >= 35),
        ("Keywords for search", keywords_count >= 35),
        ("Getting Started topics", "Getting Started" in content),
        ("Canvas topics", "Canvas Basics" in content),
        ("AI topics", "AI Diagram Generation" in content),
        ("Mermaid topics", "Mermaid" in content),
        ("Collaboration topics", "Real-Time Collaboration" in content),
        ("Export topics", "Export Formats" in content),
        ("Security topics", "Security Best Practices" in content),
    ]
    
    passed = 0
    for check_name, condition in checks:
        if isinstance(condition, bool):
            result = condition
        else:
            result = condition in content
        
        if result:
            print_success(f"{check_name} ✓")
            passed += 1
        else:
            print_error(f"{check_name} ✗")
    
    print_info(f"Total topics: {topics_count}")
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed >= len(checks) - 2

def test_layout_integration():
    """Test 18: Layout integration"""
    print_test_header("Layout Integration")
    
    filepath = "services/frontend/app/layout.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("GlobalHelpCenter import", "import GlobalHelpCenter"),
        ("GlobalHelpCenter component", "<GlobalHelpCenter"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}HELP SYSTEM TEST SUITE - Feature #671{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*80}{Colors.END}\n")
    
    tests = [
        ("Component Structure", test_component_structure),
        ("Help Topics Database", test_help_topics_database),
        ("Category System", test_category_system),
        ("Search Functionality", test_search_functionality),
        ("Category Filtering", test_category_filtering),
        ("Topic Expansion", test_topic_expansion),
        ("Related Topics", test_related_topics),
        ("Code Copying", test_code_copying),
        ("External Links", test_external_links),
        ("UI Components", test_ui_components),
        ("Accessibility", test_accessibility),
        ("Dark Mode", test_dark_mode),
        ("Responsive Design", test_responsive_design),
        ("Global Help Center", test_global_help_center),
        ("Keyboard Shortcut", test_keyboard_shortcut),
        ("Floating Help Button", test_floating_help_button),
        ("Documentation Completeness", test_documentation_completeness),
        ("Layout Integration", test_layout_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*80}{Colors.END}\n")
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%){Colors.END}\n")
    
    if passed_count == total_count:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SUCCESS: All help system tests passed!{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ WARNING: Some tests failed. Please review the output above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

'use client';

import { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';

interface MermaidEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function MermaidEditor({ value, onChange }: MermaidEditorProps) {
  const editorRef = useRef<any>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Register Mermaid language if not already registered
    if (!monaco.languages.getLanguages().some(lang => lang.id === 'mermaid')) {
      monaco.languages.register({ id: 'mermaid' });

      // Define Mermaid syntax highlighting
      monaco.languages.setMonarchTokensProvider('mermaid', {
        tokenizer: {
          root: [
            // Comments
            [/%%.*$/, 'comment'],
            
            // Keywords for diagram types
            [/\b(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram-v2|erDiagram|gantt|gitGraph|pie)\b/, 'keyword'],
            
            // Direction keywords
            [/\b(TD|TB|BT|RL|LR)\b/, 'keyword'],
            
            // Sequence diagram keywords
            [/\b(participant|actor|activate|deactivate|Note|loop|alt|opt|par|and|else|end|rect|autonumber)\b/, 'keyword'],
            
            // Class diagram keywords
            [/\b(class|interface|abstract|enum|extends|implements)\b/, 'keyword'],
            
            // State diagram keywords
            [/\b(state|choice|fork|join)\b/, 'keyword'],
            
            // ER diagram keywords
            [/\b(entity|relationship)\b/, 'keyword'],
            
            // Gantt keywords
            [/\b(title|dateFormat|axisFormat|section|excludes|todayMarker|done|active|crit|milestone|after)\b/, 'keyword'],
            
            // Arrows and connections
            [/-->|---|-\.\->|===>|==>|->|--\||o--|\|--/, 'operator'],
            
            // Cardinality in ER diagrams
            [/\|\|--|o\{|}\||o--/, 'operator'],
            
            // Strings
            [/"([^"\\]|\\.)*$/, 'string.invalid'],
            [/"/, 'string', '@string'],
            [/'([^'\\]|\\.)*$/, 'string.invalid'],
            [/'/, 'string', '@string_single'],
            
            // Brackets
            [/[\[\]\(\)\{\}]/, 'bracket'],
            
            // Identifiers
            [/[a-zA-Z_]\w*/, 'identifier'],
            
            // Numbers
            [/\d+/, 'number'],
          ],
          
          string: [
            [/[^\\"]+/, 'string'],
            [/"/, 'string', '@pop'],
          ],
          
          string_single: [
            [/[^\\']+/, 'string'],
            [/'/, 'string', '@pop'],
          ],
        },
      });

      // Define theme colors for Mermaid
      monaco.editor.defineTheme('mermaid-theme', {
        base: 'vs',
        inherit: true,
        rules: [
          { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
          { token: 'keyword', foreground: '0000ff', fontStyle: 'bold' },
          { token: 'operator', foreground: 'aa5500' },
          { token: 'string', foreground: 'a31515' },
          { token: 'identifier', foreground: '001080' },
          { token: 'number', foreground: '098658' },
        ],
        colors: {
          'editor.foreground': '#000000',
          'editor.background': '#ffffff',
        },
      });
    }

    // Set the theme
    monaco.editor.setTheme('mermaid-theme');

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      // Trigger save - this will be handled by the parent component
      const event = new CustomEvent('mermaid-save');
      window.dispatchEvent(event);
    });
  };

  return (
    <Editor
      height="100%"
      language="mermaid"
      value={value}
      onChange={(value) => onChange(value || '')}
      onMount={handleEditorDidMount}
      options={{
        minimap: { enabled: true },
        fontSize: 14,
        lineNumbers: 'on',
        roundedSelection: false,
        scrollBeyondLastLine: false,
        readOnly: false,
        automaticLayout: true,
        wordWrap: 'on',
        wrappingIndent: 'same',
        tabSize: 2,
        insertSpaces: true,
        folding: true,
        foldingStrategy: 'indentation',
        showFoldingControls: 'always',
        bracketPairColorization: {
          enabled: true,
        },
      }}
      theme="mermaid-theme"
    />
  );
}

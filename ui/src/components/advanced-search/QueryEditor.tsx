import { useState, useEffect, useRef } from 'react';
import { Play, Pencil, X, Save, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SchemaPopover } from './SchemaPopover';
import { motion, AnimatePresence } from 'framer-motion';

interface QueryEditorProps {
  query: Record<string, unknown> | null;
  originalQuery: Record<string, unknown> | null;
  onResubmit: (query: Record<string, unknown>) => void;
  isLoading: boolean;
}

export function QueryEditor({ query, originalQuery, onResubmit, isLoading }: QueryEditorProps) {
  const [editedQuery, setEditedQuery] = useState('');
  const [parseError, setParseError] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [preEditSnapshot, setPreEditSnapshot] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (query) {
      const formatted = JSON.stringify(query, null, 2);
      setEditedQuery(formatted);
      setParseError('');
      setIsEditing(false);
      setIsExpanded(false);
    }
  }, [query]);

  const handleRun = () => {
    try {
      const parsed = JSON.parse(editedQuery);
      setParseError('');
      onResubmit(parsed);
    } catch {
      setParseError('Invalid JSON');
    }
  };

  const handleEditToggle = () => {
    setPreEditSnapshot(editedQuery);
    setIsEditing(true);
    setIsExpanded(true);
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const handleSaveAndRun = () => {
    try {
      const parsed = JSON.parse(editedQuery);
      setParseError('');
      setIsEditing(false);
      setIsExpanded(false);
      onResubmit(parsed);
    } catch {
      setParseError('Invalid JSON');
    }
  };

  const handleCancel = () => {
    setEditedQuery(preEditSnapshot);
    setParseError('');
    setIsEditing(false);
    setIsExpanded(false);
  };

  if (!query) return null;

  const lineCount = editedQuery.split('\n').length;
  const LINE_HEIGHT = 18;
  const collapsedHeight = 5 * LINE_HEIGHT + 16; // 5 lines + padding
  const expandedHeight = lineCount * LINE_HEIGHT + 16;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass-card rounded-2xl overflow-hidden border border-border/60 bg-card/80"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <button
            onClick={() => { if (!isEditing) setIsExpanded(v => !v); }}
            className="flex items-center gap-1.5 hover:text-primary transition-colors"
            disabled={isEditing}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
            <h3 className="text-sm font-semibold text-foreground">Generated Query</h3>
          </button>
          <SchemaPopover />
        </div>

        <div className="flex items-center gap-1.5">
          <AnimatePresence mode="wait">
            {isEditing ? (
              <motion.div
                key="edit-actions"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-1.5"
              >
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancel}
                  className="h-7 px-2.5 text-xs rounded-full"
                  disabled={isLoading}
                >
                  <X className="w-3 h-3 mr-1" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveAndRun}
                  className="h-7 px-3 text-xs rounded-full"
                  disabled={isLoading}
                >
                  <Save className="w-3 h-3 mr-1" />
                  Save & Run
                </Button>
              </motion.div>
            ) : (
              <motion.div
                key="view-actions"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-1.5"
              >
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleEditToggle}
                  className="h-7 px-2.5 text-xs rounded-full"
                  disabled={isLoading}
                >
                  <Pencil className="w-3 h-3 mr-1" />
                  Edit
                </Button>
                <Button
                  size="sm"
                  onClick={handleRun}
                  className="h-7 px-3 text-xs rounded-full"
                  disabled={isLoading}
                >
                  <Play className="w-3 h-3 mr-1" />
                  Run
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Query content */}
      <div className="relative">
        <motion.div
          animate={{
            height: isExpanded ? expandedHeight : collapsedHeight,
          }}
          transition={{ duration: 0.25, ease: 'easeInOut' }}
          className="overflow-hidden"
        >
          <textarea
            ref={textareaRef}
            value={editedQuery}
            onChange={(e) => {
              setEditedQuery(e.target.value);
              setParseError('');
            }}
            readOnly={!isEditing}
            className={`w-full p-2 px-4 bg-transparent font-mono text-xs text-foreground resize-none focus:outline-none transition-colors ${
              !isEditing ? 'cursor-default opacity-70' : ''
            }`}
            style={{
              lineHeight: `${LINE_HEIGHT}px`,
              height: `${expandedHeight}px`,
            }}
            spellCheck={false}
          />
        </motion.div>

        {/* Fade overlay when collapsed */}
        {!isExpanded && lineCount > 5 && (
          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background/80 to-transparent pointer-events-none rounded-b-2xl" />
        )}

        {parseError && (
          <div className="absolute bottom-2 left-4 text-xs text-destructive font-medium">
            {parseError}
          </div>
        )}
      </div>
    </motion.div>
  );
}

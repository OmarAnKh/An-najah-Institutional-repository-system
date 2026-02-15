import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { Button } from '@/components/ui/button';
import { ArrowUp, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const direction = detectLanguageDirection(input);

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading]);

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="mb-3">
      <div className="max-w-2xl mx-auto">
        <div className="relative flex items-center gap-2 glass-subtle rounded-full px-3 py-2 transition-all duration-200 focus-within:ring-2 focus-within:ring-primary/20 focus-within:shadow-md border border-border/60 bg-card/90">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            dir={direction}
            placeholder="Message..."
            disabled={isLoading}
            rows={1}
            className="flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 max-h-32 leading-relaxed"
            style={{ textAlign: direction === 'rtl' ? 'right' : 'left' }}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-9 w-9 rounded-full bg-primary hover:bg-primary/90 disabled:opacity-40 shrink-0 transition-all duration-200 shadow-sm"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

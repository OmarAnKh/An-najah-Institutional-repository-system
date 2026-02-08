import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchSuggestions } from '@/lib/api';

interface SearchInputProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function SearchInput({ onSearch, isLoading }: SearchInputProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const direction = detectLanguageDirection(query);

  useEffect(() => {
    const doFetch = async () => {
      if (query.length < 3) {
        setSuggestions([]);
        return;
      }

      try {
        const results = await fetchSuggestions(query);
        setSuggestions(results.slice(0, 5));
      } catch {
        // Fallback demo suggestions
        setSuggestions([
          `${query} in machine learning`,
          `${query} research methodology`,
          `${query} case study analysis`,
        ]);
      }
    };

    const timer = setTimeout(doFetch, 200);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSubmit = (value?: string) => {
    const searchQuery = value || query;
    if (searchQuery.trim()) {
      const normalized = searchQuery.trim();
      setQuery(normalized);
      onSearch(normalized);
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        handleSubmit(suggestions[selectedIndex]);
      } else {
        handleSubmit();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="relative">
      <div className="relative glass-subtle rounded-full border border-border/70 bg-secondary/50">
        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-muted-foreground">
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Search className="w-5 h-5" />
          )}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowSuggestions(true);
            setSelectedIndex(-1);
          }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          onKeyDown={handleKeyDown}
          dir={direction}
          placeholder="Search the repository..."
          className="w-full h-12 pl-13 pr-5 rounded-full text-foreground placeholder:text-muted-foreground bg-transparent focus:outline-none focus:ring-2 focus:ring-primary/20 focus:shadow-md transition-all duration-200"
          style={{ textAlign: direction === 'rtl' ? 'right' : 'left', paddingLeft: '3.25rem' }}
        />
      </div>

      {/* Suggestions Dropdown */}
      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 right-0 mt-2 glass-subtle rounded-2xl overflow-hidden z-50 shadow-lg"
          >
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className={`w-full px-5 py-3 text-left text-sm transition-colors ${
                  index === selectedIndex
                    ? 'bg-primary/15 text-foreground'
                    : 'text-foreground/80 hover:bg-secondary/70 hover:text-foreground'
                }`}
                onMouseDown={() => handleSubmit(suggestion)}
              >
                <div className="flex items-center gap-2.5">
                  <Search className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  {suggestion}
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

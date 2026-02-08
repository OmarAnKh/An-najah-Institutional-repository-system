import { SearchResult } from '@/types/chat';
import { FileText, ArrowUpRight, Search } from 'lucide-react';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { HighlightedText } from './HighlightedText';
import { motion } from 'framer-motion';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading: boolean;
}

export function SearchResults({ results, query, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="mt-8 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card rounded-2xl p-5 animate-pulse">
            <div className="h-4 bg-secondary rounded-full w-3/4 mb-3" />
            <div className="h-3 bg-secondary rounded-full w-full mb-2" />
            <div className="h-3 bg-secondary rounded-full w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (!query) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mt-20 text-center"
      >
        <div className="w-14 h-14 rounded-2xl glass-card flex items-center justify-center mx-auto mb-4 shadow-sm">
          <Search className="w-6 h-6 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-1">
          Search the repository
        </h3>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">
          Find research papers, theses, and academic publications
        </p>
      </motion.div>
    );
  }

  if (results.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mt-20 text-center"
      >
        <div className="w-14 h-14 rounded-2xl glass-card flex items-center justify-center mx-auto mb-4 shadow-sm">
          <FileText className="w-6 h-6 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-1">No results</h3>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">Try different keywords</p>
      </motion.div>
    );
  }

  return (
    <div className="mt-8">
      <p className="text-sm text-muted-foreground mb-4">
        {results.length} results
      </p>
      <div className="space-y-2">
        {results.map((result, index) => {
          const direction = detectLanguageDirection(result.title);
          
          return (
            <motion.a
              key={result.id}
              href={`https://repository.najah.edu/items/${result.id}`}
              target="_blank"
              rel="noopener noreferrer"
              dir={direction}
              className="group block p-4 rounded-2xl glass-card border border-border/60 bg-card/80 hover:bg-card/95 hover:border-primary/40 hover:shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all duration-200"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04, duration: 0.3 }}
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <h4 className="text-foreground font-medium group-hover:text-primary transition-colors line-clamp-2 mb-1">
                    <HighlightedText text={result.title} query={query} />
                  </h4>
                  {result.snippet && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                      <HighlightedText text={result.snippet} query={query} />
                    </p>
                  )}
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {result.type && (
                      <span className="px-2.5 py-0.5 rounded-full glass-input capitalize text-xs font-medium">
                        {result.type}
                      </span>
                    )}
                    {result.year && <span>{result.year}</span>}
                    {result.author && (
                      <span>
                        <HighlightedText text={result.author} query={query} />
                      </span>
                    )}
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all duration-200 shrink-0 mt-1" />
              </div>
            </motion.a>
          );
        })}
      </div>
    </div>
  );
}

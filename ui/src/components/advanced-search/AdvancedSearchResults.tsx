import { ArrowUpRight, FileText, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { motion } from 'framer-motion';

export interface AdvancedResult {
  id: string;
  item_uuid?: string;
  title: string;
  abstract?: string;
  authors: string[];
  publicationDate?: string;
  collection?: string;
  hasFiles?: boolean;
  type?: string;
}

interface AdvancedSearchResultsProps {
  results: AdvancedResult[];
  isLoading: boolean;
  hasSearched: boolean;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function AdvancedSearchResults({ results, isLoading, hasSearched, page, pageSize, onPageChange }: AdvancedSearchResultsProps) {
  if (isLoading) {
    return (
      <div className="space-y-3 mt-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card rounded-2xl p-5 animate-pulse">
            <div className="h-4 bg-secondary rounded-full w-3/4 mb-3" />
            <div className="h-3 bg-secondary rounded-full w-full mb-2" />
            <div className="h-3 bg-secondary rounded-full w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!hasSearched) return null;

  if (results.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mt-12 text-center"
      >
        <div className="w-14 h-14 rounded-2xl glass-card flex items-center justify-center mx-auto mb-4 shadow-sm">
          <Search className="w-6 h-6 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-1">No results</h3>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">Try refining your query.</p>
      </motion.div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(results.length / pageSize));
  const currentPage = Math.min(Math.max(page, 1), totalPages);
  const start = (currentPage - 1) * pageSize;
  const currentSlice = results.slice(start, start + pageSize);

  const goToPage = (next: number) => {
    const clamped = Math.min(Math.max(next, 1), totalPages);
    onPageChange(clamped);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="mt-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">
          Documents
        </h3>
        <span className="text-xs text-muted-foreground">
          {results.length} results
        </span>
      </div>
      <div className="space-y-2">
        {currentSlice.map((result, index) => {
          const direction = detectLanguageDirection(result.title);
          return (
            <motion.a
              key={result.id}
              href={`https://repository.najah.edu/items/${result.item_uuid || result.id}`}
              target="_blank"
              rel="noopener noreferrer"
              dir={direction}
              className="group block p-4 rounded-2xl glass-card border border-border/60 bg-card/80 hover:bg-card/95 hover:border-primary/40 hover:shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all duration-200"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03, duration: 0.25 }}
            >
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl glass-subtle flex items-center justify-center shrink-0 mt-0.5">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-foreground font-medium group-hover:text-primary transition-colors line-clamp-2 mb-1">
                    {result.title}
                  </h4>
                  {result.abstract && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                      {result.abstract}
                    </p>
                  )}
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {result.authors.length > 0 && (
                      <span>{result.authors.join(', ')}</span>
                    )}
                    {result.publicationDate && (
                      <span>· {result.publicationDate}</span>
                    )}
                    {result.collection && (
                      <span className="px-2 py-0.5 rounded-full glass-input capitalize text-xs font-medium">
                        {result.collection}
                      </span>
                    )}
                    {result.hasFiles && (
                      <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
                        Has files
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

      <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
        <span>
          Showing {start + 1}-{Math.min(start + pageSize, results.length)} of {results.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded-full glass-subtle border border-border/50 disabled:opacity-50 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-4 h-4" /> Prev
          </button>
          <span className="px-3 py-1.5 rounded-full glass-input border border-border/50">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-3 py-1.5 rounded-full glass-subtle border border-border/50 disabled:opacity-50 disabled:pointer-events-none"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

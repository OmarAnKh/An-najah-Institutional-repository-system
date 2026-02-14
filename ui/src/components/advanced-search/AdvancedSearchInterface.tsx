import { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { executeAdvancedQuery, generateAdvancedQuery } from '@/lib/api';
import { QueryEditor } from './QueryEditor';
import { AdvancedSearchResults, AdvancedResult } from './AdvancedSearchResults';

type LocalizedField = { en?: string; ar?: string } | string | undefined;

type OpenSearchHitSource = {
  title?: LocalizedField;
  abstract?: LocalizedField;
  author?: unknown;
  publicationDate?: string;
  collection?: string;
  hasFiles?: boolean;
  type?: string;
  item_uuid?: string;
};

type OpenSearchHit = {
  _id?: string;
  _source?: OpenSearchHitSource;
};

export function AdvancedSearchInterface() {
  const [query, setQuery] = useState('');
  const [generatedQuery, setGeneratedQuery] = useState<Record<string, unknown> | null>(null);
  const [originalQuery, setOriginalQuery] = useState<Record<string, unknown> | null>(null);
  const [results, setResults] = useState<AdvancedResult[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [page, setPage] = useState(1);

  const PAGE_SIZE = 10;

  const direction = detectLanguageDirection(query);

  const parseHits = (data: Record<string, unknown>): AdvancedResult[] => {
    const hitsRoot = (data as { hits?: { hits?: unknown[] } })?.hits?.hits;
    const hits: OpenSearchHit[] = Array.isArray(hitsRoot) ? hitsRoot : [];

    const asText = (field: LocalizedField): string => {
      if (typeof field === 'string') return field;
      if (field && typeof field === 'object') return field.en || field.ar || '';
      return '';
    };

    return hits.map((hit) => {
      const src = hit._source || {};
      const title = asText(src.title) || 'Untitled';
      const abstract = asText(src.abstract);
      const authors = Array.isArray(src.author)
        ? src.author.filter((a): a is string => typeof a === 'string')
        : [];

      const itemId = src.item_uuid || hit._id || crypto.randomUUID();

      return {
        id: itemId,
        item_uuid: src.item_uuid,
        title,
        abstract,
        authors,
        publicationDate: src.publicationDate || '',
        collection: src.collection || '',
        hasFiles: Boolean(src.hasFiles),
        type: src.type || '',
      };
    });
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setIsGenerating(true);
    setResults([]);
    setPage(1);
    setHasSearched(false);

    try {
      const enforcedPrompt = `${query.trim()}\n\nConstraint: If a document has multiple chunks, return only one chunk per document.`;
      const data = await generateAdvancedQuery(enforcedPrompt);
      const gq = data.dsl as Record<string, unknown>;
      setGeneratedQuery(gq);
      setOriginalQuery(gq);

      // Auto-run search with generated query
      setIsSearching(true);
      try {
        const searchData = await executeAdvancedQuery(gq);
        setResults(parseHits(searchData.results));
        setHasSearched(true);
      } catch {
        setResults([]);
        setHasSearched(true);
      } finally {
        setIsSearching(false);
      }
    } catch {
      setGeneratedQuery(null);
      setOriginalQuery(null);
      setHasSearched(true);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleResubmit = async (editedQuery: Record<string, unknown>) => {
    setIsSearching(true);
    setPage(1);
    setHasSearched(false);
    try {
      const searchData = await executeAdvancedQuery(editedQuery);
      setResults(parseHits(searchData.results));
      setHasSearched(true);
    } catch {
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center mb-10"
        >
          <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-3xl font-semibold text-foreground mb-2 tracking-tight">
            Advanced Search
          </h1>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            Describe what you need in your own words. We’ll understand your request, run an advanced search, and return the most relevant results.
          </p>
        </motion.div>

        {/* Big search input */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mb-8"
        >
          <div className="glass-subtle rounded-2xl border border-border/70 bg-secondary/50 overflow-hidden focus-within:ring-2 focus-within:ring-primary/20 focus-within:shadow-lg transition-all duration-200">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              dir={direction}
              placeholder="e.g. Find all theses about machine learning published after 2020 by authors from the engineering department..."
              className="w-full min-h-[120px] p-5 bg-transparent text-foreground placeholder:text-muted-foreground resize-none focus:outline-none text-[15px] leading-relaxed"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
            />
            <div className="flex items-center justify-between px-4 py-3 border-t border-border/30">
              <span className="text-xs text-muted-foreground">
                Enter to search · Shift+Enter for new line
              </span>
              <button
                onClick={handleSubmit}
                disabled={isGenerating || !query.trim()}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none transition-colors"
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Generate & Search
              </button>
            </div>
          </div>
        </motion.div>

        {/* Generated Query Editor */}
        <QueryEditor
          query={generatedQuery}
          originalQuery={originalQuery}
          onResubmit={handleResubmit}
          isLoading={isSearching}
        />

        {/* Search Results */}
        <AdvancedSearchResults
          results={results}
          isLoading={isSearching}
          hasSearched={hasSearched}
          page={page}
          pageSize={PAGE_SIZE}
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}

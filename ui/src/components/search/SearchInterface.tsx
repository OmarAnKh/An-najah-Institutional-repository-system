import { useState } from 'react';
import { SearchInput } from './SearchInput';
import { SearchResults } from './SearchResults';
import { SearchResult } from '@/types/chat';
import { motion } from 'framer-motion';
import { generateQuery, searchDocuments } from '@/lib/api';

export function SearchInterface() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const hasQuery = currentQuery.trim().length > 0;

  const handleSearch = async (query: string) => {
    setCurrentQuery(query);
    setIsLoading(true);

    try {
      // Primary: use backend query generation (same pipeline as backend Swagger search)
      const generated = await generateQuery(query);
      let hits = (generated.results as any)?.hits?.hits || [];

      // Fallback: use new full-text hybrid search if generation returns nothing
      if (!hits.length) {
        const fallbackRes = await import('@/lib/api').then(m => m.searchFullText(query));
        hits = (fallbackRes.results as any)?.hits?.hits || [];
      }

      // Map hits to UI-friendly shape
      const parsed: SearchResult[] = hits.map((hit: any) => {
        const source = hit._source || {};
        const titleObj = source.title || {};
        const title =
          (typeof titleObj === 'object'
            ? titleObj.en || titleObj.ar
            : titleObj) || source.dc_title || 'Untitled';

        const abstract =
          source.abstract || source.description || source.dc_description || source.snippet || '';
        const snippet =
          typeof abstract === 'object'
            ? abstract.en || abstract.ar || ''
            : abstract;

        const authorField = source.author || source.dc_creator;
        const author = Array.isArray(authorField) ? authorField.join(', ') : authorField;

        return {
          id: source.item_uuid || hit._id || source.id || crypto.randomUUID(),
          title,
          snippet,
          score: hit._score,
          author,
          year: (source.year || source.dc_date)?.toString(),
          type: source.type || source.dc_type,
        };
      });

      setResults(parsed);
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div
        className={`max-w-2xl mx-auto px-4 py-12 ${hasQuery || isLoading ? '' : 'flex flex-col justify-center min-h-[70vh]'
          }`}
      >
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center mb-10"
        >
          <h1 className="text-3xl font-semibold text-foreground mb-2 tracking-tight">
            Search
          </h1>
          <p className="text-muted-foreground">
            Explore the institutional repository
          </p>
        </motion.div>

        <SearchInput onSearch={handleSearch} isLoading={isLoading} />
        {(hasQuery || isLoading) && (
          <SearchResults results={results} query={currentQuery} isLoading={isLoading} />
        )}
      </div>
    </div>
  );
}

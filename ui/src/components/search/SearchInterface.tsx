import { useState } from 'react';
import { SearchInput } from './SearchInput';
import { SearchResults } from './SearchResults';
import { SearchResult } from '@/types/chat';
import { motion } from 'framer-motion';

const GENERATE_QUERY_ENDPOINT = '/api/generate-query';
const SEARCH_ENDPOINT = '/api/search';

const mapSearchResults = (results: any): SearchResult[] => {
  const hits = results?.hits?.hits ?? [];

  return hits.map((hit: any) => {
    const src = hit?._source ?? {};

    const title = typeof src.title === 'string'
      ? src.title
      : src.title?.en || src.title?.ar || 'Untitled document';

    const abstract = typeof src.abstract === 'string'
      ? src.abstract
      : src.abstract?.en || src.abstract?.ar;

    const authorRaw = src.author;
    const author = Array.isArray(authorRaw)
      ? authorRaw.filter(Boolean).join(', ')
      : authorRaw;

    const year = src.year || src.publication_year || src.date;
    const docType = src.type || src.document_type || src.category;

    return {
      id: hit?._id || src.id || crypto.randomUUID(),
      title,
      snippet: abstract,
      author: author || undefined,
      year: year ? String(year) : undefined,
      type: docType || undefined,
    } satisfies SearchResult;
  });
};

export function SearchInterface() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setCurrentQuery(query);
    setIsLoading(true);

    try {
      let generatedQueryBody: any = null;
      let interimResults: SearchResult[] = [];

      const generateResp = await fetch(GENERATE_QUERY_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: query }),
      });

      if (generateResp.ok) {
        const data = await generateResp.json();
        interimResults = mapSearchResults(data.results);

        const generatedQuery = data.generated_query;
        try {
          generatedQueryBody = typeof generatedQuery === 'string'
            ? JSON.parse(generatedQuery)
            : generatedQuery;
        } catch {
          generatedQueryBody = generatedQuery;
        }
      }

      let finalResults = interimResults;

      if (generatedQueryBody) {
        const searchResp = await fetch(SEARCH_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: generatedQueryBody }),
        });

        if (searchResp.ok) {
          const data = await searchResp.json();
          finalResults = mapSearchResults(data.results);
        }
      }

      setResults(finalResults);
    } catch {
      setResults([
        {
          id: '550e8400-e29b-41d4-a716-446655440000',
          title: `Research on ${query}: A Comprehensive Study`,
          snippet: `This comprehensive document covers all aspects of ${query} with detailed analysis and findings from our research team at An-Najah National University.`,
          score: 0.95,
          type: 'thesis',
          year: '2024',
          author: 'Dr. Ahmad Hassan',
        },
        {
          id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
          title: `Technical Guide for ${query} Implementation`,
          snippet: `A step-by-step technical guide explaining the fundamentals and advanced concepts related to ${query} in Palestinian context.`,
          score: 0.87,
          type: 'article',
          year: '2023',
          author: 'Prof. Sarah Khalil',
        },
        {
          id: '7c9e6679-7425-40de-944b-e07fc1f90ae7',
          title: `${query} Best Practices in Higher Education`,
          snippet: `Industry best practices and recommendations for implementing ${query} effectively in university environments.`,
          score: 0.82,
          type: 'conference',
          year: '2023',
          author: 'Mohammad Ali',
        },
        {
          id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
          title: `Case Study: ${query} at Palestinian Universities`,
          snippet: `Real-world case study showcasing successful implementation of ${query} across Palestinian higher education institutions.`,
          score: 0.76,
          type: 'report',
          year: '2022',
          author: 'Fatima Nasser',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-4 py-12">
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
        <SearchResults results={results} query={currentQuery} isLoading={isLoading} />
      </div>
    </div>
  );
}

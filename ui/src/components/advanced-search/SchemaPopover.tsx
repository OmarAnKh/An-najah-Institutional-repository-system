import { Info } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

const schemaFields = [
  { name: 'collection', type: 'string', desc: 'Collection identifier' },
  { name: 'bitstream_uuid', type: 'string', desc: 'Bitstream UUID' },
  { name: 'item_uuid', type: 'string', desc: 'Item UUID' },
  { name: 'chunk_id', type: 'int', desc: 'Chunk index' },
  { name: 'title', type: 'LocalizedText', desc: 'Document title (localized)' },
  { name: 'abstract', type: 'LocalizedText', desc: 'Document abstract (localized)' },
  { name: 'abstract_vector', type: 'LocalizedVector', desc: 'Embedding vector for abstract' },
  { name: 'author', type: 'List[str]', desc: 'List of authors' },
  { name: 'hasFiles', type: 'bool', desc: 'Whether document has files' },
  { name: 'publicationDate', type: 'date', desc: 'Publication date' },
  { name: 'geoReferences', type: 'List[GeoReference]', desc: 'Geographic references' },
  { name: 'temporalExpressions', type: 'List[str]', desc: 'Temporal expressions' },
];

export function SchemaPopover() {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground glass-subtle rounded-full transition-colors">
          <Info className="w-3.5 h-3.5" />
          Schema
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 glass-card border-border/50 rounded-2xl p-0" align="start">
        <div className="px-4 py-3 border-b border-border/50">
          <h4 className="text-sm font-semibold text-foreground">OpenSearch Schema</h4>
          <p className="text-xs text-muted-foreground mt-0.5">Available fields in the index</p>
        </div>
        <div className="max-h-64 overflow-y-auto p-2">
          {schemaFields.map((field) => (
            <div
              key={field.name}
              className="flex items-start gap-2 px-2 py-1.5 rounded-lg hover:bg-secondary/50 transition-colors"
            >
              <code className="text-xs font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded shrink-0">
                {field.name}
              </code>
              <div className="min-w-0">
                <span className="text-xs text-muted-foreground">{field.type}</span>
                <p className="text-xs text-muted-foreground/70">{field.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

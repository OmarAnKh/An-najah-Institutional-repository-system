import { DocumentSource } from '@/types/chat';
import { FileText, ArrowUpRight } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { motion } from 'framer-motion';

interface SourcesPopoverProps {
  sources: DocumentSource[];
}

export function SourcesPopover({ sources }: SourcesPopoverProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors duration-200 py-1 px-2 rounded-lg hover:bg-secondary">
          <FileText className="w-3 h-3" />
          <span>{sources.length} source{sources.length > 1 ? 's' : ''}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-3 rounded-2xl max-h-80 overflow-y-auto" align="start">
        <p className="text-xs font-medium text-muted-foreground mb-3">
          Sources
        </p>
        <div className="space-y-2">
          {sources.map((source, index) => (
            <motion.a
              key={source.id}
              href={`https://repository.najah.edu/items/${source.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-secondary transition-colors duration-200 group"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04 }}
            >
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <FileText className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground line-clamp-2 group-hover:text-primary transition-colors">
                  {source.title}
                </p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
            </motion.a>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

import { ChatMessage } from '@/types/chat';
import { detectLanguageDirection } from '@/lib/languageUtils';
import { ChatAvatar } from './ChatAvatar';
import { SourcesPopover } from './SourcesPopover';
import { StreamingText } from './StreamingText';
import { TypingIndicator } from './TypingIndicator';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatBubbleProps {
  message: ChatMessage;
  onStreamingComplete?: () => void;
}

export function ChatBubble({ message, onStreamingComplete }: ChatBubbleProps) {
  const direction = detectLanguageDirection(message.content);
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      <ChatAvatar role={message.role} />
      
      <div
        className={cn(
          'flex flex-col max-w-[100%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          dir={direction}
          className={cn(
            'px-4 py-2.5 transition-all duration-200',
            isUser
              ? 'bg-primary text-primary-foreground rounded-[20px] rounded-br-[6px] shadow-sm'
              : 'glass-card rounded-[20px] rounded-bl-[6px] text-foreground'
          )}
          style={{ textAlign: direction === 'rtl' ? 'right' : 'left' }}
        >
          {message.isStreaming ? (
            message.content ? (
              <StreamingText
                text={message.content}
                onComplete={onStreamingComplete}
              />
            ) : (
              <TypingIndicator />
            )
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              className={cn(
                'prose prose-sm max-w-none text-[15px] leading-[1.5] prose-p:my-1 prose-headings:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:bg-muted prose-code:text-foreground prose-a:underline prose-a:font-medium',
                isUser ? 'prose-invert prose-a:text-primary-foreground' : 'prose-a:text-primary'
              )}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && !message.isStreaming && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-2 rounded-2xl"
          >
            <SourcesPopover sources={message.sources} />
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

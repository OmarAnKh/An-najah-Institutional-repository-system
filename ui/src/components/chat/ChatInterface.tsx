import { useRef, useEffect, useState } from 'react';
import { ChatMessage, DocumentSource } from '@/types/chat';
import { ChatBubble } from './ChatBubble';
import { ChatInput } from './ChatInput';
import { ChatSidebar } from './ChatSidebar';
import { useConversations } from '@/hooks/useConversations';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { fetchAnswer, type ChatHistoryItem } from '@/lib/api';
import logoSvg from '@/assets/logo.svg';

export function ChatInterface() {
  const {
    conversations,
    activeConversation,
    activeId,
    setActiveId,
    createConversation,
    deleteConversation,
    renameConversation,
    addMessage,
    updateMessage,
  } = useConversations();

  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const buildHistory = (msgs: ChatMessage[]): ChatHistoryItem[] => {
    const pairs: ChatHistoryItem[] = [];
    let pendingQuery: string | null = null;

    msgs.forEach((msg) => {
      if (msg.role === 'user') {
        pendingQuery = msg.content;
      } else if (msg.role === 'assistant' && pendingQuery !== null) {
        pairs.push({ query: pendingQuery, response: msg.content });
        pendingQuery = null;
      }
    });

    return pairs.slice(-2);
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages]);

  const handleSendMessage = async (content: string) => {
    const historyToSend = buildHistory(activeConversation?.messages ?? []);
    let conversationId = activeId;

    if (!conversationId) {
      conversationId = createConversation();
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    addMessage(conversationId, userMessage);
    setIsLoading(true);

    const aiMessageId = crypto.randomUUID();
    const aiPlaceholder: ChatMessage = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    addMessage(conversationId, aiPlaceholder);

    try {
      const { answer, sources } = await fetchAnswer(
        content,
        historyToSend.length > 0 ? historyToSend : undefined
      );

      updateMessage(conversationId, aiMessageId, {
        content: answer,
        sources,
        isStreaming: true,
      });
    } catch {
      // Demo fallback
      const demoSources: DocumentSource[] = [
        {
          id: '550e8400-e29b-41d4-a716-446655440000',
          title: 'Research on Machine Learning in Educational Systems',
          snippet: 'This comprehensive study explores the application of ML...',
        },
        {
          id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
          title: 'Digital Transformation in Palestinian Universities',
          snippet: 'An analysis of digital infrastructure development...',
        },
      ];

      updateMessage(conversationId, aiMessageId, {
        content: `This is a demo response to your query: "${content}"\n\nIn production, this connects to your RAG backend and provides intelligent answers with proper citations from your document corpus.`,
        sources: demoSources,
        isStreaming: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamingComplete = (messageId: string) => {
    if (activeId) {
      updateMessage(activeId, messageId, { isStreaming: false });
    }
  };

  const messages = activeConversation?.messages || [];

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: sidebarOpen ? 272 : 0 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="overflow-hidden border-r border-border/50"
      >
        <ChatSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onCreate={createConversation}
          onDelete={deleteConversation}
          onRename={renameConversation}
        />
      </motion.div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toggle Button */}
        <div className="px-4 py-3 flex items-center">
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full h-8 w-8"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeft className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-6">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
              >
                <div className="w-20 h-20 rounded-full glass-card flex items-center justify-center mb-6 mx-auto shadow-lg">
                  <img src={logoSvg} alt="AI" className="w-20 h-20 object-contain rounded-full" />
                </div>
                <h2 className="text-2xl font-semibold text-foreground mb-2 tracking-tight">
                  How can I help you?
                </h2>
                <p className="text-muted-foreground text-base max-w-sm leading-relaxed">
                  Ask questions about documents in the repository
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
                className="mt-10 flex flex-wrap justify-center gap-2 max-w-lg"
              >
                {['Find research on AI', 'Latest thesis publications', 'Search renewable energy'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSendMessage(suggestion)}
                    className="px-4 py-2.5 text-sm rounded-full glass-card hover:shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 text-foreground bg-primary/10 hover:bg-primary/20"
                  >
                    {suggestion}
                  </button>
                ))}
              </motion.div>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto py-6 px-4 space-y-5">
              {messages.map((message) => (
                <ChatBubble
                  key={message.id}
                  message={message}
                  onStreamingComplete={() => handleStreamingComplete(message.id)}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

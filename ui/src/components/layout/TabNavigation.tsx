import { MessageCircle, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface TabNavigationProps {
  activeTab: 'chat' | 'search';
  onTabChange: (tab: 'chat' | 'search') => void;
}

export function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  return (
    <div className="flex items-center glass-subtle rounded-full p-1">
      <TabButton
        active={activeTab === 'chat'}
        onClick={() => onTabChange('chat')}
        icon={<MessageCircle className="w-4 h-4" />}
        label="Chat"
      />
      <TabButton
        active={activeTab === 'search'}
        onClick={() => onTabChange('search')}
        icon={<Search className="w-4 h-4" />}
        label="Search"
      />
    </div>
  );
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

function TabButton({ active, onClick, icon, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'relative flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors duration-200',
        active ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
      )}
    >
      {active && (
        <motion.div
          layoutId="tab-indicator"
          className="absolute inset-0 bg-card rounded-full shadow-md"
          transition={{ type: 'spring', bounce: 0.15, duration: 0.4 }}
        />
      )}
      <span className="relative z-10">{icon}</span>
      <span className="relative z-10">{label}</span>
    </button>
  );
}

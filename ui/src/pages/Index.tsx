import { useState, useEffect } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { SearchInterface } from '@/components/search/SearchInterface';
import { AdvancedSearchInterface } from '@/components/advanced-search/AdvancedSearchInterface';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { SplashScreen } from '@/components/SplashScreen';
import logo from '@/assets/logo.svg';

const Index = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'search' | 'advanced'>('chat');
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <SplashScreen isVisible={showSplash} />
      <div className="flex flex-col h-screen bg-background">
        {/* Glass Header */}
        <header className="sticky top-0 z-40 glass border-b border-border/50">
          <div className="max-w-screen-2xl mx-auto flex items-center justify-between px-6 py-3">
            <div className="flex items-center gap-3">
              <img 
                src={logo} 
                alt="Logo" 
                className="w-8 h-8 object-contain" 
              />
              <span className="text-[15px] font-semibold text-foreground tracking-tight">
                An-Najah Repository
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
              <div className="w-px h-5 bg-border/50 mx-2" />
              <ThemeToggle />
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' && <ChatInterface />}
            {activeTab === 'search' && <SearchInterface />}
            {activeTab === 'advanced' && <AdvancedSearchInterface />}
        </main>
      </div>
    </>
  );
};

export default Index;

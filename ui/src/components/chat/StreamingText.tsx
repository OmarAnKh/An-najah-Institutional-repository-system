import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface StreamingTextProps {
  text: string;
  onComplete?: () => void;
  speed?: number;
}

export function StreamingText({ text, onComplete, speed = 15 }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    setDisplayedText('');
    setIsComplete(false);
  }, [text]);

  useEffect(() => {
    if (!text) {
      setDisplayedText('');
      setIsComplete(true);
      onComplete?.();
      return;
    }

    const targetDurationMs = 10000;
    const intervalMs = Math.max(1, speed);
    const maxSteps = Math.max(1, Math.floor(targetDurationMs / intervalMs));
    const chunkSize = Math.max(1, Math.ceil(text.length / maxSteps));

    let currentIndex = 0;
    const interval = setInterval(() => {
      currentIndex = Math.min(text.length, currentIndex + chunkSize);
      setDisplayedText(text.slice(0, currentIndex));

      if (currentIndex >= text.length) {
        clearInterval(interval);
        setIsComplete(true);
        onComplete?.();
      }
    }, intervalMs);

    return () => {
      clearInterval(interval);
      if (!isComplete) {
        setIsComplete(true);
        onComplete?.();
      }
    };
  }, [text, speed, onComplete, isComplete]);

  return (
    <span>
      {displayedText}
      {!isComplete && (
        <motion.span
          className="inline-block w-0.5 h-4 bg-primary ml-0.5 align-middle"
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
        />
      )}
    </span>
  );
}

import { motion } from 'framer-motion';

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1 px-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full"
          animate={{
            opacity: [0.4, 1, 0.4],
            scale: [0.85, 1, 0.85],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.15,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}

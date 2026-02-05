import { motion } from 'framer-motion';
import logoSvg from '@/assets/logo.svg';

interface AnimatedLogoProps {
  size?: number;
  showLoadingText?: boolean;
  loadingText?: string;
}

/**
 * AnimatedLogo - An animated version of the An-Najah Institutional Repository System logo
 * 
 * Features:
 * - Book stays static in the center
 * - Outer circle ring rotates slowly (360° every 45 seconds)
 * - Outer glow pulse effect on the rotating ring
 * - Optional loading text with opacity pulse
 */
export const AnimatedLogo = ({ 
  size = 280, 
  showLoadingText = true,
  loadingText = "Initializing..."
}: AnimatedLogoProps) => {
  return (
    <div className="flex flex-col items-center justify-center gap-6">
      {/* Main logo container */}
      <div
        className="relative"
        style={{ width: size, height: size }}
      >
        {/* Rotating outer ring glow effect */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'radial-gradient(circle, transparent 35%, rgba(34, 211, 238, 0.2) 45%, rgba(18, 68, 113, 0.3) 55%, transparent 65%)',
            filter: 'blur(8px)',
          }}
          animate={{ 
            rotate: 360,
            scale: [1, 1.06, 1],
            opacity: [0.5, 0.85, 0.5] 
          }}
          transition={{
            rotate: {
              duration: 45,
              repeat: Infinity,
              ease: "linear"
            },
            scale: {
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut"
            },
            opacity: {
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut"
            }
          }}
        />

        {/* Secondary rotating glow ring */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0%, rgba(34, 211, 238, 0.15) 25%, transparent 50%, rgba(34, 211, 238, 0.15) 75%, transparent 100%)',
            filter: 'blur(4px)',
          }}
          animate={{ 
            rotate: 360,
          }}
          transition={{
            duration: 45,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Static book/logo - does not rotate */}
        <motion.img
          src={logoSvg}
          alt="An-Najah Institutional Repository System Logo"
          className="relative z-10 w-full h-full object-contain"
          style={{ 
            filter: 'drop-shadow(0 0 15px rgba(34, 211, 238, 0.25))'
          }}
          animate={{
            filter: [
              'drop-shadow(0 0 15px rgba(34, 211, 238, 0.25))',
              'drop-shadow(0 0 25px rgba(34, 211, 238, 0.4))',
              'drop-shadow(0 0 15px rgba(34, 211, 238, 0.25))'
            ]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        {/* Rotating dots around the perimeter */}
        <motion.div
          className="absolute inset-0"
          animate={{ rotate: 360 }}
          transition={{
            duration: 45,
            repeat: Infinity,
            ease: "linear"
          }}
        >
          {/* Glowing dots at cardinal points */}
          {[0, 90, 180, 270].map((angle, i) => (
            <motion.div
              key={angle}
              className="absolute w-2 h-2 rounded-full bg-cyan-400"
              style={{
                top: '50%',
                left: '50%',
                transform: `rotate(${angle}deg) translateY(-${size / 2 - 8}px) translate(-50%, -50%)`,
                boxShadow: '0 0 8px rgba(34, 211, 238, 0.8)',
              }}
              animate={{
                scale: [0.8, 1.3, 0.8],
                opacity: [0.6, 1, 0.6],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: i * 0.5,
              }}
            />
          ))}
        </motion.div>
      </div>

      {/* Loading text with opacity pulse */}
      {showLoadingText && (
        <motion.p
          className="text-cyan-400/80 text-sm tracking-widest uppercase font-light"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {loadingText}
        </motion.p>
      )}
    </div>
  );
};

export default AnimatedLogo;

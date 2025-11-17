'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';
import { DURATION, EASE_STANDARD } from '@/lib/motion';

/**
 * PageTransition - Smooth fade transitions between pages
 *
 * Eliminates the "blink" or "pop" when navigating
 * Uses pathname as key to trigger exit/enter animations
 */
export default function PageTransition({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{
          duration: DURATION.fast,
          ease: EASE_STANDARD,
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * ORLA³ Motion Design System
 *
 * Industry-standard animation configurations following:
 * - Apple Human Interface Guidelines
 * - Material Design Motion
 * - Framer Motion best practices
 *
 * Key Principles:
 * 1. Use GPU-accelerated properties only (transform, opacity)
 * 2. Easing curves feel natural and responsive
 * 3. Duration scales with distance traveled
 * 4. Respect user's motion preferences
 */

// ============================================================================
// EASING CURVES
// ============================================================================

/**
 * Premium easing curve - Use for hero elements and primary interactions
 * Cubic bezier that starts fast and decelerates smoothly
 */
export const EASE_PREMIUM = [0.22, 1, 0.36, 1];

/**
 * Standard easing - Use for most UI elements
 * Balanced acceleration/deceleration
 */
export const EASE_STANDARD = [0.4, 0, 0.2, 1];

/**
 * Snappy easing - Use for small, quick interactions
 * Fast in, fast out
 */
export const EASE_SNAPPY = [0.25, 0.1, 0.25, 1];

/**
 * Smooth easing - Use for background elements and subtle animations
 * Very gentle, almost linear
 */
export const EASE_SMOOTH = [0.33, 1, 0.68, 1];

// ============================================================================
// DURATION SCALES
// ============================================================================

export const DURATION = {
  /** Instant feedback (100ms) - Micro-interactions */
  instant: 0.1,

  /** Fast (200ms) - Buttons, toggles, small UI changes */
  fast: 0.2,

  /** Normal (300ms) - Cards, modals, most UI elements */
  normal: 0.3,

  /** Moderate (400ms) - Page elements, larger cards */
  moderate: 0.4,

  /** Slow (500ms) - Full-screen transitions, hero elements */
  slow: 0.5,

  /** Extra slow (700ms) - Special reveals, storytelling moments */
  extraSlow: 0.7,
};

// ============================================================================
// STAGGER CONFIGURATIONS
// ============================================================================

/**
 * Stagger timing for sequential animations
 */
export const STAGGER = {
  /** Tight stagger (50ms) - Dense grids, many items */
  tight: 0.05,

  /** Normal stagger (100ms) - Standard lists and grids */
  normal: 0.1,

  /** Relaxed stagger (150ms) - Hero sections, featured content */
  relaxed: 0.15,
};

// ============================================================================
// SPRING CONFIGURATIONS
// ============================================================================

/**
 * Spring physics for bouncy, playful interactions
 */
export const SPRING = {
  /** Gentle spring - Subtle bounce */
  gentle: {
    type: "spring",
    stiffness: 300,
    damping: 30,
  },

  /** Bouncy spring - Pronounced bounce for emphasis */
  bouncy: {
    type: "spring",
    stiffness: 400,
    damping: 25,
  },

  /** Snappy spring - Quick, responsive */
  snappy: {
    type: "spring",
    stiffness: 500,
    damping: 35,
  },
};

// ============================================================================
// ANIMATION VARIANTS
// ============================================================================

/**
 * Fade in from below - Classic entrance animation
 */
export const fadeInUp = {
  initial: {
    opacity: 0,
    y: 24,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
  exit: {
    opacity: 0,
    y: -24,
    transition: {
      duration: DURATION.fast,
      ease: EASE_STANDARD,
    },
  },
};

/**
 * Fade in from above
 */
export const fadeInDown = {
  initial: {
    opacity: 0,
    y: -24,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
};

/**
 * Fade in from left
 */
export const fadeInLeft = {
  initial: {
    opacity: 0,
    x: -24,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
};

/**
 * Fade in from right
 */
export const fadeInRight = {
  initial: {
    opacity: 0,
    x: 24,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
};

/**
 * Scale in - Grows from center
 */
export const scaleIn = {
  initial: {
    opacity: 0,
    scale: 0.9,
  },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
};

/**
 * Slide in from bottom (full height) - For modals/drawers
 */
export const slideInBottom = {
  initial: {
    y: "100%",
    opacity: 0,
  },
  animate: {
    y: 0,
    opacity: 1,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_STANDARD,
    },
  },
  exit: {
    y: "100%",
    opacity: 0,
    transition: {
      duration: DURATION.fast,
      ease: EASE_STANDARD,
    },
  },
};

/**
 * Container variant for staggered children
 * Use with staggerChildren property
 */
export const staggerContainer = (staggerDelay: number = STAGGER.normal) => ({
  initial: {},
  animate: {
    transition: {
      staggerChildren: staggerDelay,
      delayChildren: 0.1, // Small delay before first child
    },
  },
});

/**
 * Child item variant for stagger containers
 */
export const staggerItem = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
};

// ============================================================================
// HOVER/TAP ANIMATIONS
// ============================================================================

/**
 * Subtle lift on hover - For cards
 */
export const hoverLift = {
  rest: {
    y: 0,
    scale: 1,
  },
  hover: {
    y: -8,
    scale: 1.02,
    transition: {
      duration: DURATION.fast,
      ease: EASE_SNAPPY,
    },
  },
  tap: {
    scale: 0.98,
    transition: {
      duration: DURATION.instant,
    },
  },
};

/**
 * Gentle scale on hover - For buttons
 */
export const hoverScale = {
  rest: {
    scale: 1,
  },
  hover: {
    scale: 1.05,
    transition: {
      duration: DURATION.fast,
      ease: EASE_SNAPPY,
    },
  },
  tap: {
    scale: 0.95,
    transition: {
      duration: DURATION.instant,
    },
  },
};

/**
 * Glow effect on hover - For primary CTAs
 */
export const hoverGlow = {
  rest: {
    boxShadow: "0 0 0 0 rgba(255, 215, 0, 0)",
  },
  hover: {
    boxShadow: "0 0 30px 0 rgba(255, 215, 0, 0.3)",
    transition: {
      duration: DURATION.normal,
      ease: EASE_SMOOTH,
    },
  },
};

// ============================================================================
// PAGE TRANSITIONS
// ============================================================================

/**
 * Page fade transition
 */
export const pageTransition = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      duration: DURATION.normal,
      ease: EASE_STANDARD,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: DURATION.fast,
      ease: EASE_STANDARD,
    },
  },
};

/**
 * Page slide transition (for modal/drawer overlays)
 */
export const pageSlide = {
  initial: {
    x: "100%",
  },
  animate: {
    x: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_STANDARD,
    },
  },
  exit: {
    x: "100%",
    transition: {
      duration: DURATION.fast,
      ease: EASE_STANDARD,
    },
  },
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Respect user's motion preferences
 * Returns reduced motion variants if user prefers reduced motion
 */
export const respectMotionPreference = (variants: any) => {
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
    };
  }
  return variants;
};

/**
 * Create a custom stagger container with specific delay
 */
export const createStaggerContainer = (
  delayChildren: number = 0.1,
  staggerChildren: number = STAGGER.normal
) => ({
  initial: {},
  animate: {
    transition: {
      delayChildren,
      staggerChildren,
    },
  },
});

// ============================================================================
// PRESET COMBINATIONS
// ============================================================================

/**
 * Dashboard card preset - Fade in up with lift on hover
 */
export const dashboardCard = {
  initial: fadeInUp.initial,
  animate: fadeInUp.animate,
  whileHover: hoverLift.hover,
  whileTap: hoverLift.tap,
};

/**
 * Primary button preset - Scale with glow
 */
export const primaryButton = {
  whileHover: {
    scale: 1.05,
    boxShadow: "0 0 30px 0 rgba(255, 215, 0, 0.3)",
    transition: {
      duration: DURATION.fast,
      ease: EASE_SNAPPY,
    },
  },
  whileTap: {
    scale: 0.95,
    transition: {
      duration: DURATION.instant,
    },
  },
};

/**
 * Modal overlay preset
 */
export const modalOverlay = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      duration: DURATION.fast,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: DURATION.fast,
    },
  },
};

/**
 * Modal content preset
 */
export const modalContent = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 20,
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: DURATION.moderate,
      ease: EASE_PREMIUM,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: {
      duration: DURATION.fast,
      ease: EASE_STANDARD,
    },
  },
};

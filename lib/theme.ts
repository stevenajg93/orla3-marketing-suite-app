/**
 * ORLA³ Marketing Suite - Design System
 *
 * Complete brand theme and component styling guidelines.
 * This ensures consistent, professional brand experience across the entire application.
 *
 * Brand Story:
 * - Gold: Represents Orla (the Gold Lady) and the sun - energy, warmth, and achievement
 * - Cobalt/Royal: Trust, professionalism, and sophistication
 * - White: Clarity, transparency, and innovation
 * - Black/Slate: Authority and elegance
 */

export const theme = {
  // ============================================================================
  // TYPOGRAPHY HIERARCHY
  // ============================================================================
  typography: {
    // Main page titles (H1) - The hero, demands attention
    h1: {
      size: 'text-3xl sm:text-4xl md:text-5xl lg:text-6xl',
      weight: 'font-black',
      // Brand name gets gold, rest stays white for contrast
      brandColor: 'text-transparent bg-clip-text bg-gradient-to-r from-gold via-gold-intense to-gold',
      defaultColor: 'text-white',
      spacing: 'mb-2 sm:mb-4'
    },

    // Section headings (H2) - Category headers, engaging gradients
    h2: {
      size: 'text-xl sm:text-2xl md:text-3xl',
      weight: 'font-bold',
      // Rotate between brand gradients for visual interest
      colors: {
        primary: 'text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold',
        secondary: 'text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense',
        tertiary: 'text-transparent bg-clip-text bg-gradient-to-r from-royal to-cobalt'
      },
      spacing: 'mb-3 sm:mb-4'
    },

    // Subsection headings (H3) - Card titles, modal headers
    h3: {
      size: 'text-lg sm:text-xl md:text-2xl',
      weight: 'font-bold',
      color: 'text-white',
      spacing: 'mb-2 sm:mb-3'
    },

    // Small headings (H4) - Form sections, list headers
    h4: {
      size: 'text-base sm:text-lg',
      weight: 'font-semibold',
      color: 'text-gray-200',
      spacing: 'mb-2'
    },

    // Body text - Descriptions, content, readable and doesn't compete
    body: {
      size: 'text-sm sm:text-base',
      weight: 'font-normal',
      color: 'text-gray-300',
      spacing: 'mb-3'
    },

    // Small text - Labels, helper text, metadata
    small: {
      size: 'text-xs sm:text-sm',
      weight: 'font-normal',
      color: 'text-gray-400',
      spacing: 'mb-1'
    },

    // Micro text - Timestamps, footnotes
    micro: {
      size: 'text-xs',
      weight: 'font-normal',
      color: 'text-gray-500'
    }
  },

  // ============================================================================
  // BUTTONS - Clear hierarchy of actions
  // ============================================================================
  buttons: {
    // Primary CTA - Main actions (Submit, Create, Publish, Save)
    // Gold = Achievement, energy, action
    primary: {
      base: 'px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition shadow-lg',
      colors: 'bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense text-slate-900',
      disabled: 'opacity-50 cursor-not-allowed'
    },

    // Secondary - Important but not primary (Connect, View, Explore)
    // Cobalt/Royal = Trust and professionalism
    secondary: {
      base: 'px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition shadow-lg',
      colors: 'bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white',
      disabled: 'opacity-50 cursor-not-allowed'
    },

    // Tertiary/Outline - Low emphasis (Cancel, Back, Skip)
    tertiary: {
      base: 'px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition',
      colors: 'border-2 border-white/30 hover:border-white/50 text-white hover:bg-white/5',
      disabled: 'opacity-50 cursor-not-allowed'
    },

    // Danger - Destructive actions (Delete, Disconnect, Remove)
    danger: {
      base: 'px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition',
      colors: 'border-2 border-red-500/50 hover:border-red-500 text-red-400 hover:text-red-300 hover:bg-red-500/10',
      disabled: 'opacity-50 cursor-not-allowed'
    },

    // Ghost - Minimal emphasis (Close, Dismiss)
    ghost: {
      base: 'px-3 py-2 rounded-lg font-medium transition',
      colors: 'text-gray-400 hover:text-white hover:bg-white/5'
    },

    // Small variants (for compact UIs)
    small: {
      base: 'px-3 py-1.5 text-sm rounded-md font-medium transition'
    }
  },

  // ============================================================================
  // FORM ELEMENTS
  // ============================================================================
  forms: {
    // Input fields
    input: {
      base: 'w-full px-4 py-3 rounded-lg transition',
      colors: 'bg-white/5 border border-white/20 text-white placeholder-gray-500',
      focus: 'focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold',
      error: 'border-red-500 focus:ring-red-500',
      disabled: 'opacity-50 cursor-not-allowed bg-white/5'
    },

    // Textarea
    textarea: {
      base: 'w-full px-4 py-3 rounded-lg transition resize-none',
      colors: 'bg-white/5 border border-white/20 text-white placeholder-gray-500',
      focus: 'focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold'
    },

    // Select dropdowns
    select: {
      base: 'w-full px-4 py-3 rounded-lg transition cursor-pointer',
      colors: 'bg-white/5 border border-white/20 text-white',
      focus: 'focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold'
    },

    // Checkboxes and radios
    checkbox: {
      base: 'w-4 h-4 rounded transition cursor-pointer',
      colors: 'bg-white/5 border-white/30 text-gold focus:ring-gold focus:ring-2'
    },

    // Labels
    label: {
      base: 'block mb-2 font-medium',
      color: 'text-gray-300',
      size: 'text-sm sm:text-base'
    },

    // Helper text
    helper: {
      base: 'mt-1',
      color: 'text-gray-400',
      size: 'text-xs sm:text-sm'
    },

    // Error messages
    error: {
      base: 'mt-1',
      color: 'text-red-400',
      size: 'text-xs sm:text-sm'
    }
  },

  // ============================================================================
  // CARDS & CONTAINERS
  // ============================================================================
  cards: {
    // Standard card
    base: {
      container: 'rounded-2xl border transition',
      background: 'bg-white/10 backdrop-blur-lg',
      border: 'border-white/20 hover:border-white/30',
      padding: 'p-4 sm:p-6'
    },

    // Interactive card (clickable)
    interactive: {
      container: 'rounded-2xl border transition cursor-pointer',
      background: 'bg-white/10 backdrop-blur-lg',
      border: 'border-white/20 hover:border-white/40',
      hover: 'hover:scale-105 hover:shadow-xl',
      padding: 'p-4 sm:p-6'
    },

    // Feature card (dashboard tools)
    feature: {
      container: 'group relative overflow-hidden rounded-2xl border transition',
      background: 'bg-white/5 backdrop-blur-lg',
      border: 'border-white/10 hover:border-white/30',
      hover: 'hover:scale-105',
      padding: 'p-4 sm:p-6'
    },

    // Stat card
    stat: {
      container: 'rounded-xl border',
      background: 'bg-white/10 backdrop-blur-lg',
      border: 'border-white/20',
      padding: 'p-4 sm:p-6'
    }
  },

  // ============================================================================
  // ALERTS & NOTIFICATIONS
  // ============================================================================
  alerts: {
    // Success - Gold (achievement, completion)
    success: {
      container: 'px-4 py-3 rounded-lg border',
      colors: 'bg-gold/20 border-gold text-gold',
      icon: 'text-gold'
    },

    // Warning - Gold-intense (attention needed)
    warning: {
      container: 'px-4 py-3 rounded-lg border',
      colors: 'bg-gold-intense/20 border-gold-intense text-gold-intense',
      icon: 'text-gold-intense'
    },

    // Error - Red (critical issues)
    error: {
      container: 'px-4 py-3 rounded-lg border',
      colors: 'bg-red-500/20 border-red-500 text-red-200',
      icon: 'text-red-400'
    },

    // Info - Cobalt (helpful information)
    info: {
      container: 'px-4 py-3 rounded-lg border',
      colors: 'bg-cobalt/20 border-cobalt/50 text-cobalt-200',
      icon: 'text-cobalt-300'
    }
  },

  // ============================================================================
  // BADGES & TAGS
  // ============================================================================
  badges: {
    // Gold badge - Premium, new, featured
    gold: {
      base: 'px-3 py-1 rounded-full text-xs font-bold',
      colors: 'bg-gold/20 border border-gold text-gold'
    },

    // Cobalt badge - Active, verified
    cobalt: {
      base: 'px-3 py-1 rounded-full text-xs font-bold',
      colors: 'bg-cobalt/20 border border-cobalt text-cobalt-300'
    },

    // Royal badge - Premium tier
    royal: {
      base: 'px-3 py-1 rounded-full text-xs font-bold',
      colors: 'bg-royal/20 border border-royal text-royal-300'
    },

    // Gray badge - Neutral, disabled, coming soon
    gray: {
      base: 'px-3 py-1 rounded-full text-xs font-bold',
      colors: 'bg-gray-700/30 border border-gray-600 text-gray-400'
    },

    // Status dot (connected, active, etc)
    dot: {
      base: 'inline-block w-2 h-2 rounded-full',
      colors: {
        active: 'bg-gold animate-pulse',
        inactive: 'bg-gray-500'
      }
    }
  },

  // ============================================================================
  // PROGRESS & LOADING
  // ============================================================================
  progress: {
    // Progress bar container
    bar: {
      container: 'w-full h-2 rounded-full overflow-hidden',
      background: 'bg-white/10',
      fill: 'h-full bg-gradient-to-r from-cobalt to-royal transition-all duration-500'
    },

    // Loading spinner
    spinner: {
      base: 'inline-block animate-spin rounded-full border-b-2',
      colors: 'border-gold',
      sizes: {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12'
      }
    }
  },

  // ============================================================================
  // LINKS
  // ============================================================================
  links: {
    // Primary links (in content)
    primary: {
      base: 'font-medium transition underline-offset-4',
      colors: 'text-gold hover:text-gold-intense hover:underline'
    },

    // Secondary links (navigation)
    secondary: {
      base: 'font-medium transition',
      colors: 'text-cobalt-300 hover:text-cobalt-200'
    },

    // Subtle links (breadcrumbs, footers)
    subtle: {
      base: 'transition',
      colors: 'text-gray-400 hover:text-gray-300'
    }
  },

  // ============================================================================
  // BACKGROUNDS & GRADIENTS
  // ============================================================================
  backgrounds: {
    // Main app background
    app: 'min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900',

    // Card overlay gradients (for feature cards)
    overlays: {
      gold: 'absolute inset-0 bg-gradient-to-br from-gold to-gold-intense opacity-10 group-hover:opacity-20 transition-opacity',
      cobalt: 'absolute inset-0 bg-gradient-to-br from-cobalt to-cobalt-600 opacity-10 group-hover:opacity-20 transition-opacity',
      royal: 'absolute inset-0 bg-gradient-to-br from-royal to-royal-600 opacity-10 group-hover:opacity-20 transition-opacity'
    }
  },

  // ============================================================================
  // SPACING & LAYOUT
  // ============================================================================
  spacing: {
    // Page container
    container: 'max-w-7xl mx-auto',

    // Page padding
    page: 'p-3 sm:p-4 md:p-6 lg:p-8',

    // Section spacing
    section: 'mb-6 sm:mb-8 md:mb-12',

    // Grid gaps
    grid: {
      tight: 'gap-2 sm:gap-3',
      normal: 'gap-4 sm:gap-6',
      loose: 'gap-6 sm:gap-8'
    }
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Combine theme classes safely
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Get button classes by variant
 */
export function getButtonClasses(
  variant: 'primary' | 'secondary' | 'tertiary' | 'danger' | 'ghost' = 'primary',
  disabled: boolean = false,
  small: boolean = false
): string {
  const button = theme.buttons[variant];
  return cn(
    small ? theme.buttons.small.base : button.base,
    button.colors,
    disabled && button.disabled
  );
}

/**
 * Get alert classes by type
 */
export function getAlertClasses(
  type: 'success' | 'warning' | 'error' | 'info' = 'info'
): string {
  const alert = theme.alerts[type];
  return cn(alert.container, alert.colors);
}

/**
 * Get badge classes by variant
 */
export function getBadgeClasses(
  variant: 'gold' | 'cobalt' | 'royal' | 'gray' = 'gold'
): string {
  const badge = theme.badges[variant];
  return cn(badge.base, badge.colors);
}

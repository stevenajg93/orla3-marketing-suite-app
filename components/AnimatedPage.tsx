'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { staggerContainer, staggerItem, fadeInUp, DURATION, EASE_PREMIUM } from '@/lib/motion';

/**
 * AnimatedPage - Wrapper for consistent page animations
 *
 * Usage:
 * <AnimatedPage>
 *   <AnimatedPage.Header title="Page Title" subtitle="Description" />
 *   <AnimatedPage.Section>
 *     <AnimatedPage.Card>Content</AnimatedPage.Card>
 *     <AnimatedPage.Card>Content</AnimatedPage.Card>
 *   </AnimatedPage.Section>
 * </AnimatedPage>
 */

interface AnimatedPageProps {
  children: ReactNode;
  className?: string;
}

function AnimatedPageRoot({ children, className = '' }: AnimatedPageProps) {
  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={staggerContainer(0.05)}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

function Header({ title, subtitle, action, className = '' }: HeaderProps) {
  return (
    <motion.div
      variants={staggerItem}
      className={`mb-6 sm:mb-8 ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-2">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm sm:text-base md:text-lg text-gray-400">{subtitle}</p>
          )}
        </div>
        {action && (
          <div className="flex-shrink-0">
            {action}
          </div>
        )}
      </div>
    </motion.div>
  );
}

interface SectionProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

function Section({ children, className = '', delay = 0.08 }: SectionProps) {
  return (
    <motion.div
      variants={staggerContainer(delay)}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: () => void;
}

function Card({ children, className = '', hoverable = false, onClick }: CardProps) {
  const hoverProps = hoverable ? {
    whileHover: {
      y: -4,
      scale: 1.01,
      transition: {
        duration: DURATION.fast,
        ease: EASE_PREMIUM,
      },
    },
    whileTap: {
      scale: 0.99,
      transition: {
        duration: 0.1,
      },
    },
  } : {};

  return (
    <motion.div
      variants={staggerItem}
      {...hoverProps}
      onClick={onClick}
      className={`${className} ${hoverable || onClick ? 'cursor-pointer' : ''}`}
    >
      {children}
    </motion.div>
  );
}

interface GridProps {
  children: ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: string;
  className?: string;
}

function Grid({ children, cols = { default: 1, sm: 2, lg: 3 }, gap = '4 sm:gap-6', className = '' }: GridProps) {
  const colsClass = `grid-cols-${cols.default || 1} ${cols.sm ? `sm:grid-cols-${cols.sm}` : ''} ${cols.md ? `md:grid-cols-${cols.md}` : ''} ${cols.lg ? `lg:grid-cols-${cols.lg}` : ''} ${cols.xl ? `xl:grid-cols-${cols.xl}` : ''}`;

  return (
    <motion.div
      variants={staggerContainer(0.08)}
      className={`grid ${colsClass} gap-${gap} ${className}`}
    >
      {children}
    </motion.div>
  );
}

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  className = '',
  type = 'button'
}: ButtonProps) {
  const baseClasses = 'font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white shadow-lg hover:shadow-xl',
    secondary: 'bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense text-slate-900 shadow-lg hover:shadow-xl',
    outline: 'border-2 border-white/20 hover:border-white/40 text-white backdrop-blur-sm',
    ghost: 'text-gray-300 hover:text-white hover:bg-white/5',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      transition={{ duration: DURATION.fast, ease: EASE_PREMIUM }}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {children}
    </motion.button>
  );
}

interface FadeInProps {
  children: ReactNode;
  delay?: number;
  className?: string;
}

function FadeIn({ children, delay = 0, className = '' }: FadeInProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: DURATION.moderate, delay, ease: EASE_PREMIUM }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// Compound component pattern
export const AnimatedPage = Object.assign(AnimatedPageRoot, {
  Header,
  Section,
  Card,
  Grid,
  Button,
  FadeIn,
});

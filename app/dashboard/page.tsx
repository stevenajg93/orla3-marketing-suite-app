'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/context/AuthContext';
import UnverifiedEmailBanner from './components/UnverifiedEmailBanner';
import { staggerContainer, staggerItem, hoverLift, DURATION, EASE_PREMIUM } from '@/lib/motion';

const contentCreation = [
  { name: 'Blog Writer', icon: '', href: '/dashboard/blog', description: 'AI-powered long-form content', color: 'from-cobalt to-cobalt-600' },
  { name: 'Carousel Maker', icon: '', href: '/dashboard/carousel', description: 'Engaging social carousels', color: 'from-cobalt to-cobalt-600' },
  { name: 'Media Library', icon: '', href: '/dashboard/media', description: 'Browse & manage assets', color: 'from-gold to-gold-600' },
];

const socialManagement = [
  { name: 'Social Manager', icon: '', href: '/dashboard/social', description: 'Unified social posting & scheduling', color: 'from-gold to-gold-intense' },
];

const planningAnalysis = [
  { name: 'Content Calendar', icon: '', href: '/dashboard/calendar', description: 'Plan & schedule ORLA³ content', color: 'from-royal to-royal-600' },
  { name: 'Analytics', icon: '', href: '/dashboard/analytics', description: 'Track content performance', color: 'from-cobalt to-cobalt-600', disabled: false },
  { name: 'Brand Voice', icon: '', href: '/dashboard/brand-voice', description: 'Consistent messaging', color: 'from-cobalt to-cobalt-600', disabled: false },
  { name: 'Competitor Analysis', icon: '', href: '/dashboard/competitor', description: 'Market insights', color: 'from-gold-intense to-gold-600', disabled: false },
  { name: 'Strategy Planner', icon: '', href: '/dashboard/strategy', description: 'Content strategy', color: 'from-cobalt to-cobalt-600', disabled: false },
  { name: 'Find a Videographer', icon: '', href: 'https://orla3.com/browse', description: 'Hire professional creators', color: 'from-cobalt to-gold-intense', external: true },
];

const ToolCard = ({ tool }: { tool: any }) => {
  const CardContent = (
    <>
      <div className={`absolute inset-0 bg-gradient-to-br ${tool.color} opacity-10 group-hover:opacity-20 transition-opacity duration-300`}></div>
      <div className="relative p-4 sm:p-6 bg-white/5 backdrop-blur-lg">
        <div className="flex items-start justify-between">
          <div className="text-4xl sm:text-5xl mb-3 sm:mb-4">{tool.icon}</div>
          {tool.isNew && (
            <span className="px-2 py-1 bg-gold/20 border border-gold rounded-full text-gold text-xs font-bold animate-pulse">
              NEW
            </span>
          )}
          {tool.external && (
            <span className="text-gray-400 text-xs">↗</span>
          )}
        </div>
        <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-1 sm:mb-2">{tool.name}</h3>
        <p className="text-sm sm:text-base text-gray-400">{tool.description}</p>
        {tool.disabled && (
          <span className="inline-block mt-2 sm:mt-3 px-3 py-1 bg-gold-600/30 text-gold-400 text-xs font-bold rounded-full">
            Coming Soon
          </span>
        )}
      </div>
    </>
  );

  const baseClassName = `group relative overflow-hidden rounded-2xl border border-white/10 block ${
    tool.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
  }`;

  if (tool.disabled) {
    return (
      <motion.div
        variants={staggerItem}
        className={baseClassName}
      >
        {CardContent}
      </motion.div>
    );
  }

  if (tool.external) {
    return (
      <motion.a
        href={tool.href}
        target="_blank"
        rel="noopener noreferrer"
        variants={staggerItem}
        whileHover={{
          y: -8,
          scale: 1.02,
          transition: {
            duration: DURATION.fast,
            ease: EASE_PREMIUM,
          },
        }}
        whileTap={{
          scale: 0.98,
          transition: {
            duration: 0.1,
          },
        }}
        className={baseClassName}
      >
        {CardContent}
      </motion.a>
    );
  }

  return (
    <Link href={tool.href} className="block">
      <motion.div
        variants={staggerItem}
        whileHover={{
          y: -8,
          scale: 1.02,
          transition: {
            duration: DURATION.fast,
            ease: EASE_PREMIUM,
          },
        }}
        whileTap={{
          scale: 0.98,
          transition: {
            duration: 0.1,
          },
        }}
        className={baseClassName}
      >
        {CardContent}
      </motion.div>
    </Link>
  );
};

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-3 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Unverified Email Banner */}
        {user && !user.email_verified && (
          <UnverifiedEmailBanner userEmail={user.email} />
        )}

        {/* Header with fade in */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: DURATION.moderate, ease: EASE_PREMIUM }}
          className="mb-6 sm:mb-8 md:mb-12"
        >
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black mb-2 sm:mb-4">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold via-gold-intense to-gold">Orla³</span>
            <span className="text-white"> Marketing Suite</span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-300">AI-powered marketing automation at your fingertips</p>
        </motion.div>

        {/* TIER 1: Content Creation */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={staggerContainer(0.08)}
          className="mb-6 sm:mb-8"
        >
          <motion.h2
            variants={staggerItem}
            className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4 flex items-center gap-2 sm:gap-3"
          >
            <span className="text-2xl sm:text-3xl"></span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">Content Creation</span>
          </motion.h2>
          <motion.div
            variants={staggerContainer(0.08)}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
          >
            {contentCreation.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </motion.div>
        </motion.div>

        {/* TIER 2: Social Management */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={staggerContainer(0.08)}
          className="mb-6 sm:mb-8"
        >
          <motion.h2
            variants={staggerItem}
            className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4 flex items-center gap-2 sm:gap-3"
          >
            <span className="text-2xl sm:text-3xl"></span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense">Social Management</span>
          </motion.h2>
          <motion.div
            variants={staggerContainer(0.08)}
            className="grid grid-cols-1 gap-4 sm:gap-6"
          >
            {socialManagement.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </motion.div>
        </motion.div>

        {/* TIER 3: Planning & Intelligence */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={staggerContainer(0.08)}
          className="mb-6 sm:mb-8"
        >
          <motion.h2
            variants={staggerItem}
            className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4 flex items-center gap-2 sm:gap-3"
          >
            <span className="text-2xl sm:text-3xl"></span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-royal to-cobalt">Planning & Intelligence</span>
          </motion.h2>
          <motion.div
            variants={staggerContainer(0.08)}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
          >
            {planningAnalysis.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

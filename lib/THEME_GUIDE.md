# ORLA³ Design System - Implementation Guide

## 🎨 Brand Philosophy

**ORLA³** is about **empowerment through clarity**. Our design system reflects:

- **Gold**: Achievement, energy, and action (Orla, the Gold Lady)
- **Cobalt/Royal**: Trust, professionalism, and sophistication
- **White**: Clarity, transparency, and innovation
- **Slate**: Authority and elegance

---

## 📐 Visual Hierarchy

### The Golden Rule
**Gold draws the eye, use it strategically:**
1. Brand name "Orla³" - Always gold
2. Primary CTAs - Gold gradient (represents achievement/action)
3. Success states - Gold (achievement completed)
4. Important badges/highlights - Gold accent

### Typography Hierarchy
```
H1 (Main Title)    → Brand name: Gold gradient | Rest: White
H2 (Sections)      → Brand color gradients (cobalt-gold, gold-intense, royal-cobalt)
H3 (Subsections)   → White
H4 (Form sections) → Gray-200
Body Text          → Gray-300
Small Text         → Gray-400
Micro Text         → Gray-500
```

---

## 🔘 Button Hierarchy

### When to use each variant:

**Primary (Gold Gradient)**
- Main page actions: "Create Post", "Publish", "Save Changes", "Subscribe"
- Conversion-focused CTAs
- Represents achievement and forward motion

**Secondary (Cobalt-Royal Gradient)**
- Supporting actions: "Connect Account", "View Details", "Explore"
- Trust-building actions
- Professional interactions

**Tertiary (Outline)**
- Low-emphasis actions: "Cancel", "Back", "Skip"
- Navigation
- Reversible actions

**Danger (Red Outline)**
- Destructive actions: "Delete", "Disconnect", "Remove"
- Always requires confirmation
- Use sparingly

---

## 📝 Usage Examples

### Import the theme
```typescript
import { theme, getButtonClasses, getAlertClasses, getBadgeClasses } from '@/lib/theme';
```

### Page Layout
```tsx
<div className={theme.backgrounds.app}>
  <div className={`${theme.spacing.container} ${theme.spacing.page}`}>
    {/* Content */}
  </div>
</div>
```

### Typography
```tsx
{/* Main page title */}
<h1 className={`${theme.typography.h1.size} ${theme.typography.h1.weight} ${theme.typography.h1.spacing}`}>
  <span className={theme.typography.h1.brandColor}>Orla³</span>
  <span className={theme.typography.h1.defaultColor}> Marketing Suite</span>
</h1>

{/* Section heading */}
<h2 className={`${theme.typography.h2.size} ${theme.typography.h2.weight} ${theme.typography.h2.spacing}`}>
  <span className={theme.typography.h2.colors.primary}>Content Creation</span>
</h2>

{/* Card title */}
<h3 className={`${theme.typography.h3.size} ${theme.typography.h3.weight} ${theme.typography.h3.color}`}>
  Blog Writer
</h3>

{/* Body text */}
<p className={`${theme.typography.body.size} ${theme.typography.body.color}`}>
  AI-powered long-form content creation for your blog.
</p>
```

### Buttons
```tsx
{/* Primary CTA */}
<button className={getButtonClasses('primary')}>
  Create Post
</button>

{/* Secondary action */}
<button className={getButtonClasses('secondary')}>
  Connect Account
</button>

{/* Tertiary/Cancel */}
<button className={getButtonClasses('tertiary')}>
  Cancel
</button>

{/* Danger */}
<button className={getButtonClasses('danger')}>
  Delete Post
</button>

{/* Disabled */}
<button className={getButtonClasses('primary', true)} disabled>
  Publishing...
</button>

{/* Small variant */}
<button className={getButtonClasses('primary', false, true)}>
  Quick Action
</button>
```

### Forms
```tsx
<div className="space-y-4">
  {/* Label */}
  <label className={`${theme.forms.label.base} ${theme.forms.label.color} ${theme.forms.label.size}`}>
    Post Title
  </label>

  {/* Input */}
  <input
    type="text"
    className={`${theme.forms.input.base} ${theme.forms.input.colors} ${theme.forms.input.focus}`}
    placeholder="Enter your post title"
  />

  {/* Helper text */}
  <p className={`${theme.forms.helper.base} ${theme.forms.helper.color} ${theme.forms.helper.size}`}>
    This will be displayed as the main heading
  </p>

  {/* Error state */}
  <input
    type="text"
    className={`${theme.forms.input.base} ${theme.forms.input.colors} ${theme.forms.input.error}`}
  />
  <p className={`${theme.forms.error.base} ${theme.forms.error.color} ${theme.forms.error.size}`}>
    Title is required
  </p>
</div>
```

### Cards
```tsx
{/* Standard card */}
<div className={`${theme.cards.base.container} ${theme.cards.base.background} ${theme.cards.base.border} ${theme.cards.base.padding}`}>
  <h3>Card Title</h3>
  <p>Card content</p>
</div>

{/* Interactive/clickable card */}
<button className={`${theme.cards.interactive.container} ${theme.cards.interactive.background} ${theme.cards.interactive.border} ${theme.cards.interactive.hover} ${theme.cards.interactive.padding}`}>
  <h3>Clickable Card</h3>
</button>

{/* Feature card with overlay */}
<div className={theme.cards.feature.container}>
  <div className={theme.backgrounds.overlays.gold}></div>
  <div className={`relative ${theme.cards.feature.padding}`}>
    <h3>Feature Title</h3>
    <p>Feature description</p>
  </div>
</div>
```

### Alerts
```tsx
{/* Success */}
<div className={getAlertClasses('success')}>
  Post published successfully!
</div>

{/* Warning */}
<div className={getAlertClasses('warning')}>
  Your subscription expires in 3 days
</div>

{/* Error */}
<div className={getAlertClasses('error')}>
  Failed to connect to Instagram
</div>

{/* Info */}
<div className={getAlertClasses('info')}>
  New features are available
</div>
```

### Badges
```tsx
{/* Gold badge - Premium/New/Featured */}
<span className={getBadgeClasses('gold')}>
  NEW
</span>

{/* Cobalt badge - Active/Verified */}
<span className={getBadgeClasses('cobalt')}>
  VERIFIED
</span>

{/* Royal badge - Premium tier */}
<span className={getBadgeClasses('royal')}>
  PRO
</span>

{/* Gray badge - Disabled/Coming Soon */}
<span className={getBadgeClasses('gray')}>
  COMING SOON
</span>

{/* Status dot */}
<span className={`${theme.badges.dot.base} ${theme.badges.dot.colors.active}`}></span>
```

### Progress Bar
```tsx
<div className={`${theme.progress.bar.container} ${theme.progress.bar.background}`}>
  <div
    className={theme.progress.bar.fill}
    style={{ width: '75%' }}
  />
</div>
```

### Loading Spinner
```tsx
{/* Medium spinner */}
<div className={`${theme.progress.spinner.base} ${theme.progress.spinner.colors} ${theme.progress.spinner.sizes.md}`}></div>

{/* Large spinner */}
<div className={`${theme.progress.spinner.base} ${theme.progress.spinner.colors} ${theme.progress.spinner.sizes.lg}`}></div>
```

### Links
```tsx
{/* Primary link */}
<a href="#" className={`${theme.links.primary.base} ${theme.links.primary.colors}`}>
  Learn more
</a>

{/* Secondary link */}
<a href="#" className={`${theme.links.secondary.base} ${theme.links.secondary.colors}`}>
  View documentation
</a>

{/* Subtle link */}
<a href="#" className={`${theme.links.subtle.base} ${theme.links.subtle.colors}`}>
  Terms of Service
</a>
```

---

## 🎯 Quick Reference

### Component Color Mapping

| Component | Color | Meaning |
|-----------|-------|---------|
| Primary Button | Gold Gradient | Achievement, Action |
| Secondary Button | Cobalt-Royal Gradient | Trust, Professionalism |
| Success Alert | Gold | Achievement Complete |
| Warning Alert | Gold-Intense | Needs Attention |
| Error Alert | Red | Critical Issue |
| Info Alert | Cobalt | Helpful Information |
| Progress Bar | Cobalt-Royal | Ongoing Progress |
| Active Status | Gold (pulsing) | Currently Active |
| Premium Badge | Gold | Premium Feature |
| Verified Badge | Cobalt | Verified/Trusted |

### Color Psychology

**Gold** = Energy, achievement, warmth, sun, Orla
- Use for: CTAs, success, premium features, brand name
- Don't overuse: Loses impact if everywhere

**Cobalt** = Trust, professionalism, stability
- Use for: Secondary actions, info messages, progress
- Pairs well with: Gold, Royal, White

**Royal** = Sophistication, authority, premium
- Use for: Premium tiers, important sections
- Pairs well with: Cobalt, Gold

**White** = Clarity, innovation, transparency
- Use for: Text, headings, borders
- Primary readable color

**Slate** = Authority, elegance, professionalism
- Use for: Backgrounds, containers
- Creates depth

**Red** = Urgency, danger, critical
- Use for: Errors, destructive actions only
- Use sparingly

---

## ✅ Do's and Don'ts

### ✅ DO
- Use gold for primary CTAs and the brand name
- Maintain clear visual hierarchy
- Use semantic colors (gold = success, red = error)
- Keep body text readable (gray-300/400)
- Use brand gradients for visual interest
- Provide clear button hierarchy

### ❌ DON'T
- Don't use colors outside the brand palette
- Don't make everything gold (loses impact)
- Don't use red for anything except errors/danger
- Don't use low-contrast text
- Don't mix too many gradients in one view
- Don't use bright colors for body text

---

## 🚀 Migration from Old Styles

### Before (Old Code)
```tsx
<button className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
  Submit
</button>
```

### After (New Theme)
```tsx
<button className={getButtonClasses('primary')}>
  Submit
</button>
```

---

## 📚 Resources

- **Brand Colors**: See `tailwind.config.ts` for exact color values
- **Theme Object**: Import from `@/lib/theme`
- **Utility Functions**: `getButtonClasses()`, `getAlertClasses()`, `getBadgeClasses()`

---

## 🎨 Design Principles

1. **Hierarchy First**: Users should instantly know what's important
2. **Gold = Achievement**: Use gold to represent success and action
3. **Trust Through Blue**: Cobalt/Royal = professionalism
4. **Clarity Always**: White text, clear contrast, readable
5. **Consistency Wins**: Same components = same colors
6. **Brand Everywhere**: Every interaction reinforces ORLA³ brand

---

*Built with the ORLA³ Marketing Suite Design System*
*"Empowerment through clarity"*

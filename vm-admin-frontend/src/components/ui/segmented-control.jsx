import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function SegmentedControl({ options, value, onChange, className }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  return (
    <div
      className={cn(
        'flex p-1 rounded-lg bg-background border border-border',
        className
      )}
    >
      {options.map((option, index) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          onMouseEnter={() => setHoveredIndex(index)}
          onMouseLeave={() => setHoveredIndex(null)}
          className={cn(
            'relative flex-1 py-2 px-3 text-sm font-medium transition-all duration-200 rounded-md',
            value === option.value
              ? 'text-primary'
              : 'text-foreground/60 hover:text-foreground'
          )}
        >
          {value === option.value && (
            <motion.div
              layoutId="segment-active"
              className="absolute inset-0 bg-primary/10 rounded-md"
              transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
            />
          )}
          {hoveredIndex === index && value !== option.value && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-foreground/5 rounded-md"
            />
          )}
          <span className="relative z-10">{option.label}</span>
        </button>
      ))}
    </div>
  );
}

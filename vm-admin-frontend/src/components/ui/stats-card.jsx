import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function StatsCard({ 
  title, 
  value, 
  icon, 
  trend, 
  trendUp,
  color = 'teal',
  delay = 0 
}) {
  const IconComponent = icon;
  
  const colors = {
    teal: 'from-primary/20 to-primary/5 text-primary',
    blue: 'from-blue-500/20 to-blue-500/5 text-blue-500',
    amber: 'from-amber-500/20 to-amber-500/5 text-amber-500',
    slate: 'from-foreground/20 to-foreground/5 text-foreground/70',
    red: 'from-red-500/20 to-red-500/5 text-red-500',
  };

  const borderColors = {
    teal: 'group-hover:border-primary/30',
    blue: 'group-hover:border-blue-500/30',
    amber: 'group-hover:border-amber-500/30',
    slate: 'group-hover:border-foreground/30',
    red: 'group-hover:border-red-500/30',
  };

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-xl border border-border',
        'bg-gradient-to-br from-card to-transparent',
        'backdrop-blur-md transition-all duration-300',
        'hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/5',
        borderColors[color]
      )}
    >
      <div className={cn('absolute top-0 left-0 w-full h-1 bg-gradient-to-r', colors[color])} />
      
      <div className="relative p-5">
        <div className="flex items-start justify-between mb-4">
          <div className={cn('p-2.5 rounded-lg bg-gradient-to-br', colors[color])}>
            <IconComponent className="w-5 h-5" />
          </div>
          {trend !== undefined && trend !== 0 && (
            <div className={cn(
              'flex items-center gap-1 text-xs font-medium',
              trendUp ? 'text-primary' : 'text-red-500'
            )}>
              {trendUp ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {Math.abs(trend)}%
            </div>
          )}
        </div>
        
        <div className="space-y-1">
          <p className="text-2xl font-bold text-foreground font-mono tracking-tight">
            {value}
          </p>
          <p className="text-xs text-foreground/60 font-medium uppercase tracking-wider">
            {title}
          </p>
        </div>
      </div>
      
      <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    </div>
  );
}

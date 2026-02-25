import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export function StatusBadge({ status, className }) {
  const config = {
    Running: {
      bg: 'bg-[#24ab94]/20',
      text: 'text-[#24ab94]',
      border: 'border-[#24ab94]/30',
      dot: 'bg-[#24ab94]',
      pulse: true,
    },
    Stopped: {
      bg: 'bg-[#bdccd4]/10',
      text: 'text-[#bdccd4]/70',
      border: 'border-[#bdccd4]/20',
      dot: 'bg-[#bdccd4]/50',
      pulse: false,
    },
    Provisioning: {
      bg: 'bg-amber-500/20',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      dot: 'bg-amber-400',
      pulse: true,
    },
  };

  const style = config[status] || config.Stopped;

  return (
    <Badge
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 border font-medium',
        style.bg,
        style.text,
        style.border,
        className
      )}
    >
      <span className={cn('relative flex h-2 w-2', style.pulse && 'pulse-dot')}>
        {style.pulse && (
          <span
            className={cn(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              style.dot
            )}
          />
        )}
        <span className={cn('relative inline-flex rounded-full h-2 w-2', style.dot)} />
      </span>
      {status}
    </Badge>
  );
}

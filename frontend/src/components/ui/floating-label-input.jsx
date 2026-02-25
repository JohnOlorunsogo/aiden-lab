import { cn } from '@/lib/utils';

export function FloatingLabelInput({
  id,
  label,
  value,
  onChange,
  type = 'text',
  min,
  max,
  className,
  helperText,
  ...props
}) {
  const isActive = value !== '' && value !== undefined;

  return (
    <div className={cn('relative', className)}>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        min={min}
        max={max}
        placeholder=" "
        className={cn(
          'peer w-full px-3 pt-6 pb-2 bg-[#010311] border border-[#bdccd4]/20 rounded-lg',
          'text-[#bdccd4] text-sm placeholder:text-transparent',
          'focus:outline-none focus:border-[#24ab94] focus:ring-1 focus:ring-[#24ab94]/20',
          'transition-all duration-200'
        )}
        {...props}
      />
      <label
        htmlFor={id}
        className={cn(
          'absolute left-3 text-[#bdccd4]/50 text-sm transition-all duration-200 pointer-events-none',
          'peer-placeholder-shown:top-1/2 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:text-base',
          'peer-focus:top-2 peer-focus:-translate-y-0 peer-focus:text-xs peer-focus:text-[#24ab94]',
          isActive ? 'top-2 -translate-y-0 text-xs text-[#24ab94]' : ''
        )}
      >
        {label}
      </label>
      {helperText && (
        <p className="mt-1 text-xs text-[#bdccd4]/40">{helperText}</p>
      )}
    </div>
  );
}

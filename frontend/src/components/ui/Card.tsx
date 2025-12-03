import { cn } from '@/lib/utils'
import type { ReactNode, CSSProperties } from 'react'
import { AnimatedNumber } from './AnimatedNumber'

interface CardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  style?: CSSProperties
}

export function Card({ children, className, hover = true, style }: CardProps) {
  return (
    <div
      className={cn(
        'bg-content1 rounded-[14px] border border-white/5 transition-all duration-250',
        hover && 'hover:bg-[#1f1f23]',
        className
      )}
      style={style}
    >
      {children}
    </div>
  )
}

interface StatCardProps {
  icon: ReactNode
  iconClassName: string
  label: string
  value: string | number
  suffix?: string
  animate?: boolean
  decimals?: number  // 保留小数位数
}

export function StatCard({ icon, iconClassName, label, value, suffix, animate = true, decimals = 0 }: StatCardProps) {
  const numericValue = typeof value === 'number' ? value : parseFloat(value.toString().replace(/,/g, ''))
  const isNumeric = !isNaN(numericValue)

  return (
    <div className="relative overflow-hidden rounded-[14px] border border-white/5 bg-gradient-to-br from-content1 to-[#1a1a1f] p-5 flex flex-col">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      <div className="flex items-center gap-3 mb-3">
        <div className={cn('w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0', iconClassName)}>
          {icon}
        </div>
        <span className="text-sm text-zinc-400">{label}</span>
      </div>
      <div className="mt-auto">
        <p className="text-3xl font-bold">
          {animate && isNumeric ? (
            <AnimatedNumber value={numericValue} decimals={decimals} />
          ) : (
            value
          )}
        </p>
        {suffix ? (
          <p className="text-xs text-zinc-500 mt-1">{suffix}</p>
        ) : (
          <p className="text-xs text-zinc-500 mt-1 invisible">占位</p>
        )}
      </div>
    </div>
  )
}

import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // AI 工程学习主题 · 浅色基调
        // 灵蓝(主色 brand): 方法/运行资源 → sky(天蓝/水蓝)
        brand: {
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#0EA5E9',
          600: '#0284C7',
          700: '#0369A1',
          800: '#075985',
          900: '#0C4A6E',
        },
        // 赤金(经验 exp): 学习进度/奖励 → amber
        exp: {
          50: '#FEF9E7',
          100: '#FDF0C4',
          200: '#FBE18A',
          300: '#F8CB4E',
          400: '#F5B324',
          500: '#E9970B',
          600: '#C97407',
          700: '#A1520A',
          800: '#84400E',
          900: '#70350F',
        },
        // 玄紫(点缀 accent): 高阶/神秘 → violet
        accent: {
          50: '#F3EFFC',
          100: '#E9E2FA',
          200: '#D4C6F5',
          300: '#B79FEE',
          400: '#9A72E4',
          500: '#7F4DD6',
          600: '#6933BC',
          700: '#55289A',
          800: '#43227A',
          900: '#381F63',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-brand': '0 0 24px rgba(14, 165, 233, 0.28), 0 4px 16px rgba(14, 165, 233, 0.12)',
        'glow-exp': '0 0 24px rgba(233, 151, 11, 0.28), 0 4px 16px rgba(233, 151, 11, 0.12)',
        'glow-accent': '0 0 24px rgba(127, 77, 214, 0.26), 0 4px 16px rgba(127, 77, 214, 0.12)',
        card: '0 1px 3px rgba(16, 42, 67, 0.06), 0 8px 24px rgba(16, 42, 67, 0.06)',
        'card-hover':
          '0 4px 12px rgba(16, 42, 67, 0.08), 0 16px 40px rgba(14, 165, 233, 0.12), 0 0 0 1px rgba(14, 165, 233, 0.25)',
        soft: '0 2px 8px rgba(16, 42, 67, 0.05)',
      },
      backgroundImage: {
        'grid-light':
          'linear-gradient(rgba(14,165,233,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(14,165,233,0.05) 1px, transparent 1px)',
        'gradient-brand': 'linear-gradient(135deg, #0EA5E9 0%, #38BDF8 55%, #7DD3FC 100%)',
        'gradient-exp': 'linear-gradient(135deg, #E9970B 0%, #F5B324 55%, #F8CB4E 100%)',
        'gradient-accent': 'linear-gradient(135deg, #7F4DD6 0%, #9A72E4 55%, #B79FEE 100%)',
        'gradient-text-hero': 'linear-gradient(120deg, #0284C7 0%, #0EA5E9 40%, #E9970B 100%)',
        'mesh-light':
          'radial-gradient(ellipse 60% 45% at 15% 0%, rgba(14,165,233,0.10), transparent), radial-gradient(ellipse 55% 45% at 85% 15%, rgba(127,77,214,0.08), transparent), radial-gradient(ellipse 50% 40% at 50% 90%, rgba(233,151,11,0.07), transparent)',
      },
      backgroundSize: {
        grid: '44px 44px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.35s ease-out',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) both',
        'slide-in-left': 'slideInLeft 0.5s cubic-bezier(0.22, 1, 0.36, 1) both',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) both',
        float: 'float 6s ease-in-out infinite',
        'float-slow': 'float 9s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2.6s ease-in-out infinite',
        shimmer: 'shimmer 2.5s linear infinite',
        'spin-slow': 'spin 14s linear infinite',
        wiggle: 'wiggle 2.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-14px)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(14,165,233,0.25)' },
          '50%': { boxShadow: '0 0 40px rgba(14,165,233,0.5)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-4deg)' },
          '50%': { transform: 'rotate(4deg)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config

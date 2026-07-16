// Be.カラフル 公式ロゴ（logo-224.png）
import logoUrl from '../assets/logo-224.png'

export function Logo({ className = 'h-10' }: { className?: string }) {
  return <img src={logoUrl} alt="一般社団法人 Be.カラフル" className={`${className} w-auto`} />
}

export interface HeroSectionProps { title?: string; children?: React.ReactNode }
export function HeroSection({ title, children }: HeroSectionProps) {
  return <section className="bg-[#2A5C82] text-white py-20 px-6 text-center"><h2 className="text-2xl font-bold mb-4">{title ?? 'HeroSection'}</h2>{children}</section>;
}

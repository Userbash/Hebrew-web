export interface FeatureCardsProps { title?: string; children?: React.ReactNode }
export function FeatureCards({ title, children }: FeatureCardsProps) {
  return <section className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6"><h2 className="text-2xl font-bold mb-4">{title ?? 'FeatureCards'}</h2>{children}</section>;
}

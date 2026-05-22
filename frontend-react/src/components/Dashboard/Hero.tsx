import { CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export default function Hero() {
  const { t } = useLanguage();

  return (
    <section className="app-hero">
      <div>
        <span className="app-status">
          <CheckCircle2 size={16} /> {t.systemOnline}
        </span>
        <h2>{t.dayReadyTitle}</h2>
        <p>{t.dayReadyDesc}</p>
      </div>
      <button className="app-primary-action">{t.continueLesson}</button>
    </section>
  );
}

import { CheckCircle2 } from 'lucide-react';

export default function Hero() {
  return (
    <section className="app-hero">
      <div>
        <span className="app-status">
          <CheckCircle2 size={16} /> Система работает
        </span>
        <h2>Ваш учебный день готов</h2>
        <p>3 коротких упражнения и один словарный повтор помогут сохранить темп без перегрузки.</p>
      </div>
      <button className="app-primary-action">Продолжить урок</button>
    </section>
  );
}

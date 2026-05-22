import { useLanguage } from '../../context/LanguageContext';

export default function HealthPanel() {
  const { t } = useLanguage();

  return (
    <div className="app-panel health-panel">
      <div className="app-panel-header">
        <h3>{t.envStatusTitle}</h3>
        <span>{t.updatedNow}</span>
      </div>
      <div className="health-content">
        <div className="health-ring" aria-label="90 percent system health">
          <span>90%</span>
        </div>
        <div>
          <h4>{t.stable}</h4>
          <p>{t.stableDesc}</p>
        </div>
      </div>
    </div>
  );
}

import { Clock3 } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

interface ActivityItemProps {
  title: string;
  time: string;
  result: string;
}

function ActivityItem({ title, time, result }: ActivityItemProps) {
  return (
    <div className="activity-item">
      <div className="activity-icon">
        <Clock3 size={16} />
      </div>
      <div>
        <strong>{title}</strong>
        <span>{time}</span>
      </div>
      <em>{result}</em>
    </div>
  );
}

export default function ActivityPanel() {
  const { t } = useLanguage();

  return (
    <div className="app-panel">
      <div className="app-panel-header">
        <h3>{t.recentActions}</h3>
        <button>{t.all}</button>
      </div>
      <div className="activity-list">
        <ActivityItem title={t.activity1Title} time={t.twoHoursAgo} result="+250 XP" />
        <ActivityItem title={t.activity2Title} time={t.yesterday} result="+120 XP" />
        <ActivityItem title={t.activity3Title} time={t.threeDaysAgo} result="+400 XP" />
      </div>
    </div>
  );
}

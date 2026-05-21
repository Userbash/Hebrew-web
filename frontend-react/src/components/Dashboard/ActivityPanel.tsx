import { Clock3 } from 'lucide-react';

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
  return (
    <div className="app-panel">
      <div className="app-panel-header">
        <h3>Последние действия</h3>
        <button>Все</button>
      </div>
      <div className="activity-list">
        <ActivityItem title="Урок: базовая грамматика" time="2 часа назад" result="+250 XP" />
        <ActivityItem title="Повтор: современная лексика" time="Вчера" result="+120 XP" />
        <ActivityItem title="Тест: технические термины" time="3 дня назад" result="+400 XP" />
      </div>
    </div>
  );
}

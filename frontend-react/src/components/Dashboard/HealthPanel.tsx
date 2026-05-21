export default function HealthPanel() {
  return (
    <div className="app-panel health-panel">
      <div className="app-panel-header">
        <h3>Состояние среды</h3>
        <span>Обновлено сейчас</span>
      </div>
      <div className="health-content">
        <div className="health-ring" aria-label="90 процентов здоровья системы">
          <span>90%</span>
        </div>
        <div>
          <h4>Стабильно</h4>
          <p>API, база данных и учебные сервисы отвечают в пределах нормы.</p>
        </div>
      </div>
    </div>
  );
}

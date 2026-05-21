import type { ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  note: string;
}

export default function StatCard({ icon, label, value, note }: StatCardProps) {
  return (
    <div className="app-stat-card">
      <div className="app-stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
    </div>
  );
}

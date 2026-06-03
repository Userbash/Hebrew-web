export interface UserTableProps {
  title?: string;
}

export function UserTable({ title }: UserTableProps) {
  const students = [
    { name: 'Sarah L.', score: 980, progress: 'Advanced', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah' },
    { name: 'David M.', score: 945, progress: 'Intermediate', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=David' },
    { name: 'Elena R.', score: 910, progress: 'Beginner', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Elena' }
  ];

  return (
    <div className="performers-table">
      {title && <h3 className="performers-table__title">{title}</h3>}
      <div className="performers-table__scroll">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Level</th>
              <th className="is-right">Points</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s, i) => (
              <tr key={i}>
                <td>
                  <span className="performers-table__student">
                    <img src={s.avatar} alt="" />
                    <span>{s.name}</span>
                  </span>
                </td>
                <td>
                  <span className="performers-table__level">{s.progress}</span>
                </td>
                <td className="is-right">{s.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

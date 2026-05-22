interface AccessDeniedProps {
  message?: string;
}

export default function AccessDenied({ message = 'Access denied' }: AccessDeniedProps) {
  return (
    <div className="site-wrap">
      <div className="site-card">
        <h2>Access Denied</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Form,
  InputGroup,
  Modal,
  Nav,
  Row,
  Spinner,
  Tab,
  Table,
} from 'react-bootstrap';
import { Navigate } from 'react-router-dom';
import { useAuth, type RoleKey } from '../../context/AuthContext';
import { accessApi, type UserRoleAssignment } from '../../api/access';
import { adminUsersApi, type AdminUser, type AdminUsersListParams, type UserSession } from '../../api/adminUsers';
import { publicationsApi, type Publication } from '../../api/publications';
import './AdminPanel.css';

const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];
const SEARCHABLE_RBAC_ROLES: RoleKey[] = [
  'root',
  'platform_admin',
  'security_admin',
  'content_admin',
  'editor',
  'moderator',
  'support',
  'analyst',
  'user',
];
const USER_SORT_OPTIONS: Array<{ value: NonNullable<AdminUsersListParams['sortBy']>; label: string }> = [
  { value: 'created_at', label: 'Created at' },
  { value: 'updated_at', label: 'Updated at' },
  { value: 'last_login', label: 'Last login' },
  { value: 'publication_count', label: 'Publications' },
  { value: 'xp_total', label: 'XP' },
  { value: 'level', label: 'Level' },
  { value: 'username', label: 'Username' },
  { value: 'email', label: 'Email' },
  { value: 'id', label: 'User ID' },
];

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  return new Date(value).toLocaleString();
};

const statusVariant = (status?: string) => {
  switch (status) {
    case 'published':
      return 'success';
    case 'archived':
      return 'secondary';
    case 'review':
      return 'warning';
    default:
      return 'info';
  }
};

export default function AdminPanel() {
  const { user, hasAnyRole } = useAuth();

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMessage, setOkMessage] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [rbacRoleFilter, setRbacRoleFilter] = useState('');
  const [permissionFilter, setPermissionFilter] = useState('');
  const [publicationStatusFilter, setPublicationStatusFilter] = useState('');
  const [publicationSearchFilter, setPublicationSearchFilter] = useState('');
  const [hasPublicationsFilter, setHasPublicationsFilter] = useState<'all' | 'yes' | 'no'>('all');
  const [blockedFilter, setBlockedFilter] = useState<'all' | 'blocked' | 'active'>('all');
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [sortBy, setSortBy] = useState<NonNullable<AdminUsersListParams['sortBy']>>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [selectedUserSessions, setSelectedUserSessions] = useState<UserSession[]>([]);
  const [showSessionsModal, setShowSessionsModal] = useState(false);

  const [catalog, setCatalog] = useState<Array<{ role: RoleKey; title: string; priority: number; summary: string; privileges: string[] }>>([]);
  const [selectedRole, setSelectedRole] = useState<RoleKey>('user');
  const [assignmentNote, setAssignmentNote] = useState('');
  const [userAssignments, setUserAssignments] = useState<UserRoleAssignment[]>([]);

  const [publications, setPublications] = useState<Publication[]>([]);
  const [publicationForm, setPublicationForm] = useState({
    title: '',
    description: '',
    status: 'draft',
    visibility: 'private' as 'private' | 'team' | 'public',
    tags: '',
  });

  const activeRoles = user?.access?.roleKeys || [];

  const reloadUsers = async () => {
    const hasPublications = hasPublicationsFilter === 'yes'
      ? true
      : hasPublicationsFilter === 'no'
        ? false
        : undefined;

    const isBlocked = blockedFilter === 'blocked'
      ? true
      : blockedFilter === 'active'
        ? false
        : undefined;

    const data = await adminUsersApi.list({
      page: 1,
      limit: 50,
      id: userIdFilter || undefined,
      search: search || undefined,
      role: roleFilter || undefined,
      rbacRole: rbacRoleFilter || undefined,
      permission: permissionFilter || undefined,
      publicationStatus: publicationStatusFilter || undefined,
      publicationSearch: publicationSearchFilter || undefined,
      hasPublications,
      includeDeleted,
      isBlocked,
      sortBy,
      sortOrder,
    });

    setUsers(data.users);
    setUsersTotal(data.pagination.total);

    if (data.users.length > 0 && !selectedUser) {
      setSelectedUser(data.users[0]);
    }
  };

  const reloadCatalog = async () => {
    const data = await accessApi.getCatalog();
    setCatalog(data.hierarchy || []);
    if (data.hierarchy?.length > 0) {
      setSelectedRole(data.hierarchy[data.hierarchy.length - 1].role);
    }
  };

  const reloadPublications = async () => {
    const data = await publicationsApi.list();
    setPublications(data.publications || []);
  };

  const loadInitial = async () => {
    setBusy(true);
    setError(null);

    try {
      await Promise.all([reloadUsers(), reloadCatalog(), reloadPublications()]);
    } catch (loadError) {
      setError((loadError as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Failed to load admin data');
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!hasAnyRole(ADMIN_ROLES)) {
      return;
    }

    const timer = window.setTimeout(() => {
      void loadInitial();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasAnyRole]);

  const availableRoles = useMemo(() => catalog.map((item) => item.role), [catalog]);

  if (!hasAnyRole(ADMIN_ROLES)) {
    return <Navigate to="/dashboard" replace />;
  }

  const withAction = async (action: () => Promise<void>, successMessage: string) => {
    setBusy(true);
    setError(null);
    setOkMessage(null);

    try {
      await action();
      setOkMessage(successMessage);
    } catch (actionError) {
      setError((actionError as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const assignRole = async () => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.assignRole(selectedUser.id, selectedRole, assignmentNote || undefined, null);
      const assignmentData = await accessApi.getUserAccess(selectedUser.id);
      setUserAssignments(assignmentData.assignments);
      setAssignmentNote('');
    }, `Role ${selectedRole} assigned to ${selectedUser.username}`);
  };

  const revokeRole = async () => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.revokeRole(selectedUser.id, selectedRole, assignmentNote || undefined);
      const assignmentData = await accessApi.getUserAccess(selectedUser.id);
      setUserAssignments(assignmentData.assignments);
      setAssignmentNote('');
    }, `Role ${selectedRole} revoked from ${selectedUser.username}`);
  };

  const toggleBlock = async () => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.setBlockedState(selectedUser.id, true, assignmentNote || 'Blocked from admin panel');
      const assignmentData = await accessApi.getUserAccess(selectedUser.id);
      setUserAssignments(assignmentData.assignments);
      setAssignmentNote('');
    }, `${selectedUser.username} has been blocked`);
  };

  const loadAssignments = async (userId: string) => {
    await withAction(async () => {
      const assignmentData = await accessApi.getUserAccess(userId);
      setUserAssignments(assignmentData.assignments);
    }, 'User permissions loaded');
  };

  const loadSessions = async (userId: string) => {
    await withAction(async () => {
      const sessionData = await adminUsersApi.sessions(userId);
      setSelectedUserSessions(sessionData.sessions || []);
      setShowSessionsModal(true);
    }, 'User sessions loaded');
  };

  const updateUser = async (userToUpdate: AdminUser) => {
    await withAction(async () => {
      await adminUsersApi.update(userToUpdate.id, {
        first_name: userToUpdate.first_name,
        last_name: userToUpdate.last_name,
        username: userToUpdate.username,
        email: userToUpdate.email,
        xp_total: userToUpdate.xp_total,
        level: userToUpdate.level,
      });
      await reloadUsers();
    }, `${userToUpdate.username} updated`);
  };

  const softDeleteUser = async (userId: string) => {
    await withAction(async () => {
      await adminUsersApi.softDelete(userId);
      await reloadUsers();
    }, 'User soft-deleted');
  };

  const restoreUser = async (userId: string) => {
    await withAction(async () => {
      await adminUsersApi.restore(userId);
      await reloadUsers();
    }, 'User restored');
  };

  const createPublication = async () => {
    if (!publicationForm.title.trim()) {
      setError('Publication title is required');
      return;
    }

    await withAction(async () => {
      await publicationsApi.create({
        title: publicationForm.title,
        description: publicationForm.description,
        status: publicationForm.status,
        visibility: publicationForm.visibility,
        tags: publicationForm.tags.split(',').map((item) => item.trim()).filter(Boolean),
      });

      setPublicationForm({
        title: '',
        description: '',
        status: 'draft',
        visibility: 'private',
        tags: '',
      });

      await reloadPublications();
    }, 'Publication created');
  };

  const updatePublicationStatus = async (publicationId: string, status: string) => {
    await withAction(async () => {
      await publicationsApi.update(publicationId, { status });
      await reloadPublications();
    }, `Publication status changed to ${status}`);
  };

  const deletePublication = async (publicationId: string) => {
    await withAction(async () => {
      await publicationsApi.remove(publicationId);
      await reloadPublications();
    }, 'Publication deleted');
  };

  return (
    <div className="admin-console py-4 py-lg-5">
      <div className="container-xl">
        <Card className="admin-toolbar text-light p-4 mb-4">
          <Row className="align-items-center g-4">
            <Col lg={8}>
              <h1 className="mb-2 fw-bold">Advanced Administration Console</h1>
              <p className="mb-0 text-secondary">Users, permissions, publications, and full operational governance.</p>
            </Col>
            <Col lg={4} className="text-lg-end">
              <Badge className="badge-soft me-2">Operator: {user?.email}</Badge>
              <Badge className="badge-soft">Roles: {activeRoles.join(', ') || 'none'}</Badge>
            </Col>
          </Row>
        </Card>

        <Row className="g-3 mb-4">
          <Col md={4}><Card body className="admin-kpi"><h6 className="text-secondary">Users</h6><h3>{usersTotal}</h3></Card></Col>
          <Col md={4}><Card body className="admin-kpi"><h6 className="text-secondary">Roles</h6><h3>{catalog.length}</h3></Card></Col>
          <Col md={4}><Card body className="admin-kpi"><h6 className="text-secondary">Publications</h6><h3>{publications.length}</h3></Card></Col>
        </Row>

        {error && <Alert variant="danger">{error}</Alert>}
        {okMessage && <Alert variant="success">{okMessage}</Alert>}

        <Tab.Container defaultActiveKey="users">
          <Card className="admin-panel">
            <Card.Header>
              <Nav variant="tabs" className="border-0">
                <Nav.Item><Nav.Link eventKey="users">Users</Nav.Link></Nav.Item>
                <Nav.Item><Nav.Link eventKey="access">Permissions & Roles</Nav.Link></Nav.Item>
                <Nav.Item><Nav.Link eventKey="publications">Publications</Nav.Link></Nav.Item>
              </Nav>
            </Card.Header>
            <Card.Body>
              {busy && (
                <div className="d-flex align-items-center gap-2 mb-3 text-secondary">
                  <Spinner animation="border" size="sm" /> Processing...
                </div>
              )}

              <Tab.Content>
                <Tab.Pane eventKey="users">
                  <Row className="g-3 mb-3">
                    <Col lg={4}>
                      <InputGroup>
                        <InputGroup.Text>Search</InputGroup.Text>
                        <Form.Control
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                          placeholder="email / username / first / last name"
                        />
                      </InputGroup>
                    </Col>
                    <Col lg={4}>
                      <InputGroup>
                        <InputGroup.Text>User ID</InputGroup.Text>
                        <Form.Control
                          value={userIdFilter}
                          onChange={(e) => setUserIdFilter(e.target.value)}
                          placeholder="exact UUID"
                        />
                      </InputGroup>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
                        <option value="">Legacy role</option>
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                        <option value="moderator">moderator</option>
                      </Form.Select>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={rbacRoleFilter} onChange={(e) => setRbacRoleFilter(e.target.value)}>
                        <option value="">RBAC role</option>
                        {SEARCHABLE_RBAC_ROLES.map((role) => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                      </Form.Select>
                    </Col>
                  </Row>

                  <Row className="g-3 mb-3">
                    <Col lg={3}>
                      <InputGroup>
                        <InputGroup.Text>Permission</InputGroup.Text>
                        <Form.Control
                          value={permissionFilter}
                          onChange={(e) => setPermissionFilter(e.target.value)}
                          placeholder="users.read.any"
                        />
                      </InputGroup>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={publicationStatusFilter} onChange={(e) => setPublicationStatusFilter(e.target.value)}>
                        <option value="">Pub status</option>
                        <option value="draft">draft</option>
                        <option value="review">review</option>
                        <option value="published">published</option>
                        <option value="archived">archived</option>
                      </Form.Select>
                    </Col>
                    <Col lg={3}>
                      <InputGroup>
                        <InputGroup.Text>Pub search</InputGroup.Text>
                        <Form.Control
                          value={publicationSearchFilter}
                          onChange={(e) => setPublicationSearchFilter(e.target.value)}
                          placeholder="publication title / description"
                        />
                      </InputGroup>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={hasPublicationsFilter} onChange={(e) => setHasPublicationsFilter(e.target.value as 'all' | 'yes' | 'no')}>
                        <option value="all">Any publication count</option>
                        <option value="yes">Has publications</option>
                        <option value="no">No publications</option>
                      </Form.Select>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={blockedFilter} onChange={(e) => setBlockedFilter(e.target.value as 'all' | 'blocked' | 'active')}>
                        <option value="all">Block state</option>
                        <option value="blocked">Blocked</option>
                        <option value="active">Not blocked</option>
                      </Form.Select>
                    </Col>
                  </Row>

                  <Row className="g-3 mb-3 align-items-center">
                    <Col lg={3}>
                      <Form.Select value={sortBy} onChange={(e) => setSortBy(e.target.value as NonNullable<AdminUsersListParams['sortBy']>)}>
                        {USER_SORT_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </Form.Select>
                    </Col>
                    <Col lg={2}>
                      <Form.Select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}>
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                      </Form.Select>
                    </Col>
                    <Col lg={2}>
                      <Form.Check checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.target.checked)} label="Include deleted" />
                    </Col>
                    <Col lg={5} className="text-lg-end">
                      <Button variant="outline-light" onClick={() => void withAction(reloadUsers, 'Advanced user search refreshed')}>Run Search</Button>
                    </Col>
                  </Row>

                  <Card className="admin-kpi mb-3">
                    <Card.Body className="small text-secondary">
                      Quick search fields: `id`, email, username, first/last name, RBAC role key, permission key (`resource.action.scope`),
                      publication status/title, blocked state, deleted state, publication presence, and sort by activity or content volume.
                    </Card.Body>
                  </Card>

                  <div className="table-responsive">
                    <Table hover>
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Legacy</th>
                          <th>RBAC Roles</th>
                          <th>Perms</th>
                          <th>Pubs</th>
                          <th>Last Login</th>
                          <th>Status</th>
                          <th className="text-end">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((item) => (
                          <tr key={item.id}>
                            <td>
                              <div className="fw-semibold">{item.username}</div>
                              <div className="text-secondary small">{item.email}</div>
                              <div className="text-secondary small">{item.id}</div>
                            </td>
                            <td>{item.role}</td>
                            <td>{item.rbac_roles?.join(', ') || '—'}</td>
                            <td>{item.permission_count ?? 0}</td>
                            <td>
                              {item.publication_count ?? 0}
                              <span className="text-secondary small"> / published: {item.published_publication_count ?? 0}</span>
                            </td>
                            <td>{formatDate(item.last_login)}</td>
                            <td>
                              <div className="d-flex flex-column gap-1">
                                {item.deleted_at ? <Badge bg="danger">Deleted</Badge> : <Badge bg="success">Active</Badge>}
                                {item.is_system_blocked ? <Badge bg="warning">Blocked</Badge> : <Badge bg="info">Open</Badge>}
                              </div>
                            </td>
                            <td className="text-end">
                              <Button size="sm" variant="outline-light" className="me-2" onClick={() => { setSelectedUser(item); void loadAssignments(item.id); }}>Select</Button>
                              <Button size="sm" variant="outline-light" className="me-2" onClick={() => void loadSessions(item.id)}>Sessions</Button>
                              {!item.deleted_at && <Button size="sm" variant="outline-danger" onClick={() => void softDeleteUser(item.id)}>Delete</Button>}
                              {item.deleted_at && <Button size="sm" variant="outline-success" onClick={() => void restoreUser(item.id)}>Restore</Button>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>

                  {selectedUser && (
                    <Card className="admin-kpi mt-3">
                      <Card.Body>
                        <h6 className="mb-3">Edit User: {selectedUser.username}</h6>
                        <Row className="g-3">
                          <Col md={4}><Form.Control value={selectedUser.first_name || ''} placeholder="First name" onChange={(e) => setSelectedUser({ ...selectedUser, first_name: e.target.value })} /></Col>
                          <Col md={4}><Form.Control value={selectedUser.last_name || ''} placeholder="Last name" onChange={(e) => setSelectedUser({ ...selectedUser, last_name: e.target.value })} /></Col>
                          <Col md={4}><Form.Control value={selectedUser.email} placeholder="Email" onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })} /></Col>
                          <Col md={4}><Form.Control value={selectedUser.username} placeholder="Username" onChange={(e) => setSelectedUser({ ...selectedUser, username: e.target.value })} /></Col>
                          <Col md={4}><Form.Control type="number" value={selectedUser.xp_total} placeholder="XP" onChange={(e) => setSelectedUser({ ...selectedUser, xp_total: Number.parseInt(e.target.value || '0', 10) })} /></Col>
                          <Col md={4}><Form.Control type="number" value={selectedUser.level} placeholder="Level" onChange={(e) => setSelectedUser({ ...selectedUser, level: Number.parseInt(e.target.value || '1', 10) })} /></Col>
                        </Row>
                        <div className="mt-3 text-end">
                          <Button onClick={() => void updateUser(selectedUser)}>Save User</Button>
                        </div>
                      </Card.Body>
                    </Card>
                  )}
                </Tab.Pane>

                <Tab.Pane eventKey="access">
                  <Row className="g-3">
                    <Col lg={5}>
                      <Card className="admin-kpi h-100">
                        <Card.Body>
                          <h6 className="mb-3">Role Catalog</h6>
                          <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
                            {catalog.map((role) => (
                              <div key={role.role} className="mb-3 p-3 border rounded border-secondary-subtle">
                                <div className="d-flex justify-content-between align-items-center">
                                  <strong>{role.title}</strong>
                                  <Badge bg="primary">{role.priority}</Badge>
                                </div>
                                <div className="small text-secondary mt-2">{role.summary}</div>
                                <div className="small mt-2">{role.privileges.join(' • ')}</div>
                              </div>
                            ))}
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>

                    <Col lg={7}>
                      <Card className="admin-kpi mb-3">
                        <Card.Body>
                          <h6 className="mb-3">Assignment Control</h6>
                          <Row className="g-3">
                            <Col md={6}>
                              <Form.Select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value as RoleKey)}>
                                {(availableRoles.length > 0 ? availableRoles : ADMIN_ROLES).map((role) => (
                                  <option key={role} value={role}>{role}</option>
                                ))}
                              </Form.Select>
                            </Col>
                            <Col md={6}>
                              <Form.Control value={assignmentNote} onChange={(e) => setAssignmentNote(e.target.value)} placeholder="Audit note" />
                            </Col>
                          </Row>
                          <div className="mt-3 d-flex gap-2 justify-content-end flex-wrap">
                            <Button variant="outline-light" disabled={!selectedUser} onClick={() => selectedUser && void loadAssignments(selectedUser.id)}>Load User Access</Button>
                            <Button variant="success" disabled={!selectedUser} onClick={() => void assignRole()}>Assign Role</Button>
                            <Button variant="warning" disabled={!selectedUser} onClick={() => void revokeRole()}>Revoke Role</Button>
                            <Button variant="danger" disabled={!selectedUser} onClick={() => void toggleBlock()}>Block User</Button>
                          </div>
                        </Card.Body>
                      </Card>

                      <Card className="admin-kpi">
                        <Card.Body>
                          <h6 className="mb-3">Current Assignments {selectedUser ? `for ${selectedUser.username}` : ''}</h6>
                          {userAssignments.length === 0 && <p className="text-secondary mb-0">No assignments loaded.</p>}
                          {userAssignments.length > 0 && (
                            <Table size="sm" hover>
                              <thead>
                                <tr>
                                  <th>Role</th>
                                  <th>Priority</th>
                                  <th>Active</th>
                                  <th>Assigned</th>
                                  <th>Note</th>
                                </tr>
                              </thead>
                              <tbody>
                                {userAssignments.map((assignment) => (
                                  <tr key={assignment.id}>
                                    <td>{assignment.role_key}</td>
                                    <td>{assignment.priority}</td>
                                    <td>{assignment.is_active ? 'yes' : 'no'}</td>
                                    <td>{formatDate(assignment.assigned_at)}</td>
                                    <td>{assignment.note || '—'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </Table>
                          )}
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>
                </Tab.Pane>

                <Tab.Pane eventKey="publications">
                  <Row className="g-3 mb-3">
                    <Col lg={8}>
                      <Card className="admin-kpi h-100">
                        <Card.Body>
                          <h6 className="mb-3">Create Publication</h6>
                          <Row className="g-3">
                            <Col md={6}><Form.Control value={publicationForm.title} placeholder="Title" onChange={(e) => setPublicationForm({ ...publicationForm, title: e.target.value })} /></Col>
                            <Col md={3}>
                              <Form.Select value={publicationForm.status} onChange={(e) => setPublicationForm({ ...publicationForm, status: e.target.value })}>
                                <option value="draft">draft</option>
                                <option value="review">review</option>
                                <option value="published">published</option>
                                <option value="archived">archived</option>
                              </Form.Select>
                            </Col>
                            <Col md={3}>
                              <Form.Select value={publicationForm.visibility} onChange={(e) => setPublicationForm({ ...publicationForm, visibility: e.target.value as 'private' | 'team' | 'public' })}>
                                <option value="private">private</option>
                                <option value="team">team</option>
                                <option value="public">public</option>
                              </Form.Select>
                            </Col>
                            <Col xs={12}><Form.Control value={publicationForm.tags} placeholder="Tags (comma-separated)" onChange={(e) => setPublicationForm({ ...publicationForm, tags: e.target.value })} /></Col>
                            <Col xs={12}><Form.Control as="textarea" rows={3} value={publicationForm.description} placeholder="Description" onChange={(e) => setPublicationForm({ ...publicationForm, description: e.target.value })} /></Col>
                          </Row>
                          <div className="mt-3 text-end">
                            <Button onClick={() => void createPublication()}>Create Publication</Button>
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col lg={4}>
                      <Card className="admin-kpi h-100">
                        <Card.Body>
                          <h6 className="mb-3">Publishing Features</h6>
                          <ul className="small text-secondary mb-0">
                            <li>Draft / Review / Published workflow</li>
                            <li>Visibility levels for internal and public releases</li>
                            <li>Tagging and searchable metadata model</li>
                            <li>Role-based moderation and delete controls</li>
                          </ul>
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>

                  <div className="table-responsive">
                    <Table hover>
                      <thead>
                        <tr>
                          <th>Title</th>
                          <th>Author</th>
                          <th>Status</th>
                          <th>Visibility</th>
                          <th>Updated</th>
                          <th className="text-end">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {publications.map((publication) => (
                          <tr key={publication.id}>
                            <td>
                              <div className="fw-semibold">{publication.name}</div>
                              <div className="small text-secondary">{publication.description || 'No description'}</div>
                            </td>
                            <td>{publication.metadata?.authorId || '—'}</td>
                            <td><Badge bg={statusVariant(publication.metadata?.status)}>{publication.metadata?.status || 'draft'}</Badge></td>
                            <td>{publication.metadata?.visibility || 'private'}</td>
                            <td>{formatDate(publication.updated_at)}</td>
                            <td className="text-end">
                              <Button size="sm" variant="outline-light" className="me-2" onClick={() => void updatePublicationStatus(publication.id, 'review')}>To Review</Button>
                              <Button size="sm" variant="outline-success" className="me-2" onClick={() => void updatePublicationStatus(publication.id, 'published')}>Publish</Button>
                              <Button size="sm" variant="outline-danger" onClick={() => void deletePublication(publication.id)}>Delete</Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </Tab.Pane>
              </Tab.Content>
            </Card.Body>
          </Card>
        </Tab.Container>

        <Modal show={showSessionsModal} onHide={() => setShowSessionsModal(false)} size="lg" centered>
          <Modal.Header closeButton>
            <Modal.Title>User Sessions</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Table size="sm" striped>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Last Seen</th>
                  <th>IP</th>
                  <th>User Agent</th>
                  <th>Revoked</th>
                </tr>
              </thead>
              <tbody>
                {selectedUserSessions.map((session) => (
                  <tr key={session.id}>
                    <td>{formatDate(session.created_at)}</td>
                    <td>{formatDate(session.last_seen_at)}</td>
                    <td>{session.ip_address || '—'}</td>
                    <td>{session.user_agent || '—'}</td>
                    <td>{session.revoked_at ? 'yes' : 'no'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Modal.Body>
        </Modal>
      </div>
    </div>
  );
}

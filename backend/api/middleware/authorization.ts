import { Request, Response, NextFunction } from 'express';
import {
  canAccess,
  getUserAccessProfile,
  type UserAccessProfile,
} from '../security/rbacService.js';
import {
  type CrudAction,
  type PermissionScope,
  type RbacResource,
  type RoleKey,
} from '../security/rbacCatalog.js';
import { asyncHandler, ForbiddenError, UnauthorizedError } from './errorHandler.js';
import { RequestWithAuth } from './auth.js';

export interface RequestWithAccess extends RequestWithAuth {
  accessProfile?: UserAccessProfile;
}

const ensureAuthenticated = (req: Request) => {
  const authReq = req as Partial<RequestWithAuth>;
  if (!authReq.userId) {
    throw new UnauthorizedError('Authentication required');
  }

  return authReq.userId;
};

const loadProfile = async (req: RequestWithAccess) => {
  const userId = ensureAuthenticated(req);
  const profile = await getUserAccessProfile(userId);

  if (!profile) {
    throw new UnauthorizedError('Access profile not found');
  }

  if (profile.isSystemBlocked) {
    throw new ForbiddenError('Account is blocked by system policy');
  }

  req.accessProfile = profile;
  return profile;
};

const assertAllowed = (
  profile: UserAccessProfile,
  resource: RbacResource,
  action: CrudAction,
  scope: PermissionScope,
  message?: string
) => {
  const granted = canAccess(profile.roleKeys, action, scope, resource);
  if (!granted) {
    throw new ForbiddenError(message || `Missing permission: ${resource}.${action}.${scope}`);
  }
};

export const requirePermission = (
  resource: RbacResource,
  action: CrudAction,
  scope: PermissionScope = 'any',
  message?: string
) => asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
  const profile = await loadProfile(req as RequestWithAccess);
  assertAllowed(profile, resource, action, scope, message);
  next();
});

export const requireAnyOrOwnPermission = (
  resource: RbacResource,
  action: CrudAction,
  isOwner: (req: RequestWithAccess) => boolean,
  message?: string
) => asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
  const typedReq = req as RequestWithAccess;
  const profile = await loadProfile(typedReq);

  const hasAny = canAccess(profile.roleKeys, action, 'any', resource);
  if (hasAny) {
    next();
    return;
  }

  const hasOwn = canAccess(profile.roleKeys, action, 'own', resource);
  if (hasOwn && isOwner(typedReq)) {
    next();
    return;
  }

  throw new ForbiddenError(message || `Missing permission: ${resource}.${action}.any|own`);
});

export const requireRole = (
  allowedRoles: RoleKey[],
  message?: string
) => asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
  const profile = await loadProfile(req as RequestWithAccess);
  const hasRole = profile.roleKeys.some((role) => allowedRoles.includes(role));

  if (!hasRole) {
    throw new ForbiddenError(message || 'Role requirement is not satisfied');
  }

  next();
});

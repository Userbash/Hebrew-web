import express, { Request, Response } from 'express';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

import { verifyToken } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

const ORCHESTRATOR_QUEUE_FILE = process.env.ORCHESTRATOR_QUEUE_FILE || path.resolve(process.cwd(), '..', '.agent', 'bridge_queue.json');
const ORCHESTRATOR_RESULTS_DIR = process.env.ORCHESTRATOR_RESULTS_DIR || path.resolve(process.cwd(), '..', '.agent', 'bridge_results');
const ORCHESTRATOR_BRIDGE_URL = process.env.ORCHESTRATOR_BRIDGE_URL || 'http://127.0.0.1:8000';
const ORCHESTRATOR_CHAT_TIMEOUT_MS = Number(process.env.ORCHESTRATOR_CHAT_TIMEOUT_MS || 90_000);

const MAX_DESCRIPTION_LEN = 10_000;
const MAX_LIST_ITEMS = 200;
const MAX_ITEM_LEN = 1_000;

interface OrchestratorTaskSubmitBody {
  type?: string;
  description?: string;
  priority?: string;
  project?: string;
  repo_path?: string;
  branch?: string;
  files?: unknown;
  constraints?: unknown;
  acceptance_criteria?: unknown;
  session_id?: string;
}

interface OrchestratorChatBody {
  message?: string;
  session_id?: string;
  user_id?: string;
  provider?: 'gpt' | 'gemini' | 'auto';
}

interface OrchestratorTaskPayload {
  task_id: string;
  type: 'plan' | 'code' | 'review' | 'test' | 'docs' | 'fix' | 'research';
  description: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  project: string;
  repo_path: string;
  branch: string;
  files: string[];
  constraints: string[];
  acceptance_criteria: string[];
  session_id?: string;
}

const taskTypes = new Set<OrchestratorTaskPayload['type']>(['plan', 'code', 'review', 'test', 'docs', 'fix', 'research']);
const priorities = new Set<OrchestratorTaskPayload['priority']>(['low', 'normal', 'high', 'critical']);
const chatProviders = new Set<NonNullable<OrchestratorChatBody['provider']>>(['gpt', 'gemini', 'auto']);

const toStringList = (value: unknown, field: string): string[] => {
  if (value == null) {
    return [];
  }
  if (!Array.isArray(value)) {
    throw new ValidationError(`${field} must be an array of strings`);
  }
  if (value.length > MAX_LIST_ITEMS) {
    throw new ValidationError(`${field} exceeds max items (${MAX_LIST_ITEMS})`);
  }
  return value.map((item, idx) => {
    if (typeof item !== 'string') {
      throw new ValidationError(`${field}[${idx}] must be a string`);
    }
    const trimmed = item.trim();
    if (!trimmed) {
      throw new ValidationError(`${field}[${idx}] must not be empty`);
    }
    if (trimmed.length > MAX_ITEM_LEN) {
      throw new ValidationError(`${field}[${idx}] exceeds max length (${MAX_ITEM_LEN})`);
    }
    return trimmed;
  });
};

const buildTaskPayload = (body: OrchestratorTaskSubmitBody): OrchestratorTaskPayload => {
  const typeRaw = typeof body.type === 'string' ? body.type.trim().toLowerCase() : 'plan';
  if (!taskTypes.has(typeRaw as OrchestratorTaskPayload['type'])) {
    throw new ValidationError(`Invalid task type: ${typeRaw}`);
  }

  const priorityRaw = typeof body.priority === 'string' ? body.priority.trim().toLowerCase() : 'normal';
  if (!priorities.has(priorityRaw as OrchestratorTaskPayload['priority'])) {
    throw new ValidationError(`Invalid priority: ${priorityRaw}`);
  }

  const description = typeof body.description === 'string' ? body.description.trim() : '';
  if (!description) {
    throw new ValidationError('description is required');
  }
  if (description.length > MAX_DESCRIPTION_LEN) {
    throw new ValidationError(`description exceeds max length (${MAX_DESCRIPTION_LEN})`);
  }

  const payload: OrchestratorTaskPayload = {
    task_id: crypto.randomUUID(),
    type: typeRaw as OrchestratorTaskPayload['type'],
    description,
    priority: priorityRaw as OrchestratorTaskPayload['priority'],
    project: typeof body.project === 'string' && body.project.trim() ? body.project.trim() : 'backend',
    repo_path: typeof body.repo_path === 'string' && body.repo_path.trim() ? body.repo_path.trim() : '.',
    branch: typeof body.branch === 'string' && body.branch.trim() ? body.branch.trim() : 'main',
    files: toStringList(body.files, 'files'),
    constraints: toStringList(body.constraints, 'constraints'),
    acceptance_criteria: toStringList(body.acceptance_criteria, 'acceptance_criteria'),
  };

  if (!payload.acceptance_criteria.length) {
    payload.acceptance_criteria = ['tests pass'];
  }

  if (typeof body.session_id === 'string' && body.session_id.trim()) {
    payload.session_id = body.session_id.trim();
  }

  return payload;
};

router.get(
  '/health',
  verifyToken,
  requirePermission('system', 'read', 'any'),
  asyncHandler(async (_req: Request, res: Response) => {
    let queueExists = false;
    try {
      await fs.stat(ORCHESTRATOR_QUEUE_FILE);
      queueExists = true;
    } catch {
      queueExists = false;
    }

    await fs.mkdir(ORCHESTRATOR_RESULTS_DIR, { recursive: true });

    res.status(200).json({
      success: true,
      status: 'ok',
      queue_file: ORCHESTRATOR_QUEUE_FILE,
      queue_busy: queueExists,
      results_dir: ORCHESTRATOR_RESULTS_DIR,
      timestamp: new Date().toISOString(),
    });
  })
);

router.post(
  '/chat',
  asyncHandler(async (req: Request<unknown, unknown, OrchestratorChatBody>, res: Response) => {
    const message = typeof req.body?.message === 'string' ? req.body.message.trim() : '';
    if (!message) {
      throw new ValidationError('message is required');
    }
    if (message.length > MAX_DESCRIPTION_LEN) {
      throw new ValidationError('message exceeds max length (' + MAX_DESCRIPTION_LEN + ')');
    }

    const providerRaw = typeof req.body?.provider === 'string' ? req.body.provider.trim().toLowerCase() : 'auto';
    if (!chatProviders.has(providerRaw as NonNullable<OrchestratorChatBody['provider']>)) {
      throw new ValidationError('Invalid provider: ' + providerRaw);
    }

    const bridgePayload = {
      user_id: typeof req.body?.user_id === 'string' && req.body.user_id.trim() ? req.body.user_id.trim() : 'backend:' + providerRaw,
      session_id: typeof req.body?.session_id === 'string' && req.body.session_id.trim() ? req.body.session_id.trim() : 'backend-' + Date.now(),
      message,
      source: 'backend_orchestrator_api',
      provider: providerRaw,
    };

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), ORCHESTRATOR_CHAT_TIMEOUT_MS);

    try {
      const response = await fetch(ORCHESTRATOR_BRIDGE_URL + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bridgePayload),
        signal: controller.signal,
      });

      const text = await response.text();
      let parsed: unknown = null;
      try {
        parsed = text ? JSON.parse(text) : null;
      } catch {
        parsed = { raw: text };
      }

      if (!response.ok) {
        res.status(502).json({
          success: false,
          error: 'OrchestratorBridgeError',
          message: 'Orchestrator bridge returned non-OK status',
          bridge_status: response.status,
          bridge_response: parsed,
        });
        return;
      }

      if (parsed && typeof parsed === 'object' && (parsed as { status?: string }).status === 'error') {
        res.status(502).json({
          success: false,
          error: 'OrchestratorExecutionError',
          message: 'Orchestrator returned execution error',
          bridge_response: parsed,
        });
        return;
      }

      res.status(200).json({
        success: true,
        status: 'completed',
        provider: providerRaw,
        orchestrator_url: ORCHESTRATOR_BRIDGE_URL + '/chat',
        data: parsed,
      });
    } catch (error) {
      const isAbort = (error as { name?: string })?.name === 'AbortError';
      res.status(isAbort ? 504 : 502).json({
        success: false,
        error: isAbort ? 'OrchestratorTimeout' : 'OrchestratorUnavailable',
        message: isAbort ? 'Orchestrator chat timeout' : 'Failed to reach orchestrator bridge',
        details: isAbort ? { timeout_ms: ORCHESTRATOR_CHAT_TIMEOUT_MS } : undefined,
      });
    } finally {
      clearTimeout(timeout);
    }
  })
);

router.get(
  '/chat/health',
  asyncHandler(async (_req: Request, res: Response) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8_000);

    try {
      const response = await fetch(ORCHESTRATOR_BRIDGE_URL + '/health', {
        method: 'GET',
        signal: controller.signal,
      });

      const text = await response.text();
      let parsed: unknown = null;
      try {
        parsed = text ? JSON.parse(text) : null;
      } catch {
        parsed = { raw: text };
      }

      res.status(response.ok ? 200 : 502).json({
        success: response.ok,
        orchestrator_url: ORCHESTRATOR_BRIDGE_URL + '/health',
        bridge_status: response.status,
        bridge_response: parsed,
      });
    } catch (error) {
      const isAbort = (error as { name?: string })?.name === 'AbortError';
      res.status(isAbort ? 504 : 502).json({
        success: false,
        error: isAbort ? 'OrchestratorTimeout' : 'OrchestratorUnavailable',
        message: isAbort ? 'Orchestrator health timeout' : 'Failed to reach orchestrator health endpoint',
      });
    } finally {
      clearTimeout(timeout);
    }
  })
);

router.post(
  '/tasks',
  verifyToken,
  requirePermission('system', 'create', 'any'),
  asyncHandler(async (req: Request<unknown, unknown, OrchestratorTaskSubmitBody>, res: Response) => {
    const payload = buildTaskPayload(req.body || {});

    // Avoid long backend response: async submit + immediate 202.
    try {
      await fs.stat(ORCHESTRATOR_QUEUE_FILE);
      res.status(409).json({
        success: false,
        error: 'QueueBusy',
        message: 'Orchestrator queue is busy. Retry shortly.',
      });
      return;
    } catch {
      // queue file absent -> ready
    }

    await fs.mkdir(path.dirname(ORCHESTRATOR_QUEUE_FILE), { recursive: true });
    await fs.mkdir(ORCHESTRATOR_RESULTS_DIR, { recursive: true });

    await fs.writeFile(ORCHESTRATOR_QUEUE_FILE, JSON.stringify(payload), { encoding: 'utf-8', flag: 'wx' });

    res.status(202).json({
      success: true,
      status: 'accepted',
      task_id: payload.task_id,
      polling_url: `/api/orchestrator/tasks/${payload.task_id}`,
      timestamp: new Date().toISOString(),
    });
  })
);

router.get(
  '/tasks/:taskId',
  verifyToken,
  requirePermission('system', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const taskIdRaw = req.params?.taskId;
    const taskId = typeof taskIdRaw === 'string' ? taskIdRaw.trim() : '';
    if (!taskId) {
      throw new ValidationError('taskId is required');
    }

    const resultFile = path.join(ORCHESTRATOR_RESULTS_DIR, `${taskId}.json`);

    try {
      const content = await fs.readFile(resultFile, 'utf-8');
      const parsed: unknown = JSON.parse(content);
      res.status(200).json({
        success: true,
        status: 'done',
        task_id: taskId,
        result: parsed,
      });
      return;
    } catch {
      res.status(200).json({
        success: true,
        status: 'pending',
        task_id: taskId,
      });
    }
  })
);

export default router;

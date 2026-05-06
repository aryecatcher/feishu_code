/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from './ExecutionStatus';
/**
 * Checkpoint response.
 */
export type CheckpointResponse = {
    id: string;
    execution_id: string;
    stage_id: string;
    stage_result: Record<string, any>;
    status: ExecutionStatus;
    created_at: string;
    decided_at: (string | null);
    decided_by: (string | null);
    comment: (string | null);
    approval_action: (string | null);
};


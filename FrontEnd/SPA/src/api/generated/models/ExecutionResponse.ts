/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from './ExecutionStatus';
/**
 * Execution response.
 */
export type ExecutionResponse = {
    id: string;
    pipeline_id: string;
    status: ExecutionStatus;
    current_stage_id: (string | null);
    results?: Record<string, any>;
    checkpoints?: Record<string, any>;
    created_at: string;
    updated_at: (string | null);
    completed_at: (string | null);
};


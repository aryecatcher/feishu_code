/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from './ExecutionStatus';
/**
 * Detailed execution status.
 */
export type ExecutionStatusResponse = {
    id: string;
    pipeline_id: string;
    status: ExecutionStatus;
    current_stage_id: (string | null);
    current_stage_name: (string | null);
    /**
     * Progress percentage 0-100
     */
    progress: number;
    results: Record<string, any>;
    checkpoints: Record<string, any>;
    error: (string | null);
    created_at: string;
    updated_at: (string | null);
};


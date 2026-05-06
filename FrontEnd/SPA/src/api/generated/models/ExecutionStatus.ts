/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Execution status for a stage or overall pipeline.
 */
export enum ExecutionStatus {
    PENDING = 'pending',
    RUNNING = 'running',
    WAITING_APPROVAL = 'waiting_approval',
    APPROVED = 'approved',
    REJECTED = 'rejected',
    COMPLETED = 'completed',
    FAILED = 'failed',
    CANCELLED = 'cancelled',
}

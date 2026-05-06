/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to reject a checkpoint.
 */
export type CheckpointReject = {
    /**
     * Rejection reason (required)
     */
    comment: string;
    /**
     * Rejector identifier
     */
    rejector?: string;
};


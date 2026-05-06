/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to create and start an execution.
 */
export type ExecutionCreate = {
    /**
     * Pipeline ID to execute
     */
    pipeline_id: string;
    /**
     * Demand/requirement description
     */
    demand: string;
    /**
     * Execution configuration
     */
    config?: Record<string, any>;
};


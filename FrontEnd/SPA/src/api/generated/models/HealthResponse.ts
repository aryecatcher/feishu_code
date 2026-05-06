/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Health check response.
 */
export type HealthResponse = {
    status: string;
    version: string;
    timestamp: string;
    services?: Record<string, boolean>;
};


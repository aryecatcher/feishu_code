/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PipelineStage } from './PipelineStage';
import type { PipelineStatus } from './PipelineStatus';
/**
 * Pipeline response.
 */
export type PipelineResponse = {
    id: string;
    name: string;
    description: string;
    stages: Array<PipelineStage>;
    status: PipelineStatus;
    created_at: string;
    updated_at: string;
    metadata?: Record<string, any>;
};


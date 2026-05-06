/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PipelineStage } from './PipelineStage';
/**
 * Request to create a new pipeline.
 */
export type PipelineCreate = {
    name: string;
    description?: string;
    stages: Array<PipelineStage>;
};


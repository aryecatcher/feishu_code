/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Descriptions } from './Descriptions';
/**
 * Request to update a pipeline.
 */
export type PipelineUpdate = {
    descriptions?: (Descriptions | null);
    stages?: (Array<string> | null);
    config?: (Record<string, any> | null);
};

